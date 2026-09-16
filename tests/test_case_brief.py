"""TASK-015 AI Case Brief — unit tests for all components."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from msb_synthetic.generator import generate_to
from msb_tools.registry import invoke_tool
from msb_tools.repository import ToolRepository

from msb_case_brief.models import (
    TOOL_ALLOWLIST, ACTION_TOOLS, MAX_TOOL_CALLS, MAX_PLANNING_ROUNDS,
    MAX_RAG_CALLS, MAX_SIMULATION_CALLS, MAX_AGENT_TIME_SECONDS,
    PROMPT_VERSION, TOOL_REGISTRY_VERSION, CANONICAL_MODEL, DISCLAIMER,
    CaseBrief, CaseContext, KeyEvidence, KnowledgeRef, ValidationResult,
)
from msb_case_brief.tool_descriptions import TOOL_SPECS, tool_description_for_planner, registry_description
from msb_case_brief.tool_registry import AgentToolRegistry
from msb_case_brief.planner import AgentPlannerAdapter
from msb_case_brief.context_builder import CaseContextBuilder
from msb_case_brief.validator import CaseBriefValidator
from msb_case_brief.fallback import CaseBriefFallback
from msb_case_brief.cache import CaseBriefCache
from msb_case_brief.audit import CaseBriefAudit
from msb_case_brief.generator import CaseBriefGenerator
from msb_case_brief.service import CaseBriefService


def _tool_caller(repository: ToolRepository):
    def caller(name: str, args: dict[str, Any]) -> dict[str, Any]:
        return invoke_tool(name, args, repository=repository)
    return caller


class ToolRegistryTest(unittest.TestCase):
    def test_allowlist_exact(self):
        expected = frozenset({
            "get_customer_360", "get_current_decision", "get_cashflow_summary",
            "get_ptp_context", "get_contact_history", "get_score_breakdown",
            "simulate_decision", "find_knowledge",
        })
        self.assertEqual(TOOL_ALLOWLIST, expected)

    def test_action_tools_not_in_allowlist(self):
        self.assertEqual(TOOL_ALLOWLIST & ACTION_TOOLS, frozenset())

    def test_action_tools_defined(self):
        self.assertIn("send_zalo", ACTION_TOOLS)
        self.assertIn("create_ptp", ACTION_TOOLS)
        self.assertIn("change_route", ACTION_TOOLS)

    def test_registry_rejects_action_tools(self):
        registry = AgentToolRegistry(lambda name, args: {"ok": True, "data": {}})
        for tool in ACTION_TOOLS:
            result = registry.invoke(tool, {"cif": "SYN002846"})
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "ACTION_TOOL_BLOCKED")

    def test_registry_rejects_unknown_tools(self):
        registry = AgentToolRegistry(lambda name, args: {"ok": True, "data": {}})
        result = registry.invoke("unknown_tool", {"cif": "SYN002846"})
        self.assertFalse(result["ok"])

    def test_registry_is_allowed(self):
        registry = AgentToolRegistry(lambda name, args: {"ok": True, "data": {}})
        for tool in TOOL_ALLOWLIST:
            self.assertTrue(registry.is_allowed(tool))
        self.assertFalse(registry.is_allowed("send_zalo"))


class ToolDescriptionsTest(unittest.TestCase):
    def test_all_tools_have_specs(self):
        for name in TOOL_ALLOWLIST:
            self.assertIn(name, TOOL_SPECS, f"Missing spec for {name}")

    def test_specs_have_required_fields(self):
        for name, spec in TOOL_SPECS.items():
            self.assertTrue(spec.purpose, f"{name} missing purpose")
            self.assertTrue(spec.when_to_use, f"{name} missing when_to_use")
            self.assertTrue(spec.when_not_to_use, f"{name} missing when_not_to_use")
            self.assertTrue(spec.authority, f"{name} missing authority")
            self.assertTrue(spec.input_schema, f"{name} missing input_schema")
            self.assertTrue(spec.output_schema, f"{name} missing output_schema")
            self.assertGreater(spec.timeout_ms, 0, f"{name} missing timeout")
            self.assertTrue(spec.fallback, f"{name} missing fallback")
            self.assertIn(spec.permission, ("READ", "COMPUTE"))

    def test_simulate_is_compute(self):
        self.assertEqual(TOOL_SPECS["simulate_decision"].permission, "COMPUTE")

    def test_find_knowledge_is_read(self):
        self.assertEqual(TOOL_SPECS["find_knowledge"].permission, "READ")

    def test_planner_description_not_empty(self):
        desc = tool_description_for_planner("get_current_decision")
        self.assertIn("Authoritative", desc)
        self.assertIn("Purpose:", desc)

    def test_registry_description_covers_all(self):
        desc = registry_description()
        for name in TOOL_ALLOWLIST:
            self.assertIn(name, desc)


class BoundedPlannerTest(unittest.TestCase):
    def setUp(self):
        self.registry = AgentToolRegistry(lambda name, args: {"ok": True, "data": {}})
        self.planner = AgentPlannerAdapter(self.registry)

    def test_initial_brief_always_has_decision(self):
        tools = self.planner.plan_initial_brief("SYN002846")
        self.assertIn("get_current_decision", tools)

    def test_initial_brief_respects_max_tool_calls(self):
        tools = self.planner.plan_initial_brief("SYN002846")
        self.assertLessEqual(len(tools), MAX_TOOL_CALLS)

    def test_followup_respects_max_tool_calls(self):
        questions = [
            "Tại sao chưa gọi?", "Dòng tiền gần đây?", "PTP thế nào?",
            "Lịch sử liên hệ?", "Vì sao điểm 47?", "Nếu tiền vào bằng 0 thì sao?",
            "CALL khác CBS thế nào?", "Tóm tắt hồ sơ",
        ]
        for q in questions:
            tools = self.planner.plan_followup("SYN002846", q)
            self.assertLessEqual(len(tools), MAX_TOOL_CALLS, f"Too many tools for: {q}")

    def test_knowledge_question_selects_find_knowledge(self):
        tools = self.planner.plan_followup("SYN002846", "CALL khác CBS thế nào?")
        self.assertIn("find_knowledge", tools)

    def test_simulation_question_selects_simulate(self):
        tools = self.planner.plan_followup("SYN002846", "Nếu tiền vào 7 ngày bằng 0 thì sao?")
        self.assertIn("simulate_decision", tools)
        self.assertIn("get_current_decision", tools)

    def test_ptp_question_selects_ptp_context(self):
        tools = self.planner.plan_followup("SYN002846", "PTP thế nào?")
        self.assertIn("get_ptp_context", tools)

    def test_cashflow_question_selects_cashflow_summary(self):
        tools = self.planner.plan_followup("SYN002846", "Dòng tiền gần đây thế nào?")
        self.assertIn("get_cashflow_summary", tools)

    def test_contact_question_selects_contact_history(self):
        tools = self.planner.plan_followup("SYN002846", "Đã liên hệ chưa?")
        self.assertIn("get_contact_history", tools)

    def test_score_question_selects_score_breakdown(self):
        tools = self.planner.plan_followup("SYN002846", "Vì sao điểm là 47?")
        self.assertIn("get_score_breakdown", tools)

    def test_decision_question_selects_current_decision(self):
        tools = self.planner.plan_followup("SYN002846", "Tại sao chưa cần gọi?")
        self.assertIn("get_current_decision", tools)

    def test_no_action_tools_selected(self):
        questions = ["Tại sao chưa gọi?", "PTP thế nào?", "Nếu tiền vào bằng 0?"]
        for q in questions:
            tools = self.planner.plan_followup("SYN002846", q)
            for tool in tools:
                self.assertNotIn(tool, ACTION_TOOLS)

    def test_max_rag_calls_respected(self):
        tools = self.planner.plan_followup("SYN002846", "CALL khác CBS thế nào?")
        rag_count = sum(1 for t in tools if t == "find_knowledge")
        self.assertLessEqual(rag_count, MAX_RAG_CALLS)

    def test_max_simulation_calls_respected(self):
        tools = self.planner.plan_followup("SYN002846", "Nếu tiền vào bằng 0?")
        sim_count = sum(1 for t in tools if t == "simulate_decision")
        self.assertLessEqual(sim_count, MAX_SIMULATION_CALLS)

    def test_is_bounded(self):
        tools = self.planner.plan_initial_brief("SYN002846")
        self.assertTrue(self.planner.is_bounded(tools))


class CaseContextBuilderTest(unittest.TestCase):
    def setUp(self):
        self.builder = CaseContextBuilder()

    def test_build_with_all_data(self):
        ctx = self.builder.build(
            cif="SYN002846",
            customer_360={"customer": {"customer_name": "Test", "segment": "A"},
                          "debt": {"max_dpd_cif": 5, "total_outstanding_cif": 100000000, "loan_count": 2}},
            decision={"final_route": "CALL", "treatment": "WAIT_SELF_CURE", "channel": "NONE",
                      "recovery_opportunity_score": 47},
            cashflow={"inflow_7d": 30000000, "net_cashflow_30d": 50000000},
            ptp={"status": "NONE"},
            contact={"outbound_attempts_30d": 0},
            score_breakdown={"recovery_opportunity_score": 47},
        )
        self.assertEqual(ctx.cif, "SYN002846")
        self.assertEqual(ctx.state, "BASELINE")
        self.assertEqual(ctx.decision["treatment"], "WAIT_SELF_CURE")
        self.assertEqual(ctx.customer["max_dpd_cif"], 5)
        self.assertEqual(ctx.cashflow["inflow_7d"], 30000000)

    def test_build_with_missing_data(self):
        ctx = self.builder.build(cif="SYN002846")
        self.assertIn("customer_360", ctx.missing_data)
        self.assertIn("decision", ctx.missing_data)
        self.assertIn("cashflow", ctx.missing_data)

    def test_build_simulation_state(self):
        ctx = self.builder.build(cif="SYN002846", state="SIMULATION",
                                  simulation={"before": {}, "after": {}, "decision_changed": True})
        self.assertEqual(ctx.state, "SIMULATION")
        self.assertIsNotNone(ctx.simulation)

    def test_no_hardcoded_cif(self):
        ctx = self.builder.build(cif="SYN000746")
        self.assertEqual(ctx.cif, "SYN000746")

    def test_hash_stable(self):
        ctx1 = self.builder.build(cif="SYN002846", decision={"treatment": "WAIT"})
        ctx2 = self.builder.build(cif="SYN002846", decision={"treatment": "WAIT"})
        self.assertEqual(ctx1.hash(), ctx2.hash())


class ValidatorTest(unittest.TestCase):
    def setUp(self):
        self.validator = CaseBriefValidator()
        self.builder = CaseContextBuilder()

    def _make_context(self, cif="SYN002846", treatment="WAIT_SELF_CURE", route="CALL",
                      channel="NONE", score=47, state="BASELINE"):
        return self.builder.build(
            cif=cif,
            decision={"final_route": route, "treatment": treatment, "channel": channel,
                      "recovery_opportunity_score": score},
            state=state,
        )

    def _make_brief(self, headline="", summary="", evidence=None, state="BASELINE"):
        return CaseBrief(
            headline=headline or f"Hồ sơ SYN002846",
            summary=summary or "Đề xuất: Chờ tự thanh toán.",
            key_evidence=evidence or [],
            decision_explanation=[],
            officer_focus=[],
            knowledge_refs=[],
            missing_data=[],
            state=state,
            disclaimer=DISCLAIMER,
        )

    def test_valid_brief_passes(self):
        ctx = self._make_context()
        brief = self._make_brief()
        result = self.validator.validate(brief, ctx)
        self.assertTrue(result.passed, result.reasons)

    def test_wrong_cif_rejected(self):
        ctx = self._make_context(cif="SYN002846")
        brief = self._make_brief(headline="Hồ sơ SYN000746: Chờ")
        result = self.validator.validate(brief, ctx)
        self.assertFalse(result.passed)
        self.assertTrue(any("wrong_cif" in r for r in result.reasons))

    def test_treatment_parity_violation(self):
        ctx = self._make_context(treatment="CONTACT")
        brief = self._make_brief(summary="Chưa cần liên hệ.")
        result = self.validator.validate(brief, ctx)
        self.assertFalse(result.passed)

    def test_simulation_context_leak_rejected(self):
        ctx = self._make_context(state="BASELINE")
        brief = self._make_brief(state="SIMULATION")
        result = self.validator.validate(brief, ctx)
        self.assertFalse(result.passed)
        self.assertTrue(any("simulation_context_leak" in r for r in result.reasons))

    def test_invalid_citation_rejected(self):
        ctx = self._make_context()
        brief = self._make_brief(evidence=[KeyEvidence("test", "val1", "reason", "invalid_source")])
        result = self.validator.validate(brief, ctx)
        self.assertFalse(result.passed)
        self.assertTrue(any("citation" in r for r in result.reasons))

    def test_forbidden_claim_rejected(self):
        ctx = self._make_context()
        brief = self._make_brief(summary="Nên chuyển tuyến CBS.")
        result = self.validator.validate(brief, ctx)
        self.assertFalse(result.passed)
        self.assertTrue(any("unsupported" in r for r in result.reasons))

    def test_parsed_json_valid(self):
        ctx = self._make_context()
        parsed = {
            "headline": "Hồ sơ SYN002846",
            "summary": "Đề xuất: Chờ tự thanh toán.",
            "key_evidence": [{"label": "DPD", "value": "5", "reason": "test", "source": "customer360"}],
            "decision_explanation": ["Có dòng tiền vào."],
            "officer_focus": ["Theo dõi dòng tiền."],
            "knowledge_refs": [],
            "missing_data": [],
            "state": "BASELINE",
            "disclaimer": DISCLAIMER,
        }
        brief = self.validator.validate_parsed_json(parsed, ctx)
        self.assertIsNotNone(brief)


class FallbackTest(unittest.TestCase):
    def setUp(self):
        self.fallback = CaseBriefFallback()
        self.builder = CaseContextBuilder()

    def test_generates_valid_brief(self):
        ctx = self.builder.build(
            cif="SYN002846",
            customer_360={"debt": {"max_dpd_cif": 5, "total_outstanding_cif": 100000000, "loan_count": 2}},
            decision={"final_route": "CALL", "treatment": "WAIT_SELF_CURE", "channel": "NONE",
                      "recovery_opportunity_score": 47},
            cashflow={"inflow_7d": 30000000, "net_cashflow_30d": 50000000},
            ptp={"status": "NONE"},
        )
        brief = self.fallback.generate(ctx)
        self.assertTrue(brief.headline)
        self.assertTrue(brief.summary)
        self.assertEqual(brief.state, "BASELINE")
        self.assertEqual(brief.disclaimer, DISCLAIMER)

    def test_no_business_decision_created(self):
        ctx = self.builder.build(cif="SYN002846")
        brief = self.fallback.generate(ctx)
        text = brief.headline + brief.summary
        self.assertNotIn("nên chuyển", text.lower())
        self.assertNotIn("payment probability", text.lower())


class CacheTest(unittest.TestCase):
    def setUp(self):
        self.cache = CaseBriefCache(ttl_seconds=60)

    def test_put_and_get(self):
        data = {"status": "success", "cif": "SYN002846"}
        self.cache.put("SYN002846", "ctx1", "dec1", "sim1", data)
        result = self.cache.get("SYN002846", "ctx1", "dec1", "sim1")
        self.assertEqual(result, data)

    def test_different_context_different_key(self):
        data1 = {"status": "success", "cif": "SYN002846", "v": 1}
        data2 = {"status": "success", "cif": "SYN002846", "v": 2}
        self.cache.put("SYN002846", "ctx1", "dec1", "sim1", data1)
        self.cache.put("SYN002846", "ctx2", "dec1", "sim1", data2)
        self.assertEqual(self.cache.get("SYN002846", "ctx1", "dec1", "sim1"), data1)
        self.assertEqual(self.cache.get("SYN002846", "ctx2", "dec1", "sim1"), data2)

    def test_different_cif_different_key(self):
        data1 = {"status": "success", "cif": "SYN002846"}
        data2 = {"status": "success", "cif": "SYN000746"}
        self.cache.put("SYN002846", "ctx", "dec", "sim", data1)
        self.cache.put("SYN000746", "ctx", "dec", "sim", data2)
        self.assertEqual(self.cache.get("SYN002846", "ctx", "dec", "sim"), data1)
        self.assertEqual(self.cache.get("SYN000746", "ctx", "dec", "sim"), data2)

    def test_ttl_expiry(self):
        cache = CaseBriefCache(ttl_seconds=0)
        cache.put("SYN002846", "ctx", "dec", "sim", {"v": 1})
        import time; time.sleep(0.01)
        self.assertIsNone(cache.get("SYN002846", "ctx", "dec", "sim"))

    def test_invalidate(self):
        self.cache.put("SYN002846", "ctx", "dec", "sim", {"cif": "SYN002846"})
        self.cache.invalidate("SYN002846")
        self.assertIsNone(self.cache.get("SYN002846", "ctx", "dec", "sim"))


class AuditTest(unittest.TestCase):
    def test_build_audit(self):
        audit = CaseBriefAudit()
        meta = audit.build(
            cif="SYN002846",
            context_hash="abc",
            decision_snapshot_hash="def",
            agent_path="AGENTBASE",
            tools_used=["get_current_decision"],
            model="glm-5.2",
            knowledge_refs=[],
            validation=ValidationResult(passed=True),
            latency_ms=123.45,
        )
        self.assertEqual(meta.cif, "SYN002846")
        self.assertEqual(meta.agent_path, "AGENTBASE")
        self.assertEqual(meta.validation_result, "PASS")
        self.assertEqual(meta.prompt_version, PROMPT_VERSION)

    def test_safe_log_no_secrets(self):
        audit = CaseBriefAudit()
        meta = audit.build(
            cif="SYN002846", context_hash="x", decision_snapshot_hash="y",
            agent_path="DETERMINISTIC", tools_used=[], model="deterministic",
            knowledge_refs=[], validation=ValidationResult(passed=False, reasons=["test"]),
            latency_ms=50.0,
        )
        safe = audit.to_safe_log(meta)
        self.assertNotIn("api_key", safe)
        self.assertNotIn("password", safe)


class GeneratorIntegrationTest(unittest.TestCase):
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

    def _make_generator(self, llm_complete=None, knowledge_answer=None):
        caller = _tool_caller(self.repo)
        return CaseBriefGenerator(tool_caller=caller, llm_complete=llm_complete,
                                  knowledge_answer=knowledge_answer)

    def test_level3_deterministic_fallback(self):
        gen = self._make_generator(llm_complete=None)
        result = gen.generate_brief("SYN002846")
        self.assertEqual(result.agent_path, "DETERMINISTIC")
        self.assertTrue(result.brief.headline)
        self.assertTrue(result.validation.passed, result.validation.reasons)

    def test_level3_for_syn000746(self):
        gen = self._make_generator(llm_complete=None)
        result = gen.generate_brief("SYN000746")
        self.assertEqual(result.agent_path, "DETERMINISTIC")
        self.assertTrue(result.brief.headline)

    def test_cache_hit(self):
        gen = self._make_generator(llm_complete=None)
        result1 = gen.generate_brief("SYN002846")
        result2 = gen.generate_brief("SYN002846")
        self.assertTrue(result2.cache_hit)

    def test_followup_question(self):
        gen = self._make_generator(llm_complete=None)
        result = gen.answer_question("SYN002846", "Tại sao chưa cần gọi?")
        self.assertTrue(result.brief.headline)
        self.assertLessEqual(len(result.tools_used), MAX_TOOL_CALLS)

    def test_simulation_changes(self):
        gen = self._make_generator(llm_complete=None)
        result = gen.generate_brief("SYN002846", simulation_changes={"inflow_7d": 0})
        self.assertEqual(result.brief.state, "SIMULATION")

    def test_no_action_tools_used(self):
        gen = self._make_generator(llm_complete=None)
        result = gen.generate_brief("SYN002846")
        for tool in result.tools_used:
            self.assertNotIn(tool, ACTION_TOOLS)

    def test_audit_metadata_complete(self):
        gen = self._make_generator(llm_complete=None)
        result = gen.generate_brief("SYN002846")
        audit = result.audit
        self.assertEqual(audit.cif, "SYN002846")
        self.assertTrue(audit.generated_at)
        self.assertTrue(audit.case_context_hash)
        self.assertEqual(audit.prompt_version, PROMPT_VERSION)
        self.assertEqual(audit.tool_registry_version, TOOL_REGISTRY_VERSION)

    def test_cif_isolation(self):
        gen = self._make_generator(llm_complete=None)
        r1 = gen.generate_brief("SYN002846")
        r2 = gen.generate_brief("SYN000746")
        self.assertEqual(r1.audit.cif, "SYN002846")
        self.assertEqual(r2.audit.cif, "SYN000746")
        self.assertNotIn("SYN000746", r1.brief.headline)
        self.assertNotIn("SYN002846", r2.brief.headline)

    def test_simulation_isolation(self):
        gen = self._make_generator(llm_complete=None)
        baseline = gen.generate_brief("SYN002846")
        sim = gen.generate_brief("SYN002846",
                                 simulation_changes={"inflow_7d": 0})
        self.assertEqual(baseline.brief.state, "BASELINE")
        self.assertEqual(sim.brief.state, "SIMULATION")


class ServiceIntegrationTest(unittest.TestCase):
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

    def test_service_generate_brief(self):
        caller = _tool_caller(self.repo)
        service = CaseBriefService(tool_caller=caller)
        result = service.generate_brief("SYN002846")
        self.assertTrue(result.brief.headline)

    def test_service_answer_question(self):
        caller = _tool_caller(self.repo)
        service = CaseBriefService(tool_caller=caller)
        result = service.answer_question("SYN002846", "Dòng tiền gần đây?")
        self.assertTrue(result.brief.headline)

    def test_service_invalidate_cache(self):
        caller = _tool_caller(self.repo)
        service = CaseBriefService(tool_caller=caller)
        service.generate_brief("SYN002846")
        service.invalidate_cache("SYN002846")
