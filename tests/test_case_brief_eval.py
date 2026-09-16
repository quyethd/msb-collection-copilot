"""TASK-015 Tool-selection evaluation and Golden scenario validation.

Evaluates ~80 natural-language utterances across all required categories.
Validates business canaries SYN002846 and SYN000746.
Checks decision parity and score parity across Golden scenarios.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from msb_synthetic.generator import generate_to
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository

from msb_case_brief.models import TOOL_ALLOWLIST, ACTION_TOOLS, MAX_TOOL_CALLS
from msb_case_brief.planner import AgentPlannerAdapter
from msb_case_brief.tool_registry import AgentToolRegistry
from msb_case_brief.generator import CaseBriefGenerator
from msb_case_brief.validator import CaseBriefValidator
from msb_case_brief.context_builder import CaseContextBuilder


def _tool_caller(repository: ToolRepository):
    def caller(name: str, args: dict[str, Any]) -> dict[str, Any]:
        return invoke_tool(name, args, repository=repository)
    return caller


EVALUATION_SET: list[tuple[str, str, set[str]]] = [
    # (category, utterance, expected_tools_that_should_be_selected)
    # --- customer facts ---
    ("customer_facts", "Tóm tắt hồ sơ này", {"get_customer_360"}),
    ("customer_facts", "Thông tin khách hàng", {"get_customer_360"}),
    ("customer_facts", "Tình trạng hồ sơ", {"get_customer_360"}),
    ("customer_facts", "DPD của khách hàng bao nhiêu", {"get_customer_360"}),
    ("customer_facts", "Dư nợ hiện tại", {"get_customer_360"}),
    ("customer_facts", "Khách hàng thuộc phân khúc nào", {"get_customer_360"}),
    ("customer_facts", "Cho tôi xem hồ sơ", {"get_customer_360"}),
    ("customer_facts", "Tổng quan khách hàng", {"get_customer_360"}),
    # --- score ---
    ("score", "Điểm cơ hội thu hồi bao nhiêu", {"get_current_decision"}),
    ("score", "Vì sao điểm là 47", {"get_score_breakdown"}),
    ("score", "Điểm được tính thế nào", {"get_score_breakdown"}),
    ("score", "Thành phần nào kéo điểm lên", {"get_score_breakdown"}),
    ("score", "Thành phần nào kéo điểm xuống", {"get_score_breakdown"}),
    ("score", "Ability score là gì", {"get_score_breakdown"}),
    ("score", "Willingness score là gì", {"get_score_breakdown"}),
    ("score", "Contactability score là gì", {"get_score_breakdown"}),
    ("score", "Timing score là gì", {"get_score_breakdown"}),
    ("score", "Breakdown điểm", {"get_score_breakdown"}),
    # --- score breakdown ---
    ("score_breakdown", "Giải thích điểm", {"get_score_breakdown"}),
    ("score_breakdown", "Điểm 47 được tính như thế nào", {"get_score_breakdown"}),
    ("score_breakdown", "Các thành phần điểm", {"get_score_breakdown"}),
    # --- cashflow ---
    ("cashflow", "Dòng tiền gần đây", {"get_cashflow_summary"}),
    ("cashflow", "Tiền vào 7 ngày", {"get_cashflow_summary"}),
    ("cashflow", "Tiền vào 3 ngày", {"get_cashflow_summary"}),
    ("cashflow", "Dòng tiền ròng 30 ngày", {"get_cashflow_summary"}),
    ("cashflow", "Có tiền vào không", {"get_cashflow_summary"}),
    ("cashflow", "Tín hiệu tự thanh toán", {"get_cashflow_summary"}),
    ("cashflow", "Thay đổi tài chính gần đây", {"get_cashflow_summary"}),
    ("cashflow", "Cashflow", {"get_cashflow_summary"}),
    ("cashflow", "Tuần này không có tiền", {"get_cashflow_summary"}),
    # --- PTP ---
    ("ptp", "PTP thế nào", {"get_ptp_context"}),
    ("ptp", "Cam kết thanh toán", {"get_ptp_context"}),
    ("ptp", "Khách hàng có hứa trả không", {"get_ptp_context"}),
    ("ptp", "Cam kết gần nhất", {"get_ptp_context"}),
    ("ptp", "Thất hứa chưa", {"get_ptp_context"}),
    ("ptp", "Thanh toán một phần", {"get_ptp_context"}),
    ("ptp", "Đã hẹn trả chưa", {"get_ptp_context"}),
    ("ptp", "Trạng thái PTP", {"get_ptp_context"}),
    # --- contact history ---
    ("contact_history", "Lịch sử liên hệ", {"get_contact_history"}),
    ("contact_history", "Lần gọi gần nhất", {"get_contact_history"}),
    ("contact_history", "Đã liên hệ chưa", {"get_contact_history"}),
    ("contact_history", "Khách có bắt máy không", {"get_contact_history"}),
    ("contact_history", "Kết quả cuộc gọi", {"get_contact_history"}),
    ("contact_history", "Callback", {"get_contact_history"}),
    ("contact_history", "Verify contact", {"get_contact_history"}),
    ("contact_history", "Thay đổi từ lần liên hệ trước", {"get_contact_history"}),
    # --- current action ---
    ("current_action", "Giờ nên làm gì", {"get_current_decision"}),
    ("current_action", "Tại sao chưa gọi", {"get_current_decision"}),
    ("current_action", "Tại sao hôm nay chưa cần gọi", {"get_current_decision"}),
    ("current_action", "Vì sao chờ", {"get_current_decision"}),
    ("current_action", "Hành động đề xuất", {"get_current_decision"}),
    ("current_action", "Kênh xử lý", {"get_current_decision"}),
    ("current_action", "Quyết định hiện tại", {"get_current_decision"}),
    ("current_action", "Đề xuất hiện tại", {"get_current_decision"}),
    # --- route ---
    ("route", "Thuộc tuyến nào", {"get_current_decision"}),
    ("route", "CALL hay CBS", {"get_current_decision"}),
    ("route", "Tuyến xử lý", {"get_current_decision"}),
    ("route", "Chạy tuyến gì", {"get_current_decision"}),
    # --- knowledge ---
    ("knowledge", "CALL khác CBS thế nào", {"find_knowledge"}),
    ("knowledge", "PTP nghĩa là gì", {"find_knowledge"}),
    ("knowledge", "Policy hoạt động ra sao", {"find_knowledge"}),
    ("knowledge", "WAIT_SELF_CURE là gì", {"find_knowledge"}),
    ("knowledge", "Recovery Opportunity là gì", {"find_knowledge"}),
    ("knowledge", "Định nghĩa CALL", {"find_knowledge"}),
    ("knowledge", "Quy trình thu hồi", {"find_knowledge"}),
    ("knowledge", "Thuật ngữ nghiệp vụ", {"find_knowledge"}),
    # --- simulation ---
    ("simulation", "Nếu tiền vào 7 ngày bằng 0 thì sao", {"simulate_decision"}),
    ("simulation", "Giả sử dòng tiền giảm", {"simulate_decision"}),
    ("simulation", "Điều gì xảy ra nếu PTP thay đổi", {"simulate_decision"}),
    ("simulation", "Mô phỏng tình huống", {"simulate_decision"}),
    ("simulation", "What if inflow is zero", {"simulate_decision"}),
    ("simulation", "Nếu không có tiền vào", {"simulate_decision"}),
    ("simulation", "Nếu thay đổi dòng tiền thì sao", {"simulate_decision"}),
    # --- follow-up ---
    ("follow_up", "Vì sao", {"get_current_decision"}),
    ("follow_up", "Thế còn dòng tiền", {"get_cashflow_summary"}),
    ("follow_up", "Vậy nên làm gì", {"get_current_decision"}),
    ("follow_up", "Liên quan gì", {"find_knowledge"}),
    # --- cross-CIF safety ---
    ("cross_cif_safety", "Tóm tắt hồ sơ", {"get_customer_360"}),
    ("cross_cif_safety", "Quyết định hiện tại", {"get_current_decision"}),
    ("cross_cif_safety", "Điểm thế nào", {"get_current_decision"}),
    ("cross_cif_safety", "PTP ra sao", {"get_ptp_context"}),
    ("cross_cif_safety", "Dòng tiền", {"get_cashflow_summary"}),
    ("cross_cif_safety", "Lịch sử gọi", {"get_contact_history"}),
    ("cross_cif_safety", "Nếu tiền vào bằng 0", {"simulate_decision"}),
    ("cross_cif_safety", "CALL là gì", {"find_knowledge"}),
]


class ToolSelectionEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = AgentToolRegistry(lambda name, args: {"ok": True, "data": {}})
        cls.planner = AgentPlannerAdapter(cls.registry)

    def test_evaluation_set_size(self):
        self.assertGreaterEqual(len(EVALUATION_SET), 50)
        self.assertLessEqual(len(EVALUATION_SET), 100)

    def test_all_categories_covered(self):
        categories = {cat for cat, _, _ in EVALUATION_SET}
        required = {"customer_facts", "score", "score_breakdown", "cashflow", "ptp", "contact_history",
                    "current_action", "route", "knowledge", "simulation", "follow_up",
                    "cross_cif_safety"}
        self.assertEqual(categories, required)

    def test_tool_selection_accuracy(self):
        correct = 0
        total = len(EVALUATION_SET)
        wrong_tool = 0
        unnecessary_tool = 0
        max_breach = 0

        for category, utterance, expected_tools in EVALUATION_SET:
            selected = set(self.planner.plan_followup("SYN002846", utterance))
            if len(selected) > MAX_TOOL_CALLS:
                max_breach += 1
            if expected_tools.issubset(selected):
                correct += 1
            else:
                wrong_tool += 1
            if len(selected - expected_tools - {"get_current_decision", "get_customer_360"}) > 2:
                unnecessary_tool += 1

        accuracy = correct / total * 100
        wrong_rate = wrong_tool / total * 100
        unnecessary_rate = unnecessary_tool / total * 100

        self.assertGreaterEqual(accuracy, 90, f"Tool selection accuracy {accuracy:.1f}% < 90%")
        self.assertLessEqual(wrong_rate, 5, f"Wrong tool rate {wrong_rate:.1f}% > 5%")
        self.assertLessEqual(unnecessary_rate, 15, f"Unnecessary tool rate {unnecessary_rate:.1f}% > 15%")
        self.assertEqual(max_breach, 0, "MAX_TOOL_CALL_BREACH > 0")

    def test_no_action_tools_in_selection(self):
        for _, utterance, _ in EVALUATION_SET:
            selected = self.planner.plan_followup("SYN002846", utterance)
            for tool in selected:
                self.assertNotIn(tool, ACTION_TOOLS)

    def test_all_selected_tools_in_allowlist(self):
        for _, utterance, _ in EVALUATION_SET:
            selected = self.planner.plan_followup("SYN002846", utterance)
            for tool in selected:
                self.assertIn(tool, TOOL_ALLOWLIST)


class GoldenEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.data = cls.root / "data"
        generate_to(cls.data)
        cls.repo = ToolRepository(cls.data)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @property
    def caller(self):
        return _tool_caller(self.repo)

    def test_syn002846_decision(self):
        nba = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=self.repo)
        self.assertTrue(nba["ok"])
        data = nba["data"]
        self.assertEqual(data["final_route"], "CALL")
        self.assertEqual(data["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(data["channel"], "NONE")

    def test_syn002846_score(self):
        ctx = invoke_tool("get_customer_360", {"cif": "SYN002846"}, repository=self.repo)
        self.assertTrue(ctx["ok"])
        score = ctx["data"]["recovery_opportunity"]["recovery_opportunity_score"]
        self.assertEqual(score, 47)

    def test_syn002846_score_breakdown(self):
        ctx = invoke_tool("get_customer_360", {"cif": "SYN002846"}, repository=self.repo)
        ro = ctx["data"]["recovery_opportunity"]
        components = {c["name"]: c["score"] for c in ro.get("component_breakdown", [])}
        self.assertEqual(components.get("BUSINESS_URGENCY"), 8)
        self.assertEqual(components.get("ABILITY_TO_PAY"), 20)
        self.assertEqual(components.get("WILLINGNESS_TO_PAY"), 4)
        self.assertEqual(components.get("CONTACTABILITY"), 11)
        self.assertEqual(components.get("TIMING_OPPORTUNITY"), 4)
        self.assertEqual(components.get("STRATEGIC_ADJUSTMENT"), 0)

    def test_syn002846_simulation_inflow_zero(self):
        sim = invoke_tool("simulate_decision", {"cif": "SYN002846", "changes": {"inflow_7d": 0}},
                          repository=self.repo)
        self.assertTrue(sim["ok"])
        after = sim["data"]["after"]
        self.assertEqual(after["treatment"], "CONTACT")
        self.assertEqual(after["channel"], "CALL")

    def test_syn000746_score(self):
        ctx = invoke_tool("get_customer_360", {"cif": "SYN000746"}, repository=self.repo)
        self.assertTrue(ctx["ok"])
        score = ctx["data"]["recovery_opportunity"]["recovery_opportunity_score"]
        self.assertEqual(score, 69)

    def test_syn002846_case_brief(self):
        gen = CaseBriefGenerator(tool_caller=self.caller, llm_complete=None)
        result = gen.generate_brief("SYN002846")
        self.assertTrue(result.brief.headline)
        self.assertEqual(result.brief.state, "BASELINE")
        self.assertTrue(result.validation.passed, result.validation.reasons)
        self.assertEqual(result.audit.cif, "SYN002846")

    def test_syn000746_case_brief(self):
        gen = CaseBriefGenerator(tool_caller=self.caller, llm_complete=None)
        result = gen.generate_brief("SYN000746")
        self.assertTrue(result.brief.headline)
        self.assertEqual(result.audit.cif, "SYN000746")

    def test_decision_parity_across_golden(self):
        golden_cifs = ["SYN002846", "SYN000746"]
        for cif in golden_cifs:
            nba = invoke_tool("get_next_best_action", {"cif": cif}, repository=self.repo)
            ctx = invoke_tool("get_customer_360", {"cif": cif}, repository=self.repo)
            self.assertEqual(nba["data"]["final_route"], ctx["data"]["policy"]["final_route"])
            self.assertEqual(nba["data"]["recovery_opportunity_score"],
                             ctx["data"]["recovery_opportunity"]["recovery_opportunity_score"])

    def test_simulation_state_not_leaked(self):
        gen = CaseBriefGenerator(tool_caller=self.caller, llm_complete=None)
        baseline = gen.generate_brief("SYN002846")
        sim = gen.generate_brief("SYN002846", simulation_changes={"inflow_7d": 0})
        self.assertEqual(baseline.brief.state, "BASELINE")
        self.assertEqual(sim.brief.state, "SIMULATION")
        self.assertNotEqual(baseline.brief.state, sim.brief.state)

    def test_cif_not_hardcoded(self):
        gen = CaseBriefGenerator(tool_caller=self.caller, llm_complete=None)
        for cif in ["SYN002846", "SYN000746", "SYN000123"]:
            result = gen.generate_brief(cif)
            self.assertEqual(result.audit.cif, cif)

    def test_followup_covers_all_categories(self):
        gen = CaseBriefGenerator(tool_caller=self.caller, llm_complete=None)
        questions = {
            "score": "Vì sao điểm là 47?",
            "cashflow": "Dòng tiền gần đây?",
            "ptp": "PTP thế nào?",
            "contact": "Lịch sử liên hệ?",
            "knowledge": "CALL khác CBS thế nào?",
            "simulation": "Nếu tiền vào 7 ngày bằng 0 thì sao?",
        }
        for category, question in questions.items():
            result = gen.answer_question("SYN002846", question)
            self.assertTrue(result.brief.headline, f"Failed for {category}: {question}")
            self.assertLessEqual(len(result.tools_used), MAX_TOOL_CALLS)

    def test_fallback_level3_always_works(self):
        gen = CaseBriefGenerator(tool_caller=self.caller, llm_complete=None)
        for cif in ["SYN002846", "SYN000746"]:
            result = gen.generate_brief(cif)
            self.assertEqual(result.agent_path, "DETERMINISTIC")
            self.assertTrue(result.brief.headline)
