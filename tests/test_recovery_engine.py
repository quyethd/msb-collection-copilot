from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from msb_policy.engine import PolicyResult
from msb_recovery.engine import COMPONENT_MAX, RecoveryConfig, evaluate_one, evaluate_recovery
from msb_recovery.features import derive_features
from msb_recovery.io import evaluate_directory
from msb_recovery.validate import validate
from msb_synthetic.generator import generate_to

REF = date(2026, 8, 28)


def policy(**changes):
    base = PolicyResult("TEST", Decimal(100_000_000), 5, 1, "RED", "ORANGE", "CALL", None, "CALL", None, None, None, None, None, None, None, {name: 0 for name in ("UTC", "PTP", "NPTP", "RTP", "NIN", "THIRT", "NA")}, {}, None, None, False, None, (), ())
    return replace(base, **changes)


def features(**changes):
    base = {
        "inflow_3d": Decimal(0), "inflow_7d": Decimal(0), "inflow_30d": Decimal(0), "outflow_30d": Decimal(0), "net_cashflow_30d": Decimal(0),
        "net_cashflow_windows_30d": (Decimal(0), Decimal(0), Decimal(0)), "positive_cashflow_windows": 0, "income_sources_30d": [], "liquidity_to_due_ratio": None,
        "outbound_attempts_30d": 0, "successful_calls_30d": 0, "technical_success_rate_30d": None, "days_since_last_successful_call": None,
        "utc_count_30d": 0, "nin_present_30d": False, "call_or_operation_evidence_30d": False, "payment_after_contact_days": None,
        "cashflow_available": False, "payment_available": False, "ptp_available": False, "call_history_available": False, "operation_history_available": False,
    }
    base.update(changes); return base


def score(p=None, f=None, percentile=Decimal("0.25")):
    return evaluate_one(p or policy(), f or features(), percentile, RecoveryConfig(REF))


class RecoveryUnitTest(unittest.TestCase):
    def test_business_urgency_lower_and_upper_bounds(self):
        self.assertEqual(score(policy(max_dpd_cif=0)).business_urgency_score, 0)
        p = policy(max_dpd_cif=60, ptp_status="BROKEN", promise_date=REF, promise_amount=Decimal(1), actual_paid_amount=Decimal(0), fulfillment_ratio=Decimal(0), payment_ptp_ability="LOW")
        self.assertEqual(score(p, features(ptp_available=True), Decimal(1)).business_urgency_score, 20)

    def test_ability_lower_and_upper_bounds(self):
        self.assertEqual(score().ability_to_pay_score, 0)
        f = features(cashflow_available=True, inflow_7d=Decimal(30_000_000), net_cashflow_30d=Decimal(30_000_000), income_sources_30d=["SALARY", "BUSINESS_INCOME"], net_cashflow_windows_30d=(Decimal(1), Decimal(1), Decimal(1)), positive_cashflow_windows=3, liquidity_to_due_ratio=Decimal(2))
        self.assertEqual(score(f=f).ability_to_pay_score, 25)

    def test_willingness_lower_and_upper_bounds(self):
        self.assertEqual(score().willingness_to_pay_score, 0)
        p = policy(ptp_status="KEPT", promise_date=REF, promise_amount=Decimal(100), actual_paid_amount=Decimal(100), fulfillment_ratio=Decimal(1), payment_ptp_ability="CERTAIN")
        f = features(ptp_available=True, payment_available=True, call_history_available=True, payment_after_contact_days=3)
        self.assertEqual(score(p, f).willingness_to_pay_score, 20)

    def test_fulfillment_uses_raw_uncapped_ratio(self):
        cases = (
            (0, "0", 0),
            (25, "0.25", 1),
            (50, "0.5", 3),
            (99, "0.99", 3),
            (100, "1", 4),
            (150, "1.5", 4),
        )
        for paid, expected_ratio, expected_points in cases:
            with self.subTest(paid=paid):
                p = policy(
                    ptp_status="KEPT",
                    promise_date=REF,
                    promise_amount=Decimal(100),
                    actual_paid_amount=Decimal(paid),
                    fulfillment_ratio=min(Decimal(paid) / Decimal(100), Decimal(1)),
                    payment_ptp_ability="LOW",
                )
                result = score(p, features(ptp_available=True))
                trace = next(item for item in result.score_trace if item.rule_id == "SCORE-WIL-FULFILL-001")
                self.assertEqual(result.derived_features["ptp_fulfillment_ratio"], Decimal(expected_ratio))
                self.assertEqual(trace.evidence["ptp_fulfillment_ratio"], Decimal(expected_ratio))
                self.assertEqual(trace.points, expected_points)

    def test_contactability_lower_and_upper_bounds(self):
        self.assertEqual(score().contactability_score, 0)
        f = features(call_history_available=True, operation_history_available=True, outbound_attempts_30d=10, successful_calls_30d=7, technical_success_rate_30d=Decimal("0.7"), utc_count_30d=0, call_or_operation_evidence_30d=True, days_since_last_successful_call=7)
        self.assertEqual(score(f=f).contactability_score, 15)

    def test_timing_lower_and_upper_bounds(self):
        self.assertEqual(score().timing_opportunity_score, 0)
        p = policy(ptp_status="BROKEN", promise_date=REF, promise_amount=Decimal(1), actual_paid_amount=Decimal(0), fulfillment_ratio=Decimal(0), payment_ptp_ability="LOW", source_next_action_date=datetime(2026, 8, 28, tzinfo=timezone.utc))
        f = features(ptp_available=True, cashflow_available=True, inflow_3d=Decimal(30_000_000))
        self.assertEqual(score(p, f).timing_opportunity_score, 15)

    def test_strategic_adjustment_is_exactly_zero(self): self.assertEqual(score().strategic_adjustment_score, 0)

    def test_total_is_bounded_and_component_sum(self):
        result = score()
        self.assertGreaterEqual(result.recovery_opportunity_score, 0)
        self.assertLessEqual(result.recovery_opportunity_score, 100)
        self.assertEqual(result.recovery_opportunity_score, sum(item.score for item in result.component_breakdown))

    def test_cashflow_features_use_inclusive_source_windows(self):
        rows = [
            {"cif": "TEST", "direction": "IN", "amount": "10", "transaction_date": "2026-08-22T08:00:00+00:00", "source_type": "SALARY"},
            {"cif": "TEST", "direction": "IN", "amount": "20", "transaction_date": "2026-08-21T08:00:00+00:00", "source_type": "BUSINESS_INCOME"},
            {"cif": "TEST", "direction": "OUT", "amount": "3", "transaction_date": "2026-08-28T08:00:00+00:00", "source_type": "OTHER"},
        ]
        result = derive_features(policy(), rows, [], [], [], REF)
        self.assertEqual(result["inflow_7d"], 10)
        self.assertEqual(result["inflow_30d"], 30)
        self.assertEqual(result["net_cashflow_30d"], 27)

    def test_payment_after_contact_uses_actual_events(self):
        calls = [{"cif": "TEST", "call_type": "OUTBOUND", "status": "Success", "call_time": "2026-08-24T10:00:00+00:00"}]
        payments = [{"cif": "TEST", "amount": "100", "payment_date": "2026-08-27T09:00:00+00:00"}]
        derived = derive_features(policy(), [], payments, calls, [], REF)
        self.assertEqual(derived["payment_after_contact_days"], 3)
        self.assertEqual(score(f=derived).willingness_to_pay_score, 4)

    def test_ptp_state_scores_follow_contract(self):
        expected = {"KEPT": 8, "PARTIAL": 5, "OPEN": 3, "BROKEN": 0}
        for state, points in expected.items():
            with self.subTest(state=state):
                p = policy(ptp_status=state, promise_date=REF, promise_amount=Decimal(100), actual_paid_amount=Decimal(0), fulfillment_ratio=Decimal(0), payment_ptp_ability="LOW")
                result = score(p, features(ptp_available=True))
                trace = next(item for item in result.score_trace if item.rule_id == "SCORE-WIL-PTPSTATE-001")
                self.assertEqual(trace.points, points)

    def test_human_ability_is_marked_assessment(self):
        p = policy(ptp_status="OPEN", promise_date=REF, promise_amount=Decimal(1), actual_paid_amount=Decimal(0), fulfillment_ratio=Decimal(0), payment_ptp_ability="HIGH")
        trace = next(item for item in score(p, features(ptp_available=True)).score_trace if item.rule_id == "SCORE-WIL-HUMANABILITY-001")
        self.assertEqual(trace.points, 3); self.assertTrue(trace.evidence["human_assessment"])

    def test_utc_only_affects_contactability(self):
        base = score(f=features(operation_history_available=True, call_or_operation_evidence_30d=True, utc_count_30d=0))
        utc = score(f=features(operation_history_available=True, call_or_operation_evidence_30d=True, utc_count_30d=5))
        self.assertEqual(base.willingness_to_pay_score, utc.willingness_to_pay_score)
        self.assertNotEqual(base.contactability_score, utc.contactability_score)

    def test_nin_only_affects_contactability(self):
        base = score(f=features(operation_history_available=True, call_or_operation_evidence_30d=True))
        nin = score(f=features(operation_history_available=True, call_or_operation_evidence_30d=True, nin_present_30d=True))
        self.assertEqual(base.willingness_to_pay_score, nin.willingness_to_pay_score)
        self.assertEqual(base.contactability_score - nin.contactability_score, 3)

    def test_technical_success_does_not_create_ptp_or_state_willingness(self):
        f = features(call_history_available=True, outbound_attempts_30d=1, successful_calls_30d=1, technical_success_rate_30d=Decimal(1), days_since_last_successful_call=1, call_or_operation_evidence_30d=True)
        result = score(f=f)
        self.assertEqual(result.willingness_to_pay_score, 0)
        self.assertFalse(result.derived_features["ptp_available"])

    def test_missing_evidence_is_missing_not_negative(self):
        result = score()
        self.assertTrue(all(value == "MISSING" for value in result.data_quality.values()))
        self.assertTrue(any(trace.result == "MISSING" and trace.points == 0 for trace in result.score_trace))

    def test_zero_success_with_available_calls_is_negative_evidence_not_missing(self):
        f = features(call_history_available=True, outbound_attempts_30d=2, successful_calls_30d=0, technical_success_rate_30d=Decimal(0), call_or_operation_evidence_30d=True)
        result = score(f=f)
        recency = next(trace for trace in result.score_trace if trace.rule_id == "SCORE-CON-RECENCY-001")
        self.assertEqual((recency.result, recency.points), ("MATCH", 0))

    def test_reference_date_controls_window(self):
        row = {"cif": "TEST", "direction": "IN", "amount": "100", "transaction_date": "2026-08-22T08:00:00+00:00", "source_type": "OTHER"}
        self.assertEqual(derive_features(policy(), [row], [], [], [], REF)["inflow_7d"], 100)
        self.assertEqual(derive_features(policy(), [row], [], [], [], date(2026, 8, 29))["inflow_7d"], 0)

    def test_scoring_preserves_every_route_shape(self):
        cases = [
            policy(base_route="CALL", final_route="CALL"),
            policy(base_route="CALL", final_route="CALL", max_dpd_cif=65),
            policy(base_route="CBS", final_route="CBS"),
            policy(base_route="CBS", final_route="CBS", max_dpd_cif=65),
            policy(base_route="CBS", challenge_override_route="CALL", final_route="CALL"),
            policy(base_route="CALL", challenge_override_route="CBS", final_route="CBS"),
        ]
        for source in cases:
            with self.subTest(route=(source.base_route, source.challenge_override_route, source.final_route)):
                result = score(source)
                self.assertEqual((result.base_route, result.challenge_override_route, result.final_route), (source.base_route, source.challenge_override_route, source.final_route))

    def test_hard_suppressed_case_is_scored_but_remains_suppressed(self):
        result = score(policy(hard_suppressed=True))
        self.assertTrue(result.hard_suppressed)
        self.assertGreaterEqual(result.recovery_opportunity_score, 0)


class PortfolioRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.data = Path(cls.temp.name) / "data"
        generate_to(cls.data); cls.first = evaluate_directory(cls.data); cls.second = evaluate_directory(cls.data)
        cls.by_cif = {row.cif: row for row in cls.first}; cls.report = validate(cls.data)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_all_portfolio_bounds_and_unique_ranks(self):
        self.assertEqual(len(self.first), 3000); self.assertEqual(len(self.by_cif), 3000)
        self.assertEqual({row.recovery_rank for row in self.first}, set(range(1, 3001)))
        for row in self.first:
            self.assertTrue(all(0 <= item.score <= COMPONENT_MAX[item.name] for item in row.component_breakdown))
            self.assertTrue(0 <= row.recovery_opportunity_score <= 100)

    def test_g01_g02_product_assertion_from_actual_execution(self):
        g01, g02 = self.by_cif["GOLDEN_G01"], self.by_cif["GOLDEN_G02"]
        self.assertLess(g01.baseline_rank, g02.baseline_rank)
        self.assertLess(g02.recovery_rank, g01.recovery_rank)

    def test_golden_boundaries_and_aggregation(self):
        self.assertEqual(self.by_cif["GOLDEN_G07"].final_route, "CALL")
        self.assertEqual(self.by_cif["GOLDEN_G08"].final_route, "CBS")
        self.assertEqual(self.by_cif["GOLDEN_G19"].willingness_to_pay_score, 0)
        self.assertEqual(self.by_cif["GOLDEN_G20"].total_outstanding_cif, 400_000_000)
        self.assertEqual(self.by_cif["GOLDEN_G20"].max_dpd_cif, 12)

    def test_deterministic_scores_traces_and_ranking(self): self.assertEqual([row.to_dict() for row in self.first], [row.to_dict() for row in self.second])
    def test_validator(self): self.assertEqual(self.report["status"], "PASS", self.report["errors"])

    def test_validator_does_not_pass_unvalidated_golden_scenarios(self):
        expected_pass = {"G01", "G02", "G07", "G08", "G19", "G20"}
        self.assertEqual({sid for sid, status in self.report["golden"].items() if status == "PASS"}, expected_pass)
        self.assertEqual(
            {sid for sid, status in self.report["golden"].items() if status == "NOT_APPLICABLE"},
            {f"G{i:02d}" for i in range(1, 21)} - expected_pass,
        )
        self.assertNotIn("FAIL", self.report["golden"].values())


if __name__ == "__main__": unittest.main()
