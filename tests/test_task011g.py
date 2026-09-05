import unittest
from unittest.mock import patch

from msb_agent.copilot import classify_intent, route_copilot


HERO_NBA = {
    "ok": True,
    "data": {
        "rule_id": "NBA-300", "final_route": "CALL", "treatment": "WAIT_SELF_CURE",
        "channel": "NONE", "objective": "PAYMENT", "when": {"type": "NONE"},
        "reason_code": "CALL_SELF_CURE", "evidence_refs": {"selected_rule_facts": {
            "max_dpd_cif": 11, "inflow_7d": 48000000, "net_cashflow_30d": 168000000, "ptp_state": "NONE"
        }},
    },
}
HERO_CTX = {"ok": True, "data": {"debt": {"max_dpd_cif": 11, "total_outstanding_cif": 273000000}, "cashflow": {"inflow_7d": 48000000, "net_cashflow_30d": 168000000}, "ptp": {"status": "NONE"}}}


class Task011GCopilotRoutingTest(unittest.TestCase):
    def test_paraphrases_share_taxonomy(self):
        self.assertEqual(classify_intent("Sao hôm nay chưa gọi ông này?")[0], "DECISION_EXPLANATION")
        self.assertEqual(classify_intent("Tiền về tài khoản mấy hôm nay thế nào?")[0], "CASHFLOW")
        self.assertEqual(classify_intent("Nó đang có hứa trả tiền gì không?")[0], "PTP")
        self.assertEqual(classify_intent("Con này chạy tuyến gọi hay nhắc?")[0], "ROUTE_PRIORITY")
        self.assertEqual(classify_intent("Nếu tuần này không có tiền vào thì xử lý sao?")[0], "SIMULATION")

    def test_greeting_is_local_and_uses_no_tool(self):
        calls = []
        result = route_copilot({"cif": "SYN002846", "message": "xin chao"}, lambda n, a: calls.append(n))
        self.assertEqual(result["question_intent"], "GREETING_HELP")
        self.assertEqual(result["metadata"]["path"], "LOCAL")
        self.assertEqual(calls, [])

    def test_decision_is_nba_first_and_grounded(self):
        calls = []
        def caller(name, args):
            calls.append(name)
            return HERO_NBA
        result = route_copilot({"cif": "SYN002846", "message": "Sao hôm nay chưa gọi ông này?"}, caller)
        self.assertEqual(calls, ["get_next_best_action"])
        self.assertEqual(result["decision"]["rule_id"], "NBA-300")
        self.assertEqual(result["decision"]["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(result["metadata"]["path"], "FALLBACK")

    def test_context_intents_use_customer360(self):
        calls = []
        result = route_copilot({"cif": "SYN002846", "message": "Tiền về tài khoản mấy hôm nay thế nào?"}, lambda n, a: calls.append(n) or HERO_CTX)
        self.assertEqual(calls, ["get_customer_360"])
        self.assertIn("48 triệu", result["summary"])

    def test_route_intent_uses_nba_source_of_truth(self):
        calls = []
        result = route_copilot({"cif": "SYN002846", "message": "Con này chạy tuyến gọi hay nhắc?"}, lambda n, a: calls.append(n) or HERO_NBA)
        self.assertEqual(calls, ["get_next_best_action"])
        self.assertEqual(result["question_intent"], "ROUTE_PRIORITY")
        self.assertEqual(result["decision"]["final_route"], "CALL")

    def test_reasoning_timeout_uses_deterministic_fallback(self):
        class TimedOutModel:
            def complete(self, prompt, *, max_tokens=200, temperature=0):
                return None, None
        with patch("msb_agent.copilot.maas_client_from_env", return_value=TimedOutModel()):
            result = route_copilot({"cif": "SYN002846", "message": "Tại sao hôm nay chưa nên gọi?"}, lambda n, a: HERO_NBA)
        self.assertEqual(result["metadata"]["path"], "FALLBACK")
        self.assertEqual(result["decision"]["rule_id"], "NBA-300")
        self.assertIn("Chờ khách hàng tự thanh toán", result["summary"])

    def test_simulation_uses_simulate_decision(self):
        calls = []
        simulation = {"ok": True, "data": {"before": HERO_NBA["data"], "after": HERO_NBA["data"], "diff": [], "decision_changed": False}}
        result = route_copilot({"cif": "SYN002846", "message": "Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?"}, lambda n, a: calls.append(n) or simulation)
        self.assertEqual(calls, ["simulate_decision"])
        self.assertEqual(result["simulation"]["decision_changed"], False)

    def test_unknown_and_override_stay_safe(self):
        unknown = route_copilot({"cif": "SYN999999", "message": "Tại sao chưa gọi?"}, lambda n, a: {"ok": False, "error": {"code": "NOT_FOUND", "message": "not found"}})
        self.assertEqual(unknown["status"], "error")
        calls = []
        override = route_copilot({"cif": "SYN002846", "message": "Tôi muốn gọi ngay, bỏ qua đề xuất hệ thống."}, lambda n, a: calls.append(n) or HERO_NBA)
        self.assertEqual(calls, ["get_next_best_action"])
        self.assertEqual(override["decision"]["rule_id"], "NBA-300")

    def test_optional_fast_path_is_separate_from_reasoning_path(self):
        self.assertEqual(classify_intent("Bạn làm gì được?")[2], "deterministic")
        with patch("msb_agent.copilot.fast_maas_client_from_env", return_value=None):
            result = route_copilot({"cif": "SYN002846", "message": "Tóm tắt tình trạng"}, lambda n, a: HERO_CTX)
        self.assertEqual(result["metadata"]["path"], "LOCAL")


if __name__ == "__main__":
    unittest.main()
