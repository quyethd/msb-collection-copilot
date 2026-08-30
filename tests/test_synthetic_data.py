import json
import tempfile
import unittest
from pathlib import Path

from msb_synthetic.generator import DEFAULT_REFERENCE_DATE, DEFAULT_SEED, generate_to
from msb_synthetic.validate import validate


class SyntheticDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "one"
        cls.manifest = generate_to(cls.output)
        cls.report = validate(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_full_validation(self):
        self.assertEqual(self.report["status"], "PASS", self.report["errors"])
        self.assertTrue(all(v == "PASS" for v in self.report["golden"].values()))

    def test_required_scale(self):
        counts = self.manifest["counts"]
        self.assertEqual(counts["customer"], 3000)
        self.assertGreaterEqual(counts["loan_account"], 4500)
        self.assertLessEqual(counts["loan_account"], 5500)
        self.assertGreaterEqual(counts["cashflow_transaction"], 50_000)
        self.assertLessEqual(counts["cashflow_transaction"], 80_000)
        self.assertGreaterEqual(counts["payment_event"], 10_000)
        self.assertLessEqual(counts["payment_event"], 15_000)
        self.assertGreaterEqual(counts["call_history"], 5_000)
        self.assertLessEqual(counts["call_history"], 8_000)
        self.assertGreaterEqual(counts["operation_result"], 2_000)
        self.assertLessEqual(counts["operation_result"], 3_000)

    def test_same_seed_is_logically_identical(self):
        output = Path(self.temp.name) / "two"
        second = generate_to(output, DEFAULT_SEED, DEFAULT_REFERENCE_DATE)
        self.assertEqual(self.manifest["deterministic_digest"], second["deterministic_digest"])
        first_golden = (self.output / "golden_scenario_expected.csv").read_bytes()
        second_golden = (output / "golden_scenario_expected.csv").read_bytes()
        self.assertEqual(first_golden, second_golden)
        self.assertNotEqual(self.manifest["generated_at"], "")

    def test_manifest_counts_match_files(self):
        for table, expected in self.manifest["counts"].items():
            with (self.output / f"{table}.csv").open(encoding="utf-8") as handle:
                self.assertEqual(sum(1 for _ in handle) - 1, expected)


if __name__ == "__main__": unittest.main()

