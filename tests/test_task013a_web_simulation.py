import unittest
from pathlib import Path
from unittest.mock import patch

from msb_agent.copilot import _simulation_changes, classify_intent, route_copilot
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository


class WebSimulationNLUCorrectiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = ToolRepository(Path("build/synthetic-data"))

    def call(self, payload):
        return route_copilot(
            payload,
            lambda name, args: invoke_tool(name, args, repository=self.repo),
        )

    def test_accepted_zero_inflow_phrases_extract_one_canonical_change(self):
        phrases = (
            "tiền vào 7 ngày bằng 0",
            "Nếu tiền vào 7 ngày bằng 0 thì quyết định có thay đổi không?",
            "Nếu tiền vào 7 ngày bằng 0 thì sao?",
            "không có tiền vào 7 ngày",
            "tiền vào tuần này bằng 0",
            "giả sử 7 ngày tới không có tiền vào",
            "nếu nó không có tiền vào tuần này thì sao",
            "Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertEqual(_simulation_changes(phrase, {}), {"inflow_7d": 0})

    def test_current_fact_and_knowledge_phrases_do_not_extract_simulation_change(self):
        phrases = (
            "tiền vào 7 ngày là bao nhiêu?",
            "dòng tiền gần đây thế nào?",
            "khách này có tiền vào không?",
            "cho tôi xem tiền vào 7 ngày",
            "CALL và CBS khác nhau thế nào?",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertEqual(_simulation_changes(phrase, {}), {})
                self.assertNotEqual(classify_intent(phrase)[0], "SIMULATION")

    def test_exact_production_phrase_uses_real_simulation_engine(self):
        phrase = "Nếu tiền vào 7 ngày bằng 0 thì quyết định có thay đổi không?"
        with patch("msb_agent.copilot.maas_client_from_env", return_value=None):
            result = self.call({"cif": "SYN002846", "message": phrase})
        simulation = result["simulation"]
        self.assertEqual(result["question_intent"], "SIMULATION")
        self.assertEqual(simulation["changes_applied"], {"inflow_7d": 0})
        self.assertEqual(simulation["before"]["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(simulation["before"]["channel"], "NONE")
        self.assertEqual(simulation["after"]["treatment"], "CONTACT")
        self.assertEqual(simulation["after"]["channel"], "CALL")

    def test_short_production_phrase_has_same_real_result(self):
        with patch("msb_agent.copilot.maas_client_from_env", return_value=None):
            result = self.call({"cif": "SYN002846", "message": "tiền vào 7 ngày bằng 0"})
        simulation = result["simulation"]
        self.assertEqual(simulation["changes_applied"], {"inflow_7d": 0})
        self.assertEqual((simulation["after"]["treatment"], simulation["after"]["channel"]), ("CONTACT", "CALL"))

    def test_simulation_followup_reuses_after_state_for_same_cif(self):
        with patch("msb_agent.copilot.maas_client_from_env", return_value=None):
            first = self.call({"cif": "SYN002846", "message": "tiền vào 7 ngày bằng 0"})
            second = self.call({
                "cif": "SYN002846",
                "message": "Vậy nên làm gì?",
                "conversation_context": {
                    "active_cif": "SYN002846",
                    "previous_intent": "SIMULATION",
                    "last_simulation_changes": first["simulation"]["changes_applied"],
                },
            })
        self.assertEqual(second["question_intent"], "SIMULATION")
        self.assertEqual(second["simulation"]["changes_applied"], {"inflow_7d": 0})
        self.assertEqual((second["decision"]["treatment"], second["decision"]["channel"]), ("CONTACT", "CALL"))

    def test_simulation_context_cannot_leak_to_switched_cif(self):
        with patch("msb_agent.copilot.maas_client_from_env", return_value=None):
            result = self.call({
                "cif": "SYN000746",
                "message": "Vậy nên làm gì?",
                "conversation_context": {
                    "active_cif": "SYN002846",
                    "previous_intent": "SIMULATION",
                    "last_simulation_changes": {"inflow_7d": 0},
                },
            })
        self.assertEqual(result["cif"], "SYN000746")
        self.assertNotIn("simulation", result)
        self.assertNotEqual(result.get("question_intent"), "SIMULATION")


if __name__ == "__main__":
    unittest.main()
