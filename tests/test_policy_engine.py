from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from msb_policy.engine import PolicyConfig, derive_ptp, evaluate_customer
from msb_policy.io import evaluate_directory
from msb_policy.validate import validate
from msb_synthetic.generator import generate_to

REF = date(2026, 8, 28)


def customer(cif="TEST", heatmap="RED", segment="ORANGE"):
    return {"cif": cif, "heatmap": heatmap, "segment": segment}


def loan(cif="TEST", amount=100, dpd=5, account="L1"):
    return {"cif": cif, "account_id": account, "outstanding_amount": str(amount), "dpd": str(dpd)}


def assignment(cif="TEST", override=""):
    return {"cif": cif, "challenge_override_route": override}


def operation(outcome="PTP", promise="2026-08-28", amount=100, created="2026-08-20T10:00:00+00:00", ability="MEDIUM", **extra):
    row = {"id": "OP1", "cif": "TEST", "operation_result": outcome, "payment_ptp_date": promise if outcome == "PTP" else "", "payment_ptp_number": str(amount) if outcome == "PTP" else "", "payment_ptp_ability": ability if outcome == "PTP" else "", "created_at": created, "next_action_date": "", "next_operation_channel": ""}
    row.update(extra)
    return row


def payment(amount, day="2026-08-28"):
    return {"cif": "TEST", "linked_ptp_id": "OP1", "amount": str(amount), "payment_date": f"{day}T14:00:00+00:00"}


def evaluate(*, loans=None, override="", heatmap="RED", segment="ORANGE", operations=None, payments=None, calls=None):
    return evaluate_customer(customer(heatmap=heatmap, segment=segment), loans or [loan()], assignment(override=override), operations or [], payments or [], calls or [], REF)


class PolicyUnitTest(unittest.TestCase):
    def test_agg_001_sum_and_agg_002_max(self):
        result = evaluate(loans=[loan(amount=100, dpd=4), loan(amount=250, dpd=12, account="L2"), loan(amount=50, dpd=7, account="L3")])
        self.assertEqual(result.total_outstanding_cif, Decimal(400))
        self.assertEqual(result.max_dpd_cif, 12)
        self.assertIn("AGG-001", result.triggered_rule_ids)
        self.assertIn("AGG-002", result.triggered_rule_ids)

    def test_call_route(self): self.assertEqual(evaluate().base_route, "CALL")
    def test_cbs_route(self): self.assertEqual(evaluate(loans=[loan(dpd=4)]).base_route, "CBS")
    def test_fallback_route(self): self.assertEqual(evaluate(heatmap="AMBER").base_route, "OTHER")

    def test_cbs_to_call_override(self):
        result = evaluate(loans=[loan(dpd=2)], override="CALL")
        self.assertEqual((result.base_route, result.challenge_override_route, result.final_route), ("CBS", "CALL", "CALL"))

    def test_call_to_cbs_override(self):
        result = evaluate(override="CBS")
        self.assertEqual((result.base_route, result.challenge_override_route, result.final_route), ("CALL", "CBS", "CBS"))

    def test_ptp_exact_payment_is_kept(self): self.assertEqual(evaluate(operations=[operation()], payments=[payment(100)]).ptp_status, "KEPT")
    def test_ptp_overpayment_is_kept(self): self.assertEqual(evaluate(operations=[operation()], payments=[payment(101)]).ptp_status, "KEPT")
    def test_ptp_partial(self): self.assertEqual(evaluate(operations=[operation()], payments=[payment(50)]).ptp_status, "PARTIAL")
    def test_ptp_open_before_due(self): self.assertEqual(evaluate(operations=[operation(promise="2026-08-30")]).ptp_status, "OPEN")
    def test_ptp_open_during_grace(self): self.assertEqual(evaluate(operations=[operation(promise="2026-08-27")]).ptp_status, "OPEN")
    def test_ptp_broken_after_grace(self): self.assertEqual(evaluate(operations=[operation(promise="2026-08-26")]).ptp_status, "BROKEN")

    def test_grace_is_configurable(self):
        facts, _ = derive_ptp([operation(promise="2026-08-20")], [], REF, PolicyConfig(ptp_grace_days=10))
        self.assertEqual(facts["ptp_status"], "OPEN")

    def test_fulfillment_and_ability_are_preserved_without_score(self):
        result = evaluate(operations=[operation(ability="HIGH")], payments=[payment(50)])
        self.assertEqual(result.fulfillment_ratio, Decimal("0.5"))
        self.assertEqual(result.payment_ptp_ability, "HIGH")
        self.assertFalse(any("score" in key.lower() for key in result.to_dict()))

    def test_source_next_action_preserved(self):
        row = operation(outcome="NA", next_action_date="2026-08-29T10:00:00+00:00", next_operation_channel="CALL")
        result = evaluate(operations=[row])
        self.assertEqual(result.latest_business_outcome, "NA")
        self.assertEqual(result.source_next_action_date, datetime(2026, 8, 29, 10, tzinfo=timezone.utc))
        self.assertEqual(result.source_next_operation_channel, "CALL")
        self.assertIn("CONTACT-003", result.triggered_rule_ids)

    def test_explicit_next_action_survives_later_operation_without_one(self):
        action = operation(outcome="NA", created="2026-08-20T10:00:00+00:00", next_action_date="2026-08-29T10:00:00+00:00", next_operation_channel="CALL")
        later = operation(outcome="UTC", created="2026-08-21T10:00:00+00:00", id="OP2")
        result = evaluate(operations=[action, later])
        self.assertEqual(result.latest_business_outcome, "UTC")
        self.assertEqual(result.source_next_operation_channel, "CALL")
        self.assertIn("CONTACT-003", result.triggered_rule_ids)

    def test_nin_preserved(self): self.assertEqual(evaluate(operations=[operation(outcome="NIN")]).latest_business_outcome, "NIN")

    def test_repeated_utc_evidence(self):
        rows = [operation(outcome="UTC", created=f"2026-08-{20+i:02d}T10:00:00+00:00", id=f"OP{i}") for i in range(5)]
        self.assertEqual(evaluate(operations=rows).business_outcome_counts["UTC"], 5)

    def test_technical_success_does_not_create_ptp(self):
        result = evaluate(calls=[{"cif": "TEST", "status": "Success"}])
        self.assertIsNone(result.ptp_status)
        self.assertIsNone(result.latest_business_outcome)
        self.assertEqual(result.technical_call_status_counts["Success"], 1)

    def test_routing_unaffected_by_cashflow(self):
        cashflow_before: list[dict[str, int]] = []
        first = evaluate()
        cashflow_after = cashflow_before + [{"amount": 999_000_000}]
        second = evaluate()
        self.assertNotEqual(cashflow_before, cashflow_after)
        self.assertEqual(first.final_route, second.final_route)

    def test_trace_is_deterministic(self):
        first, second = evaluate(operations=[operation()], payments=[payment(50)]), evaluate(operations=[operation()], payments=[payment(50)])
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertTrue(all(set(trace) == {"rule_id", "result", "evidence"} for trace in first.to_dict()["policy_trace"]))


class GoldenPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_to(cls.data)
        cls.results = {row.cif: row for row in evaluate_directory(cls.data)}
        cls.report = validate(cls.data)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_all_twenty_golden_inputs_evaluate(self):
        self.assertEqual(sum(cif.startswith("GOLDEN_G") for cif in self.results), 20)
        self.assertEqual(self.report["status"], "PASS", self.report["errors"])
        self.assertTrue(all(row["status"] == "PASS" for row in self.report["golden"].values()))

    def test_golden_ptp_states(self):
        expected = {"G09": "KEPT", "G10": "PARTIAL", "G11": "BROKEN", "G12": "OPEN"}
        for sid, status in expected.items(): self.assertEqual(self.results[f"GOLDEN_{sid}"].ptp_status, status)

    def test_g20_uses_actual_loan_aggregation(self):
        result = self.results["GOLDEN_G20"]
        self.assertEqual(result.total_outstanding_cif, Decimal(400_000_000))
        self.assertEqual(result.max_dpd_cif, 12)

    def test_baseline_sort(self):
        ordered = sorted(self.results.values(), key=lambda item: item.baseline_rank)
        self.assertEqual(ordered, sorted(ordered, key=lambda item: (-item.total_outstanding_cif, -item.max_dpd_cif, item.cif)))


if __name__ == "__main__": unittest.main()
