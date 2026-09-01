from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from msb_evaluation.engine import (
    SYNTHETIC_STATISTIC_LABEL, arithmetic_mean, classify_movement, component_statistics,
    evaluate_cifs, movement_factors, normalized_rank_delta, route_counts,
    spearman_rank_correlation, summarize, top_k_summary,
)
from msb_evaluation.io import evaluate_directory
from msb_evaluation.validate import validate
from msb_policy.io import evaluate_directory as evaluate_policy_directory
from msb_recovery.io import evaluate_directory as evaluate_recovery_directory
from msb_synthetic.generator import generate_to


class EvaluationFormulaTest(unittest.TestCase):
    def test_movement_formulas(self):
        self.assertEqual(classify_movement(1), "PROMOTED")
        self.assertEqual(classify_movement(-1), "DEMOTED")
        self.assertEqual(classify_movement(0), "UNCHANGED")
        self.assertEqual(abs(-17), 17)
        self.assertEqual(normalized_rank_delta(2, 5), Decimal("0.5"))
        self.assertEqual(normalized_rank_delta(0, 1), 0)

    def test_spearman_toy_rankings(self):
        class Row:
            def __init__(self, baseline, recovery):
                self.baseline_rank, self.recovery_rank = baseline, recovery
                self.rank_delta = baseline - recovery
        self.assertEqual(spearman_rank_correlation([Row(1, 1), Row(2, 2), Row(3, 3)]), 1)
        self.assertEqual(spearman_rank_correlation([Row(1, 3), Row(2, 2), Row(3, 1)]), -1)

    def test_top_k_membership_overlap_and_displacement(self):
        class Row:
            def __init__(self, cif, baseline, recovery):
                self.cif, self.baseline_rank, self.recovery_rank = cif, baseline, recovery
        rows = [Row(f"C{i}", i, 11 - i) for i in range(1, 11)]
        result = top_k_summary(rows, 3)
        self.assertEqual(result["baseline_count"], 3)
        self.assertEqual(result["recovery_count"], 3)
        self.assertEqual(result["overlap_count"], 0)
        self.assertEqual(result["overlap_ratio"], 0)
        self.assertEqual(result["promoted_into_recovery_top_k_count"], 3)
        self.assertEqual(result["demoted_out_of_baseline_top_k_count"], 3)

    def test_route_counts_and_exact_mean(self):
        class Row:
            def __init__(self, route): self.final_route = route
        self.assertEqual(route_counts([Row("CALL"), Row("CBS"), Row("CALL")]), {"CALL": 2, "CBS": 1})
        self.assertEqual(arithmetic_mean([1, 2]), Decimal("1.5"))


class PortfolioEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_to(cls.data)
        cls.recovery = evaluate_recovery_directory(cls.data)
        cls.rows, cls.summary = evaluate_directory(cls.data)
        cls.rows_again, cls.summary_again = evaluate_directory(cls.data)
        cls.by_cif = {row.cif: row for row in cls.rows}
        cls.report = validate(cls.data)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_all_cifs_and_complete_top_k_membership(self):
        self.assertEqual(len(self.rows), 3000)
        self.assertEqual(len(self.by_cif), 3000)
        self.assertEqual({row.baseline_rank for row in self.rows}, set(range(1, 3001)))
        self.assertEqual({row.recovery_rank for row in self.rows}, set(range(1, 3001)))
        for k in (10, 50, 100):
            self.assertEqual(sum(row.baseline_rank <= k for row in self.rows), k)
            self.assertEqual(sum(row.recovery_rank <= k for row in self.rows), k)

    def test_movement_and_factor_contract(self):
        for row in self.rows:
            self.assertEqual(row.rank_delta, row.baseline_rank - row.recovery_rank)
            self.assertEqual(row.absolute_rank_delta, abs(row.rank_delta))
            self.assertLessEqual(len(row.primary_movement_factors), 3)
            self.assertTrue(all(factor.score > 0 for factor in row.movement_factors))
            self.assertEqual(list(row.movement_factors), sorted(row.movement_factors, key=lambda item: (-item.score, item.factor)))

    def test_top_k_and_profiles(self):
        for k in (10, 50, 100):
            item = self.summary["top_k"][str(k)]
            self.assertEqual(item["promoted_into_recovery_top_k_count"], item["demoted_out_of_baseline_top_k_count"])
            self.assertIn(str(k), self.summary["top_k_component_profiles"])
            self.assertIn(f"baseline_top_{k}", self.summary["route_composition"])
            self.assertIn(f"recovery_top_{k}", self.summary["route_composition"])

    def test_statistics_and_label(self):
        expected = component_statistics(self.rows)
        self.assertEqual(self.summary["component_statistics"], {key: {inner: str(value) if isinstance(value, Decimal) else value for inner, value in item.items()} for key, item in expected.items()})
        self.assertEqual(self.summary["synthetic_statistic_label"], SYNTHETIC_STATISTIC_LABEL)

    def test_hero_and_boundaries(self):
        g01, g02 = self.by_cif["GOLDEN_G01"], self.by_cif["GOLDEN_G02"]
        self.assertLess(g01.baseline_rank, g02.baseline_rank)
        self.assertLess(g02.recovery_rank, g01.recovery_rank)
        self.assertEqual((g01.movement, g02.movement), ("DEMOTED", "PROMOTED"))
        self.assertEqual(self.by_cif["GOLDEN_G07"].final_route, "CALL")
        self.assertEqual(self.by_cif["GOLDEN_G08"].final_route, "CBS")
        self.assertEqual(next(row for row in self.recovery if row.cif == "GOLDEN_G19").willingness_to_pay_score, 0)
        self.assertEqual(self.by_cif["GOLDEN_G20"].total_outstanding_cif, Decimal(400_000_000))
        self.assertEqual(self.by_cif["GOLDEN_G20"].max_dpd_cif, 12)

    def test_authoritative_fields_immutable(self):
        policies = {row.cif: row for row in evaluate_policy_directory(self.data)}
        recovery = {row.cif: row for row in self.recovery}
        for cif, row in self.by_cif.items():
            for field in ("base_route", "challenge_override_route", "final_route", "hard_suppressed", "total_outstanding_cif", "max_dpd_cif"):
                self.assertEqual(getattr(row, field), getattr(policies[cif], field))
            for field in ("baseline_rank", "recovery_rank", "recovery_opportunity_score", "business_urgency_score", "ability_to_pay_score", "willingness_to_pay_score", "contactability_score", "timing_opportunity_score", "strategic_adjustment_score"):
                self.assertEqual(getattr(row, field), getattr(recovery[cif], field))

    def test_deterministic_rerun(self):
        self.assertEqual([row.to_dict() for row in self.rows], [row.to_dict() for row in self.rows_again])
        self.assertEqual(self.summary, self.summary_again)

    def test_no_forbidden_metrics_and_truthful_golden_status(self):
        serialized = str(self.summary).lower()
        for key in ("precision", "recall", "auc", "roi", "aev", "expected_recovery", "recovery_probability"):
            self.assertNotIn(key, serialized)
        expected_pass = {"G01", "G02", "G07", "G08", "G19", "G20"}
        self.assertEqual({sid for sid, status in self.report["golden"].items() if status == "PASS"}, expected_pass)
        self.assertTrue(all(status == "NOT_APPLICABLE" for sid, status in self.report["golden"].items() if sid not in expected_pass))

    def test_validator(self):
        self.assertEqual(self.report["status"], "PASS", self.report["errors"])


if __name__ == "__main__": unittest.main()
