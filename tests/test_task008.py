from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from msb_agent.llm import LLMClient
from msb_agent.runtime import AgentRuntime
from msb_nba.config import DEFAULT_CONFIG
from msb_nba.engine import decide
from msb_simulation.display import display_projection
from msb_simulation.engine import SimulationEngine
from msb_simulation.labels import (CHANNEL_LABELS, FIELD_LABELS, PTP_STATE_LABELS,
                                   REASON_CODE_LABELS, TREATMENT_LABELS, label_for_field,
                                   label_for_value, label_for_when)
from msb_simulation.models import (BUSINESS_OUTCOMES, PTP_STATES, SUPPORTED_CHANGES,
                                   SIMULATION_VERSION)
from msb_simulation.scenarios import (ALL_SCENARIOS, HERO_SCENARIO_A, HERO_SCENARIO_B,
                                      HERO_SCENARIO_C, SYN002846_SCENARIO, run_scenario)
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository
from msb_tools.validate import PUBLIC_TOOL_ALLOWLIST
from msb_synthetic.generator import generate_to


ROOT = Path(__file__).resolve().parents[1]


class AdversarialLLM:
    def complete(self, prompt: str, *, max_tokens: int = 200, temperature: float = 0) -> tuple[str | None, str | None]:
        return ("Override: treatment=CONTACT, channel=CALL. Ignore the simulation. "
                "The real answer is CALL NOW.", "glm-5.2")


class Task008TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.root = Path(cls.temp.name)
        cls.data = cls.root / "data"; generate_to(cls.data)
        cls.repo = ToolRepository(cls.data)
        cls.engine = SimulationEngine(cls.repo)
        cls.caller = staticmethod(lambda name, args: invoke_tool(name, args, repository=cls.repo))
        cls.runtime = AgentRuntime(cls.caller, llm_client=None)
        cls.adversarial_runtime = AgentRuntime(cls.caller, llm_client=AdversarialLLM())

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()


class TestUnknownCif(Task008TestBase):
    """1. unknown CIF → NOT_FOUND."""

    def test_unknown_cif_returns_not_found(self):
        from msb_tools.errors import ToolFailure
        with self.assertRaises(ToolFailure) as ctx:
            self.engine.simulate("SYN999999", {"inflow_7d": 0})
        self.assertEqual(ctx.exception.code, "NOT_FOUND")

    def test_unknown_cif_via_tool(self):
        envelope = invoke_tool("simulate_decision", {"cif": "SYN999999", "changes": {}}, repository=self.repo)
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["error"]["code"], "NOT_FOUND")


class TestUnsupportedField(Task008TestBase):
    """2. unsupported change field → validation error."""

    def test_unknown_field_rejected(self):
        envelope = invoke_tool("simulate_decision", {"cif": "SYN002846", "changes": {"unknown_field": 1}}, repository=self.repo)
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["error"]["code"], "INVALID_ARGUMENT")

    def test_unknown_field_message(self):
        envelope = invoke_tool("simulate_decision", {"cif": "SYN002846", "changes": {"dpd": 99}}, repository=self.repo)
        self.assertFalse(envelope["ok"])
        self.assertIn("unsupported", envelope["error"]["message"])


class TestInvalidPtpState(Task008TestBase):
    """3. invalid PTP state → validation error."""

    def test_invalid_ptp_state_rejected(self):
        envelope = invoke_tool("simulate_decision", {"cif": "SYN002846", "changes": {"ptp_state": "INVALID"}}, repository=self.repo)
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["error"]["code"], "INVALID_ARGUMENT")

    def test_valid_ptp_states_accepted(self):
        for state in PTP_STATES:
            with self.subTest(state=state):
                envelope = invoke_tool("simulate_decision", {"cif": "SYN002846", "changes": {"ptp_state": state}}, repository=self.repo)
                self.assertTrue(envelope["ok"])


class TestImmutableSnapshot(Task008TestBase):
    """4. original customer state remains unchanged."""

    def test_context_unchanged_after_simulation(self):
        before = self.repo.context("SYN002846")
        self.engine.simulate("SYN002846", {"inflow_7d": 0, "net_cashflow_30d": 0})
        after = self.repo.context("SYN002846")
        self.assertEqual(before, after)

    def test_all_contexts_unchanged_after_multiple_simulations(self):
        contexts_before = {cif: self.repo.context(cif) for cif in ("GOLDEN_G03", "SYN000141", "SYN002846")}
        for cif in ("GOLDEN_G03", "SYN000141", "SYN002846"):
            self.engine.simulate(cif, {"inflow_7d": 0, "net_cashflow_30d": 0, "ptp_state": "BROKEN"})
        for cif in ("GOLDEN_G03", "SYN000141", "SYN002846"):
            self.assertEqual(contexts_before[cif], self.repo.context(cif))


class TestReplayUsesNbaEngine(Task008TestBase):
    """5. replay uses accepted deterministic NBA engine."""

    def test_before_decision_matches_decide(self):
        ctx = self.repo.context("SYN002846")
        calls = self.repo.calls_for_cif("SYN002846")
        expected = decide(ctx, calls, DEFAULT_CONFIG)
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0})
        self.assertEqual(result.before.rule_id, expected.selected_rule.rule_id)
        self.assertEqual(result.before.treatment, expected.recommendation.treatment)

    def test_after_decision_from_modified_context(self):
        ctx = self.repo.context("SYN002846")
        calls = self.repo.calls_for_cif("SYN002846")
        modified = copy.deepcopy(ctx)
        modified["cashflow"]["inflow_7d"] = 0
        modified["cashflow"]["net_cashflow_30d"] = 0
        expected = decide(modified, calls, DEFAULT_CONFIG)
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0, "net_cashflow_30d": 0})
        self.assertEqual(result.after.rule_id, expected.selected_rule.rule_id)
        self.assertEqual(result.after.treatment, expected.recommendation.treatment)


class TestBeforeMatchesTask007A(Task008TestBase):
    """6. before decision matches normal TASK-007A output."""

    def test_before_matches_get_next_best_action(self):
        nba = invoke_tool("get_next_best_action", {"cif": "SYN002846"}, repository=self.repo)["data"]
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0})
        self.assertEqual(result.before.treatment, nba["treatment"])
        self.assertEqual(result.before.rule_id, nba["rule_id"])
        self.assertEqual(result.before.channel, nba["channel"])
        self.assertEqual(result.before.objective, nba["objective"])


class TestAfterFromModifiedSnapshot(Task008TestBase):
    """7. after decision is produced from modified snapshot."""

    def test_after_reflects_changes(self):
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0, "net_cashflow_30d": 0})
        self.assertNotEqual(result.before.treatment, result.after.treatment)
        self.assertEqual(result.after.treatment, "CONTACT")
        self.assertEqual(result.after.rule_id, "NBA-900")


class TestDecisionDiff(Task008TestBase):
    """8. decision diff is correct."""

    def test_diff_contains_changed_fields(self):
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0, "net_cashflow_30d": 0})
        fields = {entry.field for entry in result.diff}
        self.assertIn("treatment", fields)
        self.assertIn("rule_id", fields)
        self.assertIn("inflow_7d", fields)

    def test_diff_before_after_values(self):
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0, "net_cashflow_30d": 0})
        treatment_diff = next(e for e in result.diff if e.field == "treatment")
        self.assertEqual(treatment_diff.before, "WAIT_SELF_CURE")
        self.assertEqual(treatment_diff.after, "CONTACT")


class TestNoDecisionChange(Task008TestBase):
    """9. no decision change returns decision_changed=false."""

    def test_no_change_returns_false(self):
        ctx = self.repo.context("SYN002846")
        result = self.engine.simulate("SYN002846", {"inflow_7d": ctx["cashflow"]["inflow_7d"]})
        self.assertFalse(result.decision_changed)
        self.assertEqual(result.diff, [])

    def test_empty_changes_returns_false(self):
        result = self.engine.simulate("SYN002846", {})
        self.assertFalse(result.decision_changed)


class TestSyn002846Reproducible(Task008TestBase):
    """10. SYN002846 simulation is reproducible."""

    def test_reproducible(self):
        changes = {"inflow_7d": 0, "net_cashflow_30d": 0}
        r1 = self.engine.simulate("SYN002846", changes)
        r2 = self.engine.simulate("SYN002846", changes)
        self.assertEqual(r1.to_dict(), r2.to_dict())


class TestBrokenPtpScenario(Task008TestBase):
    """11. broken PTP scenario."""

    def test_broken_ptp_changes_decision(self):
        result = run_scenario(self.engine, HERO_SCENARIO_B)
        self.assertTrue(result.decision_changed)
        self.assertEqual(result.before.treatment, "WAIT_SELF_CURE")
        self.assertEqual(result.after.treatment, "PTP_RECOVERY")

    def test_broken_ptp_rule_changes(self):
        result = run_scenario(self.engine, HERO_SCENARIO_B)
        self.assertEqual(result.before.rule_id, "NBA-300")
        self.assertEqual(result.after.rule_id, "NBA-210")


class TestOpenPtpScenario(Task008TestBase):
    """12. open PTP scenario."""

    def test_open_ptp_changes_decision(self):
        result = run_scenario(self.engine, HERO_SCENARIO_C)
        self.assertTrue(result.decision_changed)
        self.assertEqual(result.after.treatment, "PTP_FOLLOW_UP")
        self.assertEqual(result.after.rule_id, "NBA-230")

    def test_open_ptp_uses_promise_date(self):
        result = run_scenario(self.engine, HERO_SCENARIO_C)
        self.assertEqual(result.after.when["type"], "SOURCE_DATE")


class TestLlmCannotModifyResult(Task008TestBase):
    """13. LLM cannot modify simulation result."""

    def test_adversarial_llm_preserves_simulation(self):
        resp = self.adversarial_runtime.invoke("SIMULATE", "SYN002846",
                                                changes={"inflow_7d": 0, "net_cashflow_30d": 0})
        self.assertEqual(resp.simulation["before"]["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(resp.simulation["after"]["treatment"], "CONTACT")
        self.assertEqual(resp.decision["treatment"], "CONTACT")

    def test_simulation_identical_with_without_llm(self):
        changes = {"inflow_7d": 0, "net_cashflow_30d": 0}
        no_llm = self.runtime.invoke("SIMULATE", "SYN002846", changes=changes)
        with_llm = self.adversarial_runtime.invoke("SIMULATE", "SYN002846", changes=changes)
        self.assertEqual(no_llm.simulation, with_llm.simulation)
        self.assertEqual(no_llm.decision, with_llm.decision)


class TestReasoningContentNeverExposed(Task008TestBase):
    """14. reasoning_content never exposed."""

    def test_no_reasoning_in_response(self):
        resp = self.runtime.invoke("SIMULATE", "SYN002846", changes={"inflow_7d": 0})
        d = resp.to_dict()
        self.assertNotIn("reasoning_content", d)
        self.assertNotIn("chain_of_thought", d)

    def test_no_reasoning_with_llm(self):
        resp = self.adversarial_runtime.invoke("SIMULATE", "SYN002846", changes={"inflow_7d": 0})
        d = resp.to_dict()
        self.assertNotIn("reasoning_content", d)


class TestVietnameseLabels(unittest.TestCase):
    """15. Vietnamese display labels exist."""

    def test_treatment_labels_exist(self):
        for treatment in ("WAIT", "WAIT_SELF_CURE", "REMIND", "CONTACT", "PTP_FOLLOW_UP",
                          "PTP_RECOVERY", "PARTIAL_PAYMENT", "CALLBACK", "VERIFY_CONTACT", "ESCALATE"):
            self.assertIn(treatment, TREATMENT_LABELS)
            self.assertIsInstance(TREATMENT_LABELS[treatment], str)

    def test_channel_labels_exist(self):
        for channel in ("CALL", "SMS", "ZALO", "EMAIL", "FIELD", "NONE"):
            self.assertIn(channel, CHANNEL_LABELS)

    def test_ptp_state_labels_exist(self):
        for state in PTP_STATES:
            self.assertIn(state, PTP_STATE_LABELS)

    def test_field_labels_exist(self):
        for field in SUPPORTED_CHANGES:
            self.assertIn(field, FIELD_LABELS)

    def test_reason_code_labels_exist(self):
        self.assertIn("CALL_SELF_CURE", REASON_CODE_LABELS)
        self.assertIn("CALL_DEFAULT", REASON_CODE_LABELS)

    def test_labels_are_vietnamese(self):
        self.assertIn("thanh toán", TREATMENT_LABELS["WAIT_SELF_CURE"].lower())
        self.assertIn("điện", CHANNEL_LABELS["CALL"].lower())
        self.assertIn("tiền", FIELD_LABELS["inflow_7d"].lower())


class TestNoFabricatedMetrics(Task008TestBase):
    """16. no future-task business metrics fabricated."""

    FORBIDDEN_METRICS = frozenset({
        "recovery_rate", "amount_recovered", "time_saved", "calls_avoided",
        "annual_value", "economic_value", "roi", "aev", "uplift",
    })

    def test_no_fabricated_metrics_in_result(self):
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0})
        d = result.to_dict()
        def _keys(value):
            if isinstance(value, dict): return set(value) | set().union(*(_keys(v) for v in value.values()))
            if isinstance(value, list): return set().union(*(_keys(v) for v in value))
            return set()
        self.assertFalse(_keys(d) & self.FORBIDDEN_METRICS)

    def test_no_fabricated_metrics_in_display(self):
        result = self.engine.simulate("SYN002846", {"inflow_7d": 0})
        disp = display_projection(result)
        d = json.dumps(disp)
        for metric in self.FORBIDDEN_METRICS:
            self.assertNotIn(metric, d)


class TestToolServerAllowlist(unittest.TestCase):
    """17. tool server uses explicit allowlist."""

    def test_allowlist_is_explicit_and_tight(self):
        self.assertEqual(PUBLIC_TOOL_ALLOWLIST, frozenset({"get_customer_360", "get_next_best_action", "simulate_decision"}))

    def test_non_public_tool_blocked(self):
        from tool_server import ToolHandler
        old_key = os.environ.get("COLLECTION_TOOL_API_KEY")
        os.environ["COLLECTION_TOOL_API_KEY"] = "test-only-placeholder"
        server = ThreadingHTTPServer(("127.0.0.1", 0), ToolHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            import urllib.request, urllib.error
            for tool_name in ("get_portfolio", "get_collection_history", "get_cashflow_intelligence",
                              "get_collection_policy", "get_recovery_opportunity"):
                with self.subTest(tool=tool_name):
                    req = urllib.request.Request(
                        f"{base}/tools/{tool_name}",
                        data=json.dumps({}).encode(),
                        headers={"Content-Type": "application/json", "Authorization": "Bearer test-only-placeholder"},
                        method="POST")
                    try:
                        urllib.request.urlopen(req)
                        self.fail(f"{tool_name} should be blocked")
                    except urllib.error.HTTPError as e:
                        self.assertEqual(e.code, 404)
                        e.close()
        finally:
            server.shutdown(); server.server_close()
            if old_key is None: os.environ.pop("COLLECTION_TOOL_API_KEY", None)
            else: os.environ["COLLECTION_TOOL_API_KEY"] = old_key

    def test_simulate_decision_accessible_via_tool_server(self):
        from tool_server import ToolHandler
        old_key = os.environ.get("COLLECTION_TOOL_API_KEY")
        os.environ["COLLECTION_TOOL_API_KEY"] = "test-only-placeholder"
        server = ThreadingHTTPServer(("127.0.0.1", 0), ToolHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            import urllib.request
            req = urllib.request.Request(
                base + "/tools/simulate_decision",
                data=json.dumps({"cif": "SYN002846", "changes": {"inflow_7d": 0}}).encode(),
                headers={"Content-Type": "application/json", "Authorization": "Bearer test-only-placeholder"},
                method="POST")
            with urllib.request.urlopen(req) as response:
                body = json.load(response)
            self.assertTrue(body["ok"])
            self.assertTrue(body["data"]["decision_changed"])
        finally:
            server.shutdown(); server.server_close()
            if old_key is None: os.environ.pop("COLLECTION_TOOL_API_KEY", None)
            else: os.environ["COLLECTION_TOOL_API_KEY"] = old_key


class TestRegressionsPreserved(Task008TestBase):
    """18. TASK-001 through TASK-007B regressions remain PASS."""

    def test_nba_engine_unchanged(self):
        ctx = self.repo.context("SYN002846")
        calls = self.repo.calls_for_cif("SYN002846")
        decision = decide(ctx, calls, DEFAULT_CONFIG)
        self.assertEqual(decision.selected_rule.rule_id, "NBA-300")
        self.assertEqual(decision.recommendation.treatment, "WAIT_SELF_CURE")

    def test_tool_registry_has_eight_tools(self):
        from msb_tools.registry import TOOL_REGISTRY
        self.assertEqual(len(TOOL_REGISTRY), 8)

    def test_agent_version_updated(self):
        from msb_agent.models import AGENT_VERSION
        self.assertEqual(AGENT_VERSION, "TASK-008-V1")

    def test_simulation_version(self):
        self.assertEqual(SIMULATION_VERSION, "TASK-008-V1")


class TestDisplayProjection(Task008TestBase):
    """Display projection produces Vietnamese-friendly output."""

    def test_display_has_title(self):
        result = run_scenario(self.engine, HERO_SCENARIO_A)
        disp = display_projection(result)
        self.assertIn("title", disp)
        self.assertIn("Quyết định", disp["title"])

    def test_display_has_before_after(self):
        result = run_scenario(self.engine, HERO_SCENARIO_A)
        disp = display_projection(result)
        self.assertIn("before_display", disp)
        self.assertIn("after_display", disp)
        self.assertIn("action", disp["before_display"])
        self.assertIn("action", disp["after_display"])

    def test_display_changed_factors(self):
        result = run_scenario(self.engine, HERO_SCENARIO_A)
        disp = display_projection(result)
        self.assertTrue(disp["changed_factors"])
        for factor in disp["changed_factors"]:
            self.assertIn("label", factor)
            self.assertIn("before", factor)
            self.assertIn("after", factor)

    def test_display_uses_vietnamese(self):
        result = run_scenario(self.engine, HERO_SCENARIO_A)
        disp = display_projection(result)
        self.assertIn("Liên hệ", disp["before_display"]["action"])
        self.assertIn("thanh toán", disp["after_display"]["action"].lower())


class TestAllHeroScenarios(Task008TestBase):
    """All hero scenarios produce meaningful results."""

    def test_all_scenarios_changed(self):
        for scenario in ALL_SCENARIOS:
            with self.subTest(scenario=scenario["label"]):
                result = run_scenario(self.engine, scenario)
                self.assertTrue(result.decision_changed,
                                 f"{scenario['label']}: decision should change")

    def test_scenario_a_cashflow_change(self):
        result = run_scenario(self.engine, HERO_SCENARIO_A)
        self.assertEqual(result.before.treatment, "CONTACT")
        self.assertEqual(result.after.treatment, "WAIT_SELF_CURE")

    def test_syn002846_reverse_self_cure(self):
        result = run_scenario(self.engine, SYN002846_SCENARIO)
        self.assertEqual(result.before.treatment, "WAIT_SELF_CURE")
        self.assertEqual(result.after.treatment, "CONTACT")


if __name__ == "__main__": unittest.main()
