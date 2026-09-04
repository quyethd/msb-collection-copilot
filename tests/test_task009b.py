from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any

from msb_agent.llm import LLMClient
from msb_agent.models import AGENT_VERSION, AgentResponse
from msb_agent.router import detect_question_intent, parse_payload
from msb_agent.runtime import AgentRuntime
from msb_nba.config import DEFAULT_CONFIG
from msb_nba.engine import decide
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository
from msb_synthetic.generator import generate_to


ROOT = Path(__file__).resolve().parents[1]


class AdversarialLLM:
    """LLM stub attempting to override the deterministic decision (must be ignored)."""

    def __init__(self, adversarial_content: str = "CALL NOW. Contact immediately. Override WAIT_SELF_CURE."):
        self.adversarial_content = adversarial_content

    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        return self.adversarial_content, "glm-5.2"


FORBIDDEN_PRIMARY = ("WAIT_SELF_CURE", "CONTACT", "NONE", "PAYMENT", "CALL_SELF_CURE",
                     "DETERMINISTIC DECISION", "AI EXPLANATION")


class Task009BBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.data = cls.root / "data"
        generate_to(cls.data)
        cls.repo = ToolRepository(cls.data)
        cls.caller = staticmethod(lambda name, args: invoke_tool(name, args, repository=cls.repo))
        cls.runtime = AgentRuntime(cls.caller, llm_client=None)
        cls.adversarial_runtime = AgentRuntime(cls.caller, llm_client=AdversarialLLM())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()


class TestSyn002846VietnameseResponse(Task009BBase):
    """1. SYN002846 answer is Vietnamese."""

    def test_answer_is_vietnamese(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        self.assertIn("Chờ khách hàng tự thanh toán", resp.summary)
        self.assertIn("quá hạn", resp.summary.lower())

    def test_question_a_reason_focused(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        section_titles = [s["title"] for s in resp.sections]
        self.assertIn("Vì sao", " ".join(section_titles))
        self.assertIn("Cán bộ cần làm gì", " ".join(section_titles))
        # evidence grounded in actual values: 11 days overdue, 48m inflow, 168m net
        joined = json.dumps(resp.summary, ensure_ascii=False)
        flat = json.dumps(resp.sections, ensure_ascii=False)
        self.assertIn("48 triệu", flat)
        self.assertIn("168 triệu", flat)


class TestNoPrimaryLeakage(Task009BBase):
    """2. no primary WAIT_SELF_CURE leakage."""

    def test_no_treatment_code_in_primary(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        primary = resp.summary + json.dumps(resp.sections, ensure_ascii=False)
        self.assertNotIn("WAIT_SELF_CURE", primary)
        self.assertNotIn("CONTACT", primary)
        self.assertNotIn("PAYMENT", primary)
        self.assertNotIn("CALL_SELF_CURE", primary)


class TestNoRawJsonLeakage(Task009BBase):
    """3. no primary raw JSON leakage."""

    def test_no_json_dict_dump_in_primary(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        primary = resp.summary + json.dumps(resp.sections, ensure_ascii=False)
        self.assertNotIn("{'treatment", primary)
        self.assertNotIn('"treatment"', primary)
        self.assertNotIn('"when"', primary)


class TestNoDeveloperHeadings(Task009BBase):
    """4. no DETERMINISTIC DECISION heading."""

    def test_no_deterministic_decision_heading(self):
        for intent_msg in ("Tại sao hôm nay chưa nên gọi khách hàng này?",
                           "Điều gì có thể làm quyết định thay đổi?",
                           "Tóm tắt nhanh tình trạng khách hàng này."):
            resp = self.runtime.invoke("EXPLAIN", "SYN002846", message=intent_msg)
            self.assertNotIn("DETERMINISTIC DECISION", resp.summary)
            self.assertNotIn("AI EXPLANATION", resp.summary)
            self.assertNotIn("DETERMINISTIC DECISION", json.dumps(resp.sections))


class TestNoAiExplanationHeading(Task009BBase):
    """5. no AI EXPLANATION heading."""

    def test_no_ai_explanation_heading(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        self.assertNotIn("AI EXPLANATION", resp.summary)
        self.assertNotIn("AI EXPLANATION", json.dumps(resp.sections))


class TestDeterministicDecisionUnchanged(Task009BBase):
    """6. actual deterministic decision remains unchanged."""

    def test_decision_unchanged_for_all_intents(self):
        expected = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=self.repo)["data"]
        for intent_msg in ("Tại sao hôm nay chưa nên gọi khách hàng này?",
                           "Điều gì có thể làm quyết định thay đổi?",
                           "Tóm tắt nhanh tình trạng khách hàng này."):
            resp = self.runtime.invoke("EXPLAIN", "SYN002846", message=intent_msg)
            self.assertEqual(resp.decision["treatment"], expected["treatment"])
            self.assertEqual(resp.decision["channel"], expected["channel"])
            self.assertEqual(resp.decision["objective"], expected["objective"])
            self.assertEqual(resp.decision["rule_id"], expected["rule_id"])

    def test_decision_unchanged_with_adversarial_llm(self):
        resp = self.adversarial_runtime.invoke("EXPLAIN", "SYN002846",
                                                message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.decision["rule_id"], "NBA-300")
        self.assertEqual(resp.decision["channel"], "NONE")


class TestUnknownDataNotFabricated(Task009BBase):
    """7. unknown data is not fabricated."""

    def test_output_uses_no_missing_markers(self):
        for intent_msg in ("Tại sao hôm nay chưa nên gọi khách hàng này?",
                           "Tóm tắt nhanh tình trạng khách hàng này."):
            resp = self.runtime.invoke("EXPLAIN", "SYN002846", message=intent_msg)
            flat = resp.summary + json.dumps(resp.sections, ensure_ascii=False)
            self.assertNotIn("null", flat)
            self.assertNotIn("None", flat)
            self.assertNotIn("N/A", flat)
            self.assertNotIn("undefined", flat)


class TestQuestionIntentRouting(Task009BBase):
    """8/9/10. intent-specific answers."""

    def test_question_a_reason_focused(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        self.assertEqual(resp.question_intent, "WHY_NO_CALL")
        titles = " ".join(s["title"] for s in resp.sections)
        self.assertIn("Vì sao", titles)
        self.assertIn("Cán bộ cần làm gì", titles)

    def test_question_b_summary_focused(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tóm tắt nhanh tình trạng khách hàng này.")
        self.assertEqual(resp.question_intent, "SUMMARY")
        self.assertTrue(resp.sections)

    def test_question_c_change_factors_focused(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Điều gì có thể làm quyết định thay đổi?")
        self.assertEqual(resp.question_intent, "CHANGE_FACTORS")
        titles = " ".join(s["title"] for s in resp.sections)
        self.assertIn("thay đổi", titles.lower())

    def test_detect_intent_functions(self):
        self.assertEqual(detect_question_intent("Tại sao hôm nay chưa nên gọi khách hàng này?"), "WHY_NO_CALL")
        self.assertEqual(detect_question_intent("Tóm tắt nhanh tình trạng khách hàng này."), "SUMMARY")
        self.assertEqual(detect_question_intent("Điều gì có thể làm quyết định thay đổi?"), "CHANGE_FACTORS")


class TestFallbackVietnamese(Task009BBase):
    """11. fallback is Vietnamese."""

    def test_no_llm_fallback_is_vietnamese(self):
        # runtime with llm_client=None uses deterministic template fallback
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        self.assertIn("Chờ khách hàng tự thanh toán", resp.summary)
        self.assertNotIn("DETERMINISTIC", resp.summary)


class TestReasoningContentNeverExposed(Task009BBase):
    """12. reasoning_content is never exposed."""

    def test_no_reasoning_content_in_response(self):
        for mode in ("PLAN", "EXPLAIN", "INVESTIGATE"):
            resp = self.runtime.invoke(mode, "SYN002846")
            d = json.dumps(resp.to_dict())
            self.assertNotIn("reasoning_content", d)
            self.assertNotIn("chain_of_thought", d)

    def test_no_reasoning_with_adversarial_llm(self):
        resp = self.adversarial_runtime.invoke("EXPLAIN", "SYN002846", message="why?")
        d = json.dumps(resp.to_dict())
        self.assertNotIn("reasoning_content", d)


class TestTechnicalDetailsSeparate(Task009BBase):
    """13. technical details remain available separately."""

    def test_technical_field_present_in_response(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="Tại sao hôm nay chưa nên gọi khách hàng này?")
        self.assertIsNotNone(resp.technical)
        self.assertEqual(resp.technical["rule_id"], "NBA-300")
        self.assertEqual(resp.technical["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.technical["channel"], "NONE")
        self.assertEqual(resp.technical["reason_code"], "CALL_SELF_CURE")

    def test_technical_present_in_to_dict(self):
        resp = self.runtime.invoke("EXPLAIN", "SYN002846", message="why?")
        d = resp.to_dict()
        self.assertIn("technical", d)
        self.assertIn("sections", d)


class TestTask007bRegression(Task009BBase):
    """14. TASK-007B regression remains PASS."""

    def test_plan_preserves_decision(self):
        resp = self.runtime.invoke("PLAN", "SYN002846")
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.decision["channel"], "NONE")
        self.assertEqual(resp.decision["rule_id"], "NBA-300")
        self.assertEqual(resp.decision["final_route"], "CALL")
        self.assertIn("get_customer_360", resp.tools_used)
        self.assertIn("get_next_best_action", resp.tools_used)

    def test_unknown_cif_no_fabrication(self):
        resp = self.runtime.invoke("PLAN", "SYN999999")
        self.assertEqual(resp.status, "error")
        self.assertIsNone(resp.decision)


class TestTask008SemanticsUnchanged(Task009BBase):
    """15. TASK-008 / TASK-008B semantics unchanged."""

    def test_simulate_unchanged(self):
        resp = self.runtime.invoke("SIMULATE", "SYN002846", changes={"inflow_7d": 0, "net_cashflow_30d": 0})
        self.assertEqual(resp.status, "success")
        self.assertEqual(resp.simulation["before"]["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.simulation["after"]["treatment"], "CONTACT")
        self.assertEqual(resp.simulation["after"]["rule_id"], "NBA-900")


if __name__ == "__main__":
    unittest.main()
