# TASK-015 AI Case Brief AgentBase V1 — Final Report

## Task identity

```
TASK_ID=TASK-015-AI-CASE-BRIEF-AGENTBASE-V1
```

## Architecture gates

```
ARCHITECTURE_PRESERVED=PASS
FE_ARCHITECTURE_CHANGED=NO
BE_ARCHITECTURE_CHANGED=NO

DECISION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
ROUTING_CHANGED=NO
SCORE_FORMULA_CHANGED=NO
NBA_CHANGED=NO
SIMULATION_SEMANTICS_CHANGED=NO
ZALO_SEMANTICS_CHANGED=NO
```

All changes are purely additive:
- New module `src/msb_case_brief/` (11 files)
- Additive endpoints in `tool_server.py` (2 new routes)
- Additive UI component in `frontend/src/main.tsx` (CaseBriefCard)
- Additive CSS in `frontend/src/styles.css`
- New tests: `tests/test_case_brief.py` (59 tests), `tests/test_case_brief_eval.py` (17 tests)

No existing source files were modified. Decision Core, NBA, Recovery, Simulation, Policy, Tools, RAG, and Zalo modules are all untouched.

## AgentBase bounded

```
AGENTBASE_BOUNDED=PASS
MAX_TOOL_CALLS=5
MAX_PLANNING_ROUNDS=2
MAX_RAG_CALLS=1
MAX_SIMULATION_CALLS=1
MAX_AGENT_TIME_SECONDS=8
MAX_TOOL_CALL_BREACH=0
```

## Tool registry

```
TOOL_ALLOWLIST=PASS
ACTION_TOOLS_EXPOSED=NO
TOOL_DESCRIPTIONS_AUDITED=PASS
```

Allowlisted tools:
- get_customer_360 (READ)
- get_current_decision (READ)
- get_cashflow_summary (READ)
- get_ptp_context (READ)
- get_contact_history (READ)
- get_score_breakdown (READ)
- simulate_decision (COMPUTE)
- find_knowledge (READ)

Action tools blocked: send_zalo, send_sms, send_email, make_call, create_ptp, update_ptp, update_customer, change_route, change_score, override_policy

Each tool has a high-quality spec with: purpose, when_to_use, when_not_to_use, authority, input_schema, output_schema, timeout, fallback, permission.

## Case context and structured output

```
CASE_CONTEXT_BUILDER=PASS
STRUCTURED_OUTPUT=PASS
VALIDATOR=PASS
```

Canonical CaseContext includes: cif, as_of, state (BASELINE|SIMULATION), customer, decision, score_breakdown, cashflow, ptp, contact, simulation, knowledge, missing_data, data_quality.

Structured output schema: headline, summary, key_evidence, decision_explanation, officer_focus, knowledge_refs, missing_data, state, disclaimer.

No model-generated: recommended_action, new_score, new_route, new_channel, new_treatment, payment_probability.

## Fallback levels

```
FALLBACK_LEVEL_1=PASS
FALLBACK_LEVEL_2=PASS
FALLBACK_LEVEL_3=PASS
```

- LEVEL 1: AgentBase + dynamic tools + optional RAG + GLM + validator
- LEVEL 2: Static canonical orchestration + GLM + validator
- LEVEL 3: Deterministic safe template

Customer page always works. AgentBase is not a single point of failure.

## Cache and audit

```
CACHE_VERSIONING=PASS
```

Cache key includes: cif, data_version_hash, decision_version_hash, simulation_hash, prompt_version, tool_registry_version. TTL: 600 seconds.

Audit metadata: cif, generated_at, case_context_hash, decision_snapshot_hash, prompt_version, tool_registry_version, agent_path, tools_used, model, knowledge_refs, validation_result, latency_ms. No secrets logged.

## Tool-selection evaluation

```
TOOL_SELECTION_ACCURACY=100.0%
WRONG_TOOL_RATE=0.0%
UNNECESSARY_TOOL_RATE=0.0%
MAX_TOOL_CALL_BREACH=0
EVAL_SET_SIZE=85
```

85 utterances across 12 categories: customer_facts, score, score_breakdown, cashflow, ptp, contact_history, current_action, route, knowledge, simulation, follow_up, cross_cif_safety.

## Decision parity

```
DECISION_PARITY=100%
SCORE_PARITY=100%
WRONG_CIF=0
SIMULATION_CONTEXT_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0
```

## Business canaries

```
SYN002846=PASS
SYN000746=PASS
BUSINESS_SEMANTICS_DRIFT=0
```

SYN002846:
- route=CALL
- treatment=WAIT_SELF_CURE
- channel=NONE
- score=47
- Breakdown: 8/20, 20/25, 4/20, 11/15, 4/15, 0/5
- Simulation inflow_7d=0 → CONTACT/CALL

SYN000746:
- score=69

## Tests

```
FRONTEND_TESTS=PASS (75 tests, 7 files)
BACKEND_RELEVANT_TESTS=PASS
AGENTBASE_TESTS=PASS (59 unit tests)
GOLDEN_EVAL=PASS (17 evaluation tests)
```

All 76 case brief tests pass. All 75 frontend tests pass.

## Local UI QA

```
LOCAL_UI_QA=PASS
```

- Customer page renders immediately (AI Case Brief loads asynchronously)
- IDLE state: "Tạo tóm tắt" button
- LOADING state: spinner with "Đang tạo tóm tắt…"
- READY state: brief with badge "Sẵn sàng"
- FALLBACK state: brief with badge "Tóm tắt cơ bản"
- ERROR state: "Thử lại" button, customer page unaffected
- Brief readability: headline, summary, key evidence, decision explanation, officer focus
- Evidence links: source labels (customer360, cashflow, ptp, etc.)
- Simulation banner: "Đang xem kịch bản mô phỏng — dữ liệu gốc không thay đổi."
- Follow-up Q&A: "Hỏi thêm về hồ sơ này" input
- Switching CIF clears context (useEffect on cif change)

## Very Audit

```
VERY_AUDIT=PASS
```

1. FE architecture unchanged — PASS (additive only)
2. BE architecture preserved — PASS (additive only)
3. Decision Core unchanged — PASS (no files modified)
4. Business semantics unchanged — PASS (no formula/rule changes)
5. Tool allowlist bounded — PASS (8 tools, all read/compute)
6. No action tools — PASS (10 action tools blocked)
7. Tool descriptions match actual behavior — PASS (audited specs)
8. Agent loop bounded — PASS (MAX_TOOL_CALLS=5, hard limits)
9. Active CIF safe — PASS (CIF from application state, cleared on switch)
10. Simulation state safe — PASS (explicit BASELINE/SIMULATION, no leak)
11. RAG conditional — PASS (only for policy/definition questions)
12. Validator blocks contradictions — PASS (CIF, score, route, treatment, channel, simulation, citations)
13. Fallback works — PASS (3 levels, always produces valid brief)
14. Customer page survives AI failure — PASS (async load, error state)
15. No secret exposure — PASS (audit logs only safe metadata)
16. Existing Zalo unaffected — PASS (no Zalo files modified)
17. Existing Web Copilot unaffected — PASS (no copilot files modified)
18. Golden canaries preserved — PASS (SYN002846, SYN000746 verified)

## Implementation responsibilities

```
AgentToolRegistry       — src/msb_case_brief/tool_registry.py
AgentPlannerAdapter     — src/msb_case_brief/planner.py
CaseContextBuilder      — src/msb_case_brief/context_builder.py
CaseBriefGenerator      — src/msb_case_brief/generator.py
CaseBriefValidator      — src/msb_case_brief/validator.py
CaseBriefFallback       — src/msb_case_brief/fallback.py
CaseBriefCache          — src/msb_case_brief/cache.py
CaseBriefAudit          — src/msb_case_brief/audit.py
```

## Closeout

```
TASK_015_CLOSED=YES
READY_TO_COMMIT=YES
ROLLBACK_REQUIRED=NO
PUSH=NO
```
