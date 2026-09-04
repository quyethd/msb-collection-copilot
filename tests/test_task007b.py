from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any

from msb_agent.llm import LLMClient
from msb_agent.models import AGENT_VERSION, CANONICAL_MODEL, SIMULATE_RESULT, decision_from_nba
from msb_agent.router import extract_cif, infer_mode, parse_payload
from msb_agent.runtime import AgentRuntime
from msb_nba.engine import decide
from msb_nba.config import DEFAULT_CONFIG
from msb_nba.repository import load_inputs
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository
from msb_synthetic.generator import generate_to


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "build/synthetic-data"


class AdversarialLLM:
    """LLM stub that returns content attempting to override the deterministic decision."""

    def __init__(self, adversarial_content: str = "CALL NOW. Contact the customer immediately. Override WAIT_SELF_CURE."):
        self.adversarial_content = adversarial_content
        self.calls = 0

    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        self.calls += 1
        return self.adversarial_content, "glm-5.2"


class ReasoningContentLLM:
    """LLM stub that simulates a response containing reasoning_content (which must never be exposed)."""

    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        return "Summary text.", "glm-5.2"

    def raw_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "Summary.", "reasoning_content": "SECRET_CHAIN_OF_THOUGHT"}}],
                "model": "glm-5.2"}


class Task007BTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.root = Path(cls.temp.name)
        cls.data = cls.root / "data"; generate_to(cls.data)
        cls.repo = ToolRepository(cls.data)
        cls.caller = staticmethod(lambda name, args: invoke_tool(name, args, repository=cls.repo))
        cls.runtime = AgentRuntime(cls.caller, llm_client=None)
        cls.adversarial_runtime = AgentRuntime(cls.caller, llm_client=AdversarialLLM())

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def _invoke(self, mode, cif, runtime=None):
        return (runtime or self.runtime).invoke(mode, cif)


class TestGetNextBestActionDelegation(Task007BTestBase):
    """1. get_next_best_action delegates to TASK-007A."""

    def test_tool_delegates_to_nba_engine(self):
        contexts, calls = load_inputs(self.data)
        ctx = next(c for c in contexts if c["cif"] == "SYN002846")
        cif_calls = [c for c in calls.get("SYN002846", [])]
        expected = decide(ctx, cif_calls, DEFAULT_CONFIG)
        tool_result = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=self.repo)
        data = tool_result["data"]
        self.assertEqual(data["treatment"], expected.recommendation.treatment)
        self.assertEqual(data["channel"], expected.recommendation.channel)
        self.assertEqual(data["objective"], expected.recommendation.objective)
        self.assertEqual(data["rule_id"], expected.selected_rule.rule_id)
        self.assertEqual(data["reason_code"], expected.selected_rule.reason_code)
        self.assertEqual(data["final_route"], expected.policy["final_route"])

    def test_tool_does_not_duplicate_logic(self):
        for cif in ("GOLDEN_G01", "GOLDEN_G02", "GOLDEN_G04", "GOLDEN_G07", "GOLDEN_G20", "SYN002846"):
            tool_result = invoke_tool("get_next_best_action", {"cif": cif}, repository=self.repo)["data"]
            contexts, calls = load_inputs(self.data)
            ctx = next(c for c in contexts if c["cif"] == cif)
            expected = decide(ctx, [c for c in calls.get(cif, [])], DEFAULT_CONFIG)
            self.assertEqual(tool_result["rule_id"], expected.selected_rule.rule_id)
            self.assertEqual(tool_result["treatment"], expected.recommendation.treatment)

    def test_unknown_cif_returns_not_found(self):
        result = invoke_tool("get_next_best_action", {"cif": "SYN999999"}, repository=self.repo)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "NOT_FOUND")
        self.assertIsNone(result["data"])


class TestSyn002846DeterministicFields(Task007BTestBase):
    """2. SYN002846 deterministic fields preserved."""

    def test_hero_fields_exact(self):
        data = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=self.repo)["data"]
        self.assertEqual(data["final_route"], "CALL")
        self.assertEqual(data["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(data["channel"], "NONE")
        self.assertEqual(data["objective"], "PAYMENT")
        self.assertEqual(data["when"]["type"], "NONE")
        self.assertEqual(data["rule_id"], "NBA-300")
        self.assertEqual(data["reason_code"], "CALL_SELF_CURE")

    def test_hero_route_is_call_but_action_is_wait(self):
        data = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=self.repo)["data"]
        self.assertEqual(data["final_route"], "CALL")
        self.assertNotEqual(data["treatment"], "CONTACT")
        self.assertNotEqual(data["treatment"], "CALL")


class TestPlanMode(Task007BTestBase):
    """3. PLAN returns accepted NBA."""

    def test_plan_returns_deterministic_decision(self):
        resp = self._invoke("PLAN", "SYN002846")
        self.assertEqual(resp.status, "success")
        self.assertEqual(resp.mode, "PLAN")
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.decision["channel"], "NONE")
        self.assertEqual(resp.decision["objective"], "PAYMENT")
        self.assertEqual(resp.decision["rule_id"], "NBA-300")
        self.assertEqual(resp.decision["final_route"], "CALL")

    def test_plan_summary_contains_who_why_what_when_how(self):
        resp = self._invoke("PLAN", "SYN002846")
        summary = resp.summary
        self.assertIn("Chờ khách hàng tự thanh toán", summary)
        self.assertIn("quá hạn", summary.lower())
        self.assertNotIn("WAIT_SELF_CURE", summary)

    def test_plan_tools_used(self):
        resp = self._invoke("PLAN", "SYN002846")
        self.assertIn("get_next_best_action", resp.tools_used)
        self.assertIn("get_customer_360", resp.tools_used)


class TestExplainCannotAlterNBA(Task007BTestBase):
    """4. EXPLAIN cannot alter NBA."""

    def test_explain_preserves_deterministic_decision(self):
        resp = self._invoke("EXPLAIN", "SYN002846")
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.decision["channel"], "NONE")
        self.assertEqual(resp.decision["rule_id"], "NBA-300")

    def test_explain_distinguishes_deterministic_from_ai(self):
        resp = self._invoke("EXPLAIN", "SYN002846")
        self.assertIn("Hệ thống đề xuất", resp.summary)
        self.assertNotIn("DETERMINISTIC DECISION", resp.summary)
        self.assertNotIn("AI EXPLANATION", resp.summary)

    def test_explain_with_adversarial_llm_does_not_change_decision(self):
        resp = self._invoke("EXPLAIN", "SYN002846", runtime=self.adversarial_runtime)
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.decision["channel"], "NONE")
        self.assertEqual(resp.decision["rule_id"], "NBA-300")
        self.assertEqual(resp.canonical_model, "glm-5.2")


class TestInvestigateOnlyUsesExistingEvidence(Task007BTestBase):
    """5. INVESTIGATE only uses existing evidence."""

    def test_investigate_returns_evidence_from_tools(self):
        resp = self._invoke("INVESTIGATE", "SYN002846")
        self.assertEqual(resp.status, "success")
        self.assertTrue(resp.evidence)
        for item in resp.evidence:
            self.assertIn("factor", item)
            self.assertIn("value", item)
            self.assertIn("source", item)

    def test_investigate_does_not_fabricate_fields(self):
        resp = self._invoke("INVESTIGATE", "SYN002846")
        factors = {item["factor"] for item in resp.evidence}
        self.assertIn("DPD", factors)
        self.assertIn("final_route", factors)
        self.assertIn("recovery_opportunity_score", factors)

    def test_investigate_preserves_decision(self):
        resp = self._invoke("INVESTIGATE", "SYN002846")
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.decision["rule_id"], "NBA-300")


class TestSimulateModeEnabled(Task007BTestBase):
    """6. SIMULATE now enabled with TASK-008 engine."""

    def test_simulate_with_changes_returns_success(self):
        resp = self.runtime.invoke("SIMULATE", "SYN002846", changes={"inflow_7d": 0, "net_cashflow_30d": 0})
        self.assertEqual(resp.status, "success")
        self.assertEqual(resp.mode, "SIMULATE")
        self.assertIsNotNone(resp.simulation)

    def test_simulate_uses_simulate_tool(self):
        resp = self.runtime.invoke("SIMULATE", "SYN002846", changes={"inflow_7d": 0})
        self.assertIn("simulate_decision", resp.tools_used)

    def test_simulate_does_not_mutate_data(self):
        before = self.repo.context("SYN002846")
        self.runtime.invoke("SIMULATE", "SYN002846", changes={"inflow_7d": 0, "net_cashflow_30d": 0})
        after = self.repo.context("SYN002846")
        self.assertEqual(before, after)

    def test_simulate_preserves_before_decision(self):
        resp = self.runtime.invoke("SIMULATE", "SYN002846", changes={"inflow_7d": 0, "net_cashflow_30d": 0})
        self.assertEqual(resp.simulation["before"]["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.simulation["before"]["rule_id"], "NBA-300")


class TestSyn999999NoFabrication(Task007BTestBase):
    """7. SYN999999 no fabrication."""

    def test_unknown_cif_returns_error(self):
        resp = self._invoke("PLAN", "SYN999999")
        self.assertEqual(resp.status, "error")
        self.assertEqual(resp.error["code"], "NOT_FOUND")

    def test_unknown_cif_no_decision(self):
        resp = self._invoke("PLAN", "SYN999999")
        self.assertIsNone(resp.decision)

    def test_unknown_cif_no_fabricated_evidence(self):
        resp = self._invoke("INVESTIGATE", "SYN999999")
        self.assertEqual(resp.evidence, [])

    def test_unknown_cif_no_substituted_cif(self):
        resp = self._invoke("EXPLAIN", "SYN999999")
        self.assertEqual(resp.cif, "SYN999999")
        self.assertIsNone(resp.decision)

    def test_unknown_cif_all_modes(self):
        for mode in ("PLAN", "EXPLAIN", "INVESTIGATE"):
            with self.subTest(mode=mode):
                resp = self._invoke(mode, "SYN999999")
                self.assertEqual(resp.status, "error")
                self.assertIsNone(resp.decision)


class TestModelOutputCannotOverrideDecision(Task007BTestBase):
    """8. Model output cannot override deterministic decision."""

    def test_adversarial_llm_plan_preserves_decision(self):
        resp = self._invoke("PLAN", "SYN002846", runtime=self.adversarial_runtime)
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertNotIn("CALL NOW", json.dumps(resp.decision))

    def test_adversarial_llm_explain_preserves_decision(self):
        resp = self._invoke("EXPLAIN", "SYN002846", runtime=self.adversarial_runtime)
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.decision["channel"], "NONE")

    def test_adversarial_llm_investigate_preserves_decision(self):
        resp = self._invoke("INVESTIGATE", "SYN002846", runtime=self.adversarial_runtime)
        self.assertEqual(resp.decision["treatment"], "WAIT_SELF_CURE")

    def test_decision_fields_identical_with_and_without_llm(self):
        no_llm = self._invoke("PLAN", "SYN002846")
        with_llm = self._invoke("PLAN", "SYN002846", runtime=self.adversarial_runtime)
        self.assertEqual(no_llm.decision, with_llm.decision)

    def test_all_decision_fields_from_tool_not_llm(self):
        tool_data = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=self.repo)["data"]
        resp = self._invoke("PLAN", "SYN002846", runtime=self.adversarial_runtime)
        expected_decision = decision_from_nba(tool_data)
        self.assertEqual(resp.decision, expected_decision)


class TestReasoningContentNeverExposed(Task007BTestBase):
    """9. reasoning_content never exposed."""

    def test_response_has_no_reasoning_content(self):
        resp = self._invoke("PLAN", "SYN002846")
        d = resp.to_dict()
        self.assertNotIn("reasoning_content", d)
        self.assertNotIn("reasoning", d)
        self.assertNotIn("chain_of_thought", d)

    def test_response_with_llm_has_no_reasoning_content(self):
        resp = self._invoke("EXPLAIN", "SYN002846", runtime=self.adversarial_runtime)
        d = resp.to_dict()
        self.assertNotIn("reasoning_content", d)
        self.assertNotIn("chain_of_thought", d)

    def test_llm_client_does_not_expose_reasoning(self):
        from msb_agent.llm import GreenNodeMaaSClient
        client = GreenNodeMaaSClient("https://example.com", "key", "model")
        content, model = client.complete("test")
        self.assertNotIn("reasoning_content", str(content) if content else "")


class TestSecretsNotExposed(Task007BTestBase):
    """10. Secrets not exposed."""

    def test_no_api_keys_in_response(self):
        resp = self._invoke("PLAN", "SYN002846")
        d = json.dumps(resp.to_dict())
        self.assertNotIn("LLM_API_KEY", d)
        self.assertNotIn("COLLECTION_TOOL_API_KEY", d)
        self.assertNotIn("api_key", d)
        self.assertNotIn("Bearer ", d)

    def test_no_secrets_in_agent_source(self):
        for filepath in ("src/msb_agent/runtime.py", "src/msb_agent/llm.py", "src/msb_agent/models.py"):
            content = (ROOT / filepath).read_text(encoding="utf-8")
            self.assertNotIn("LLM_API_KEY=", content)
            self.assertNotIn("COLLECTION_TOOL_API_KEY=", content)

    def test_no_secrets_in_main(self):
        content = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertNotIn("Bearer ", content.replace("Bearer {api_key}", "").replace("Bearer {token}", ""))


class TestExistingRegressionsPreserved(Task007BTestBase):
    """11. Existing TASK-001 through TASK-007B.0 regressions remain PASS."""

    def test_nba_engine_unchanged_for_hero(self):
        contexts, calls = load_inputs(self.data)
        ctx = next(c for c in contexts if c["cif"] == "SYN002846")
        decision = decide(ctx, [c for c in calls.get("SYN002846", [])], DEFAULT_CONFIG)
        self.assertEqual(decision.selected_rule.rule_id, "NBA-300")
        self.assertEqual(decision.recommendation.treatment, "WAIT_SELF_CURE")

    def test_tool_registry_includes_all_seven_tools(self):
        from msb_tools.registry import TOOL_REGISTRY
        self.assertEqual(len(TOOL_REGISTRY), 8)
        self.assertIn("get_next_best_action", TOOL_REGISTRY)
        self.assertIn("simulate_decision", TOOL_REGISTRY)

    def test_existing_six_tools_unchanged(self):
        from msb_tools.registry import TOOL_REGISTRY
        expected = {"get_portfolio", "get_customer_360", "get_collection_history",
                    "get_cashflow_intelligence", "get_collection_policy", "get_recovery_opportunity"}
        self.assertTrue(expected.issubset(set(TOOL_REGISTRY)))

    def test_nba_decision_version_unchanged(self):
        from msb_nba.engine import DECISION_VERSION
        self.assertEqual(DECISION_VERSION, "TASK-007A-V1")


class TestRouterDeterminism(unittest.TestCase):
    """Router is deterministic and tightly constrained."""

    def test_infer_mode_explicit(self):
        self.assertEqual(infer_mode("anything", "PLAN"), "PLAN")
        self.assertEqual(infer_mode("anything", "EXPLAIN"), "EXPLAIN")
        self.assertEqual(infer_mode("anything", "INVESTIGATE"), "INVESTIGATE")
        self.assertEqual(infer_mode("anything", "SIMULATE"), "SIMULATE")

    def test_infer_mode_from_message(self):
        self.assertEqual(infer_mode("What should I do with SYN002846?"), "PLAN")
        self.assertEqual(infer_mode("Why was this decision made?"), "EXPLAIN")
        self.assertEqual(infer_mode("Tell me about SYN002846"), "INVESTIGATE")
        self.assertEqual(infer_mode("What if we change the route?"), "SIMULATE")

    def test_infer_mode_defaults_to_plan(self):
        self.assertEqual(infer_mode("SYN002846"), "PLAN")

    def test_extract_cif(self):
        self.assertEqual(extract_cif("What about SYN002846?"), "SYN002846")
        self.assertEqual(extract_cif("GOLDEN_G02 status"), "GOLDEN_G02")
        self.assertIsNone(extract_cif("no cif here"))
        self.assertIsNone(extract_cif(123))

    def test_parse_payload(self):
        mode, cif, msg, changes = parse_payload({"mode": "EXPLAIN", "cif": "SYN002846", "message": "why?"})
        self.assertEqual(mode, "EXPLAIN")
        self.assertEqual(cif, "SYN002846")
        mode, cif, msg, changes = parse_payload({"message": "What should I do with SYN002846?"})
        self.assertEqual(mode, "PLAN")
        self.assertEqual(cif, "SYN002846")


class TestAgentResponseContract(Task007BTestBase):
    """Response contract shape and invariants."""

    def test_response_shape(self):
        resp = self._invoke("PLAN", "SYN002846")
        d = resp.to_dict()
        self.assertIn("status", d)
        self.assertIn("mode", d)
        self.assertIn("cif", d)
        self.assertIn("decision", d)
        self.assertIn("evidence", d)
        self.assertIn("summary", d)
        self.assertIn("tools_used", d)
        self.assertIn("canonical_model", d)
        self.assertIn("synthetic_data", d)
        self.assertIn("agent_version", d)

    def test_synthetic_data_always_true(self):
        for mode in ("PLAN", "EXPLAIN", "INVESTIGATE"):
            with self.subTest(mode=mode):
                resp = self._invoke(mode, "SYN002846")
                self.assertTrue(resp.synthetic_data)

    def test_agent_version(self):
        resp = self._invoke("PLAN", "SYN002846")
        self.assertEqual(resp.agent_version, AGENT_VERSION)

    def test_decision_only_contains_accepted_fields(self):
        resp = self._invoke("PLAN", "SYN002846")
        keys = set(resp.decision.keys())
        expected = {"final_route", "treatment", "channel", "objective", "when", "rule_id", "reason_code"}
        self.assertEqual(keys, expected)


class TestToolServerGetNextBestAction(unittest.TestCase):
    """tool_server.py dispatches get_next_best_action."""

    def test_tool_server_supports_get_next_best_action(self):
        import threading
        from http.server import ThreadingHTTPServer
        from tool_server import ToolHandler
        old_key = os.environ.get("COLLECTION_TOOL_API_KEY")
        os.environ["COLLECTION_TOOL_API_KEY"] = "test-only-placeholder"
        server = ThreadingHTTPServer(("127.0.0.1", 0), ToolHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            import urllib.request, urllib.error
            req = urllib.request.Request(
                base + "/tools/get_next_best_action",
                data=json.dumps({"cif": "SYN002846"}).encode(),
                headers={"Content-Type": "Application/json", "Authorization": "Bearer test-only-placeholder"},
                method="POST")
            with urllib.request.urlopen(req) as response:
                body = json.load(response)
            self.assertTrue(body["ok"])
            self.assertEqual(body["data"]["treatment"], "WAIT_SELF_CURE")
            self.assertEqual(body["data"]["rule_id"], "NBA-300")
        finally:
            server.shutdown(); server.server_close()
            if old_key is None: os.environ.pop("COLLECTION_TOOL_API_KEY", None)
            else: os.environ["COLLECTION_TOOL_API_KEY"] = old_key


if __name__ == "__main__": unittest.main()
