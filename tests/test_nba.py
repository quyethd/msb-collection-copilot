from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import date
from datetime import datetime, timedelta
from fractions import Fraction
from pathlib import Path

from msb_nba.config import NBAConfig
from msb_nba.engine import decide
from msb_nba.io import write_artifacts
from msb_nba.models import When
from msb_nba.repository import load_inputs
from msb_nba.timing import select_best_window
from msb_nba.validate import validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "build/synthetic-data"
EXPECTED = {"NBA-000": 0, "NBA-100": 414, "NBA-110": 1, "NBA-200": 1, "NBA-210": 1, "NBA-220": 2,
            "NBA-230": 415, "NBA-240": 1, "NBA-300": 30, "NBA-310": 8, "NBA-400": 328,
            "NBA-900": 738, "NBA-910": 34, "NBA-920": 1027}


def context(**changes):
    row = {"cif": "TEST", "as_of_date": "2026-08-28", "debt": {"max_dpd_cif": 20},
           "policy": {"final_route": "CALL", "hard_suppressed": False, "latest_business_outcome": None,
                      "source_next_action_date": None, "source_next_operation_channel": None},
           "ptp": {"status": None, "promise_date": None},
           "cashflow": {"inflow_3d": 0, "inflow_7d": 0, "net_cashflow_30d": 0},
           "availability": {"cashflow_available": True},
           "provenance": {"synthetic_data": True, "synthetic_label": "SYNTHETIC PROTOTYPE DATA", "reference_date": "2026-08-28"}}
    for key, value in changes.items():
        section, field = key.split("__", 1); row[section][field] = value
    return row


class TestNBAUnit(unittest.TestCase):
    def rule(self, **changes): return decide(context(**changes), []).selected_rule.rule_id

    def assert_decision(self, expected, **changes):
        row = decide(context(**changes), [])
        expected_outputs = {
            "NBA-000": ("WAIT", "NONE", "NONE", "INFORMATION_COLLECTION", "HARD_SUPPRESSED"),
            "NBA-100": ("CALLBACK", "CALL", "SOURCE_DATETIME", "CALLBACK", "CALLBACK_DUE"),
            "NBA-110": ("VERIFY_CONTACT", "NONE", "TODAY", "CONTACT_VERIFICATION", "INVALID_CONTACT"),
            "NBA-200": ("PARTIAL_PAYMENT", "CALL", "BEST_WINDOW", "PAYMENT", "PARTIAL_PTP"),
            "NBA-210": ("PTP_RECOVERY", "CALL", "BEST_WINDOW", "PAYMENT", "BROKEN_PTP_RECENT_INFLOW"),
            "NBA-220": ("CONTACT", "CALL", "BEST_WINDOW", "PAYMENT", "BROKEN_PTP"),
            "NBA-230": ("PTP_FOLLOW_UP", "CALL", "BEST_WINDOW", "PTP_KEEP", "OPEN_PTP"),
            "NBA-240": ("WAIT", "NONE", "NONE", "PTP_KEEP", "KEPT_PTP"),
            "NBA-300": ("WAIT_SELF_CURE", "NONE", "NONE", "PAYMENT", "CALL_SELF_CURE"),
            "NBA-400": ("ESCALATE", "CALL", "BEST_WINDOW", "PAYMENT", "RTP_ESCALATION"),
            "NBA-900": ("CONTACT", "CALL", "BEST_WINDOW", "PAYMENT", "CALL_DEFAULT"),
        }
        observed = (row.recommendation.treatment, row.recommendation.channel, row.recommendation.when.type,
                    row.recommendation.objective, row.selected_rule.reason_code)
        self.assertEqual(row.selected_rule.rule_id, expected)
        self.assertEqual(observed, expected_outputs[expected])

    def test_every_rule_and_precedence(self):
        cases = {
            "NBA-000": {"policy__hard_suppressed": True},
            "NBA-100": {"policy__latest_business_outcome": "NA", "policy__source_next_action_date": "2026-08-29T10:00:00+00:00"},
            "NBA-110": {"policy__latest_business_outcome": "NIN"}, "NBA-200": {"ptp__status": "PARTIAL"},
            "NBA-210": {"ptp__status": "BROKEN", "cashflow__inflow_3d": 5_000_000}, "NBA-220": {"ptp__status": "BROKEN"},
            "NBA-230": {"ptp__status": "OPEN"}, "NBA-240": {"ptp__status": "KEPT"},
            "NBA-300": {"debt__max_dpd_cif": 14, "cashflow__inflow_7d": 15_000_000, "cashflow__net_cashflow_30d": 1},
            "NBA-310": {"policy__final_route": "CBS", "debt__max_dpd_cif": 14, "cashflow__inflow_7d": 15_000_000, "cashflow__net_cashflow_30d": 1},
            "NBA-400": {"policy__latest_business_outcome": "RTP"}, "NBA-900": {},
            "NBA-910": {"policy__final_route": "CBS"}, "NBA-920": {"policy__final_route": "OTHER"}}
        for expected, changes in cases.items():
            with self.subTest(expected): self.assertEqual(self.rule(**changes), expected)
        combined = cases["NBA-100"] | {"ptp__status": "BROKEN", "cashflow__inflow_3d": 9_000_000}
        result = decide(context(**combined), [])
        self.assertEqual(result.selected_rule.rule_id, "NBA-100")
        self.assertEqual(result.decision_trace[-1].effect, "SELECTED")
        self.assertNotIn("NBA-110", [x.rule_id for x in result.decision_trace])

    def test_self_cure_boundaries_and_independent_negatives(self):
        base = {"debt__max_dpd_cif": 14, "cashflow__inflow_7d": 15_000_000, "cashflow__net_cashflow_30d": 1}
        self.assertEqual(self.rule(**base), "NBA-300")
        for mutation in ({"policy__final_route": "OTHER"}, {"debt__max_dpd_cif": 15}, {"ptp__status": "OPEN"},
                         {"policy__latest_business_outcome": "RTP"}, {"policy__latest_business_outcome": "NIN"},
                         {"availability__cashflow_available": False}, {"cashflow__net_cashflow_30d": 0},
                         {"cashflow__inflow_7d": 14_999_999}, {"policy__hard_suppressed": True},
                         {"policy__source_next_action_date": "2026-08-29T10:00:00+00:00"}):
            with self.subTest(mutation): self.assertNotEqual(self.rule(**(base | mutation)), "NBA-300")
        cbs = base | {"policy__final_route": "CBS"}
        self.assertEqual(self.rule(**cbs), "NBA-310")
        for mutation in ({"policy__final_route": "CALL"}, {"debt__max_dpd_cif": 15},
                         {"cashflow__inflow_7d": 14_999_999}, {"cashflow__net_cashflow_30d": 0},
                         {"availability__cashflow_available": False}, {"ptp__status": "OPEN"}):
            with self.subTest(cbs=mutation): self.assertNotEqual(self.rule(**(cbs | mutation)), "NBA-310")

    def test_full_precedence_conflicts_preserve_complete_recommendation(self):
        callback = {"policy__latest_business_outcome": "NA", "policy__source_next_action_date": "2026-08-29T10:00:00+00:00"}
        self_cure = {"debt__max_dpd_cif": 14, "cashflow__inflow_7d": 15_000_000, "cashflow__net_cashflow_30d": 1}
        cases = (
            ("NBA-000", callback | {"policy__hard_suppressed": True, "ptp__status": "PARTIAL"}),
            ("NBA-100", callback | {"ptp__status": "PARTIAL", "cashflow__inflow_3d": 9_000_000}),
            ("NBA-110", {"policy__latest_business_outcome": "NIN", "ptp__status": "PARTIAL"} | self_cure),
            ("NBA-200", {"policy__latest_business_outcome": "RTP", "ptp__status": "PARTIAL"} | self_cure),
            ("NBA-210", {"policy__latest_business_outcome": "RTP", "ptp__status": "BROKEN", "cashflow__inflow_3d": 5_000_000} | self_cure),
            ("NBA-230", {"policy__latest_business_outcome": "RTP", "ptp__status": "OPEN"} | self_cure),
            ("NBA-240", {"policy__latest_business_outcome": "RTP", "ptp__status": "KEPT"} | self_cure),
            ("NBA-300", self_cure),
            ("NBA-400", {"policy__latest_business_outcome": "RTP"}),
        )
        for expected, changes in cases:
            with self.subTest(expected): self.assert_decision(expected, **changes)

    def test_broken_threshold_and_missing_cashflow(self):
        self.assertEqual(self.rule(ptp__status="BROKEN", cashflow__inflow_3d=4_999_999), "NBA-220")
        self.assertEqual(self.rule(ptp__status="BROKEN", cashflow__inflow_3d=5_000_000), "NBA-210")
        self.assertEqual(self.rule(ptp__status="BROKEN", cashflow__inflow_3d=None, availability__cashflow_available=False), "NBA-220")

    def test_source_values_preserved_exactly(self):
        stamp = "2026-08-29T10:00:00+07:00"
        row = decide(context(policy__latest_business_outcome="NA", policy__source_next_action_date=stamp), [])
        self.assertEqual(row.recommendation.when.datetime, stamp)
        row = decide(context(ptp__status="OPEN", ptp__promise_date="2026-08-30"), [])
        self.assertEqual(row.recommendation.when, When("SOURCE_DATE", date="2026-08-30"))

    def test_when_shapes(self):
        for args in (("NONE", None, "x", None), ("TODAY", "x", None, None), ("BEST_WINDOW", None, "2026-08-28", None)):
            with self.assertRaises(ValueError): When(args[0], datetime=args[1], date=args[2], window=args[3])

    def test_best_window_boundaries_fallback_and_ties(self):
        def call(day, hour, status="Success", kind="OUTBOUND"): return {"call_time": f"{day}T{hour:02d}:00:00+00:00", "status": status, "call_type": kind}
        ref = date(2026, 8, 28); config = NBAConfig()
        self.assertEqual(select_best_window([], ref, config)[0], "10-12")
        calls = [call("2026-07-30", 13), call("2026-07-29", 8), call("2026-08-28", 15), call("2026-08-29", 17)]
        self.assertEqual(select_best_window(calls, ref, config)[0], "13-15")
        calls = [call("2026-08-28", 8), call("2026-08-28", 8, "No Answer"), call("2026-08-28", 13)]
        self.assertEqual(select_best_window(calls, ref, config)[0], "13-15") # rate wins
        calls = [call("2026-08-28", 8), call("2026-08-28", 8, "No Answer"), call("2026-08-28", 15), call("2026-08-28", 15, "No Answer"), call("2026-08-27", 15), call("2026-08-27", 15, "No Answer")]
        self.assertEqual(select_best_window(calls, ref, config)[0], "15-17") # success count wins
        self.assertEqual(select_best_window([call("2026-08-28", 8), call("2026-08-28", 13)], ref, config)[0], "08-10")


class TestNBAIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contexts, cls.calls = load_inputs(DATA)
        cls.decisions = [decide(row, cls.calls.get(row["cif"], ())) for row in cls.contexts]
        cls.by_cif = {row.cif: row for row in cls.decisions}

    def test_population_distributions_and_representatives(self):
        counts = Counter(row.selected_rule.rule_id for row in self.decisions)
        self.assertEqual({key: counts[key] for key in EXPECTED}, EXPECTED)
        self.assertEqual(Counter(row.recommendation.when.type for row in self.decisions), {"SOURCE_DATETIME":414,"SOURCE_DATE":415,"BEST_WINDOW":1104,"TODAY":1,"NONE":1066})
        self.assertEqual(self.by_cif["GOLDEN_G03"].selected_rule.rule_id, "NBA-900")
        self.assertEqual(self.by_cif["GOLDEN_G18"].selected_rule.rule_id, "NBA-900")
        hero = self.by_cif["SYN002846"]
        self.assertEqual((hero.selected_rule.rule_id, hero.recommendation.treatment, hero.recommendation.channel, hero.recommendation.when.type, hero.recommendation.objective), ("NBA-300","WAIT_SELF_CURE","NONE","NONE","PAYMENT"))

    def test_independent_first_match_oracle(self):
        # Deliberately reconstruct conditions here without calling production decide.
        mismatches = []
        outputs={"NBA-000":("WAIT","NONE","INFORMATION_COLLECTION","HARD_SUPPRESSED"),"NBA-100":("CALLBACK","CALL","CALLBACK","CALLBACK_DUE"),"NBA-110":("VERIFY_CONTACT","NONE","CONTACT_VERIFICATION","INVALID_CONTACT"),"NBA-200":("PARTIAL_PAYMENT","CALL","PAYMENT","PARTIAL_PTP"),"NBA-210":("PTP_RECOVERY","CALL","PAYMENT","BROKEN_PTP_RECENT_INFLOW"),"NBA-220":("CONTACT","CALL","PAYMENT","BROKEN_PTP"),"NBA-230":("PTP_FOLLOW_UP","CALL","PTP_KEEP","OPEN_PTP"),"NBA-240":("WAIT","NONE","PTP_KEEP","KEPT_PTP"),"NBA-300":("WAIT_SELF_CURE","NONE","PAYMENT","CALL_SELF_CURE"),"NBA-310":("WAIT","NONE","PAYMENT","CBS_SELF_CURE"),"NBA-400":("ESCALATE","CALL","PAYMENT","RTP_ESCALATION"),"NBA-900":("CONTACT","CALL","PAYMENT","CALL_DEFAULT"),"NBA-910":("REMIND","SMS","PAYMENT","CBS_DEFAULT"),"NBA-920":("WAIT","NONE","INFORMATION_COLLECTION","OTHER_DEFAULT")}
        best_rules={"NBA-200","NBA-210","NBA-220","NBA-400","NBA-900","NBA-910"}
        bounds=((8,10,"08-10"),(10,12,"10-12"),(13,15,"13-15"),(15,17,"15-17"),(17,19,"17-19"))
        for c in self.contexts:
            p,t,a,x,d = c["policy"],c["ptp"],c["availability"],c["cashflow"],c["debt"]
            state=t["status"] or "NONE"; outcome=p["latest_business_outcome"]; route=p["final_route"]
            sc=route in {"CALL","CBS"} and d["max_dpd_cif"]<=14 and state=="NONE" and outcome not in {"RTP","NIN"} and a["cashflow_available"] and x["net_cashflow_30d"]>0 and x["inflow_7d"]>=15_000_000 and not p["hard_suppressed"] and p["source_next_action_date"] is None
            tests=(("NBA-000",p["hard_suppressed"]),("NBA-100",outcome=="NA" and p["source_next_action_date"] is not None),("NBA-110",outcome=="NIN"),("NBA-200",state=="PARTIAL"),("NBA-210",state=="BROKEN" and a["cashflow_available"] and x["inflow_3d"]>=5_000_000),("NBA-220",state=="BROKEN"),("NBA-230",state=="OPEN"),("NBA-240",state=="KEPT"),("NBA-300",sc and route=="CALL"),("NBA-310",sc and route=="CBS"),("NBA-400",route=="CALL" and outcome=="RTP"),("NBA-900",route=="CALL"),("NBA-910",route=="CBS"),("NBA-920",route=="OTHER"))
            expected=next(rule for rule,match in tests if match)
            actual=self.by_cif[c["cif"]]; expected_output=outputs[expected]
            if expected=="NBA-100" or (expected=="NBA-230" and p["source_next_action_date"] is not None): expected_when=("SOURCE_DATETIME",p["source_next_action_date"],None,None)
            elif expected=="NBA-110": expected_when=("TODAY",None,c["as_of_date"],None)
            elif expected=="NBA-230" and t["promise_date"] is not None and t["promise_date"]>=c["as_of_date"]: expected_when=("SOURCE_DATE",None,t["promise_date"],None)
            elif expected in best_rules or expected=="NBA-230":
                start=date.fromisoformat(c["as_of_date"])-timedelta(days=29); stats=defaultdict(lambda:[0,0])
                for call in self.calls.get(c["cif"],()):
                    ts=datetime.fromisoformat(call["call_time"])
                    if call["call_type"]=="OUTBOUND" and start<=ts.date()<=date.fromisoformat(c["as_of_date"]):
                        window=next((name for lo,hi,name in bounds if lo<=ts.hour<hi),None)
                        if window: stats[window][0]+=1; stats[window][1]+=call["status"]=="Success"
                order=[x[2] for x in bounds]
                window="10-12" if not any(v[1] for v in stats.values()) else max(order,key=lambda w:(Fraction(stats[w][1],stats[w][0]) if stats[w][0] else Fraction(0),stats[w][1],-order.index(w)))
                expected_when=("BEST_WINDOW",None,c["as_of_date"],window)
            else: expected_when=("NONE",None,None,None)
            observed=(actual.recommendation.when.type,actual.recommendation.when.datetime,actual.recommendation.when.date,actual.recommendation.when.window)
            if (expected != actual.selected_rule.rule_id or expected_output != (actual.recommendation.treatment,actual.recommendation.channel,actual.recommendation.objective,actual.selected_rule.reason_code) or expected_when != observed): mismatches.append(c["cif"])
        self.assertEqual(mismatches, [])

    def test_validation_determinism_and_no_source_mutation(self):
        before = hashlib.sha256(json.dumps(self.contexts, sort_keys=True).encode()).hexdigest()
        report, golden = validate(self.contexts, self.decisions, self.calls); self.assertEqual(report["status"], "PASS")
        after = hashlib.sha256(json.dumps(self.contexts, sort_keys=True).encode()).hexdigest(); self.assertEqual(before, after)
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            write_artifacts(self.decisions, report, golden, Path(a), NBAConfig()); write_artifacts(self.decisions, report, golden, Path(b), NBAConfig())
            for name in ("next_best_action.jsonl","nba_manifest.json","nba_validation.json","golden_nba_validation.json"):
                self.assertEqual((Path(a)/name).read_bytes(), (Path(b)/name).read_bytes())

    def test_validator_rejects_isolated_decision_corruptions(self):
        def rejected(original, corrupted):
            rows = [corrupted if row.cif == original.cif else row for row in self.decisions]
            self.assertEqual(validate(self.contexts, rows, self.calls)[0]["status"], "FAIL")

        base = self.by_cif["GOLDEN_G01"]
        callback = next(row for row in self.decisions if row.selected_rule.rule_id == "NBA-100")
        source_date = next(row for row in self.decisions if row.recommendation.when.type == "SOURCE_DATE")
        historical = next(row for row in self.decisions if row.evidence_refs.get("best_window", {}).get("source") == "HISTORICAL")
        fallback = next(row for row in self.decisions if row.evidence_refs.get("best_window", {}).get("source") == "FALLBACK")

        corruptions = [
            (base, replace(base, selected_rule=replace(base.selected_rule, rule_id="NBA-100"))),
            (base, replace(base, recommendation=replace(base.recommendation, treatment="WAIT_SELF_CURE"))),
            (base, replace(base, recommendation=replace(base.recommendation, channel="SMS"))),
            (base, replace(base, recommendation=replace(base.recommendation, when=When("TODAY", date=base.reference_date)))),
            (callback, replace(callback, recommendation=replace(callback.recommendation, when=When("SOURCE_DATETIME", datetime="2026-08-30T00:00:00+00:00")))),
            (source_date, replace(source_date, recommendation=replace(source_date.recommendation, when=When("SOURCE_DATE", date="2026-09-01")))),
            (historical, replace(historical, recommendation=replace(historical.recommendation, when=When("BEST_WINDOW", date=historical.reference_date, window="08-10" if historical.recommendation.when.window != "08-10" else "17-19")))),
            (base, replace(base, recommendation=replace(base.recommendation, objective="PTP"))),
            (base, replace(base, selected_rule=replace(base.selected_rule, reason_code="WRONG"))),
            (base, replace(base, provenance=base.provenance | {"synthetic_data": False})),
            (base, replace(base, provenance=base.provenance | {"synthetic_label": "WRONG"})),
            (base, replace(base, reference_date="2026-08-27")),
            (historical, replace(historical, recommendation=replace(historical.recommendation, when=When("BEST_WINDOW", date=historical.reference_date, window="08-10" if historical.recommendation.when.window != "08-10" else "17-19")))),
            (fallback, replace(fallback, recommendation=replace(fallback.recommendation, when=When("BEST_WINDOW", date=fallback.reference_date, window="15-17")))),
            (historical, replace(historical, recommendation=replace(historical.recommendation, when=When("BEST_WINDOW", date="2026-08-27", window=historical.recommendation.when.window)))),
        ]
        malformed = deepcopy(base)
        object.__setattr__(malformed.recommendation.when, "datetime", "2026-08-28T10:00:00+00:00")
        corruptions.insert(7, (base, malformed))
        for index, (original, corrupted) in enumerate(corruptions, 1):
            with self.subTest(corruption=index): rejected(original, corrupted)


if __name__ == "__main__": unittest.main()
