from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from msb_agent_eval.evaluator import evaluate_local
from msb_synthetic.generator import generate_to


class Task011EvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_to(cls.data)
        cls.summary = evaluate_local(cls.data)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_golden_suite_has_24_scenarios(self):
        self.assertEqual(self.summary.metrics()["total_scenarios"], 24)

    def test_local_trust_metrics_pass(self):
        metrics = self.summary.metrics()
        self.assertEqual(metrics["decision_fidelity_rate"], 1.0)
        self.assertEqual(metrics["unknown_cif_no_fabrication_rate"], 1.0)
        self.assertEqual(metrics["guardrail_pass_rate"], 1.0)
        self.assertEqual(metrics["private_reasoning_leak_rate"], 0.0)
        self.assertEqual(metrics["tool_use_success_rate"], 1.0)

    def test_trace_has_no_credentials_or_private_reasoning(self):
        text = str(self.summary.traces)
        self.assertNotIn("Authorization", text)
        self.assertNotIn("reasoning_content", text)
        self.assertTrue(all(t["tools_used"] for t in self.summary.traces))
