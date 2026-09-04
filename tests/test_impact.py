from pathlib import Path
import tempfile
import unittest

from msb_impact import DEFAULT_ASSUMPTIONS, build_impact_report
from msb_tools.repository import ToolRepository
from msb_synthetic.generator import generate_to


class ImpactEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        data = Path(cls.temp.name) / "data"
        generate_to(data)
        cls.repository = ToolRepository(data)
        cls.default = build_impact_report(cls.repository)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_measured_portfolio_and_decisions(self):
        measured = self.default["measured"]
        self.assertEqual(measured["total_customers"], 3000)
        self.assertEqual(measured["decisions_available"], 3000)
        self.assertEqual(measured["auto_triaged_customers"], 3000)
        self.assertEqual(measured["decision_coverage_rate"], 1.0)

    def test_call_and_ranking_metrics(self):
        measured = self.default["measured"]
        self.assertEqual(measured["call_route_customers"], 1740)
        self.assertEqual(measured["call_route_but_no_call_now"], 32)
        self.assertAlmostEqual(measured["potential_call_avoidance_rate"], 32 / 1740)
        self.assertEqual(measured["active_contact_recommendations"], 1933)
        self.assertEqual(measured["ranking"]["top10_overlap"], 0)
        self.assertEqual(measured["ranking"]["top50_overlap"], 0)
        self.assertEqual(measured["ranking"]["top100_overlap"], 6)

    def test_formulas_and_provenance(self):
        d = self.default["derived"]
        self.assertAlmostEqual(d["manual_hours_baseline"], 1250)
        self.assertAlmostEqual(d["manual_hours_copilot"], 208.3333333333)
        self.assertAlmostEqual(d["review_hours_saved"], d["manual_hours_baseline"] - d["manual_hours_copilot"])
        self.assertAlmostEqual(d["call_hours_saved"], 32 / 1740 * 100 * 3 * 250 / 60)
        self.assertAlmostEqual(d["total_hours_saved"], d["review_hours_saved"] + d["call_hours_saved"])
        self.assertEqual(d["aev_estimate_vnd"], d["estimated_operational_cost_saved_vnd"])
        self.assertIsNone(self.default["recovery_uplift"])
        self.assertEqual(self.default["provenance"]["total_customers"]["type"], "MEASURED_FROM_DEMO_DATA")
        self.assertEqual(self.default["provenance"]["daily_customers_reviewed"]["type"], "CONFIGURABLE_ASSUMPTION")
        self.assertEqual(self.default["provenance"]["aev_estimate_vnd"]["type"], "DERIVED_ESTIMATE")

    def test_assumption_change_only_changes_derived(self):
        changed = build_impact_report(self.repository, {"daily_customers_reviewed": 200})
        self.assertEqual(changed["measured"], self.default["measured"])
        self.assertNotEqual(changed["derived"], self.default["derived"])

    def test_invalid_assumptions_rejected(self):
        for key, value in (("daily_customers_reviewed", -1), ("average_call_minutes", -1),
                           ("staff_cost_per_hour_vnd", -1), ("working_days_per_year", 0),
                           ("working_days_per_year", 367)):
            with self.assertRaises(ValueError):
                build_impact_report(self.repository, {key: value})


if __name__ == "__main__":
    unittest.main()
