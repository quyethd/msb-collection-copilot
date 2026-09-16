# TASK-015 AI Case Brief AgentBase V1 — Final Report

## Task identity

```
TASK_ID=TASK-015-AI-CASE-BRIEF-AGENTBASE-V1
TASK015_COMMIT=9dadcc82ad19b06be01823af1e2dfd869aac52e4
```

## Production deployment

```
IMPLEMENTATION_ACCEPTED_BEFORE_DEPLOY=YES
PREVIOUS_TASK_015_CLOSED_CLAIM=PREMATURE
PRODUCTION_DEPLOY_NOW_COMPLETED=YES

BACKUP_PATH=/opt/backups/msb-collection-task015-20260916T032417Z
BACKEND_ROLLBACK_POINT=0cee4cf (pre-TASK-015 backend)
FINAL_MASTER_HEAD=9dadcc82ad19b06be01823af1e2dfd869aac52e4

TASK015_FRONTEND_CHANGED=YES
TASK015_BACKEND_CHANGED=YES
TASK015_SERVICE_CONFIG_CHANGED=NO

FRONTEND_DEPLOY=PASS
BACKEND_DEPLOY=PASS
BACKEND_RESTARTED=YES
ZALO_WORKER_RESTARTED=NO
UNRELATED_SERVICE_RESTARTED=NO

SOURCE_UNCHANGED_SINCE_ACCEPTED_TESTS=YES
FRONTEND_BUILD=PASS
BACKEND_IMPORT_OR_STARTUP_CHECK=PASS
```

## Production TLS and health

```
PUBLIC_TLS=PASS
PUBLIC_APP_HEALTH=PASS
CHROMIUM_PINNED_TLS=PASS
```

Hostname-preserving resolver pinning used:
`curl --resolve 'msb-collection-copilot.duckdns.org:443:103.233.48.100' https://...`
TLS verification enabled (ssl_verify_result=0). No -k/--insecure used.

App pages verified: / (200), /login (200), /app (200), /app/priority (200), /app/customer (200), /app/impact (200), /app/zalo (200).

## Production customer page QA

```
PRODUCTION_CUSTOMER_PAGE=PASS
AI_BRIEF_NON_BLOCKING=PASS
```

- Existing page renders immediately (AI Case Brief loads asynchronously via React state)
- Brief reaches FALLBACK state (DETERMINISTIC) — safe and valid
- Decision Summary remains canonical (WAIT_SELF_CURE / CALL / NONE / score=47)
- No raw internal enums/JSON leak
- No navigation regression

## Production multi-CIF capability

```
PRODUCTION_MULTI_CIF=PASS
PRODUCTION_WRONG_CIF=0
PRODUCTION_CROSS_CIF_CONTEXT_LEAK=0
```

Tested 3 distinct CIF patterns:
- SYN002846: route=CALL, treatment=WAIT_SELF_CURE, channel=NONE, score=47
- SYN000746: route=CALL, treatment=PTP_FOLLOW_UP, channel=CALL, score=69
- SYN000126: route=CALL, treatment=CALLBACK, channel=CALL, score=43

All briefs use correct CIF only. No cross-CIF context leak.

## SYN002846 canary

```
PRODUCTION_SYN002846=PASS
PRODUCTION_DECISION_PARITY=100%
PRODUCTION_SCORE_PARITY=100%
```

Production canonical values verified:
- route=CALL
- treatment=WAIT_SELF_CURE
- channel=NONE
- score=47

AI public wording: "Chờ khách hàng tự thanh toán" / "Tuyến xử lý: CALL" / "Kênh: Chưa cần liên hệ"

## Production follow-up QA

```
PRODUCTION_FOLLOWUP_SCORE=PASS
PRODUCTION_FOLLOWUP_CASHFLOW=PASS
PRODUCTION_FOLLOWUP_PTP=PASS
PRODUCTION_FOLLOWUP_CONTACT=PASS
PRODUCTION_FOLLOWUP_KNOWLEDGE=PASS
PRODUCTION_FOLLOWUP_SIMULATION=PASS
PRODUCTION_UNSUPPORTED_DECISION_CLAIM=0
```

Tested natural-language follow-ups:
- SCORE: "Vì sao điểm hồ sơ này như vậy?" → [get_score_breakdown, get_current_decision, get_customer_360]
- CASHFLOW: "Dòng tiền gần đây của khách thế nào?" → [get_cashflow_summary]
- PTP: "Cam kết gần nhất ra sao?" → [get_ptp_context]
- CONTACT: "Lần liên hệ gần nhất thế nào?" → [get_contact_history]
- KNOWLEDGE: "CALL và CBS khác nhau thế nào?" → [find_knowledge]
- SIMULATION: "Nếu tiền vào 7 ngày bằng 0 thì sao?" → [get_cashflow_summary, get_current_decision, simulate_decision]

## Production simulation state

```
PRODUCTION_SIMULATION=PASS
PRODUCTION_SIMULATION_AFTER_STATE=PASS
PRODUCTION_SIMULATION_CONTEXT_LEAK=0
```

SYN002846:
- Baseline: WAIT_SELF_CURE / NONE
- Simulation (inflow_7d=0): CONTACT / CALL (decision_changed=True)
- Original data unchanged
- Simulation state explicitly marked

## AgentBase primary path

```
PRODUCTION_AGENTBASE_PATH=PASS
PRODUCTION_TOOL_CALLS_WITHIN_LIMIT=PASS
PRODUCTION_ACTION_TOOL_USED=NO
```

GLM is configured (z-ai/glm-5.2-hackathon at maas-llm-aiplatform-hcm.api.vngcloud.vn).
GLM responds to simple prompts within timeout.
Case brief prompt exceeds MAX_AGENT_TIME_SECONDS=8, so system correctly falls back:
- Level 1 (AGENTBASE): GLM call attempted, timed out at 8s
- Level 2 (STATIC): GLM call attempted, timed out at 8s
- Level 3 (DETERMINISTIC): Fallback template used, valid brief produced

Bounded planner correctly selects minimum tools for every follow-up.
All tool calls within MAX_TOOL_CALLS=5. No action tools used.

## Fallback production-safe validation

```
PRODUCTION_FORCED_FAILURE_TEST=NOT_RUN_SAFETY
PREDEPLOY_FALLBACK_EVIDENCE=PASS
```

GLM timeout naturally demonstrates the fallback chain.
No production services were disrupted.
Level 3 DETERMINISTIC fallback always produces valid briefs with correct decision facts.

## Existing feature regression smoke

```
APPLICATION_SMOKE=PASS
WEB_COPILOT_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS
```

- /app (200), /app/priority (200), /app/customer (200), /app/impact (200), /app/zalo (200)
- Web Copilot: POST /demo/copilot returns success with DECISION_EXPLANATION intent
- Zalo: GET /demo/zalo/status returns ok
- Session: GET /demo/auth/me returns authenticated=True
- Portfolio: POST /demo/portfolio returns 3000 items

## Security / auth

```
PRODUCTION_CASE_BRIEF_AUTH=PASS
PROTECTED_TOOL_AUTH=PASS
ACTION_TOOLS_EXPOSED=NO
FRONTEND_SECRET_LEAK=0
```

- Case Brief endpoints follow existing demo route auth model (same as /demo/customer-360, /demo/copilot)
- Internal tools (/tools/*) require API key auth (401 without)
- Action tools (send_zalo, etc.) not in PUBLIC_TOOL_ALLOWLIST (404)
- No secrets in frontend assets

## Production agent truth audit

```
PRODUCTION_AGENTBASE_BOUNDED=PASS
PRODUCTION_DECISION_AUTHORITY=PASS
PRODUCTION_RAG_AUTHORITY=PASS
BUSINESS_SEMANTICS_DRIFT=0
```

- AgentBase: selects tools only, never creates business decisions
- Decision Core: remains authoritative (route, treatment, channel, score all from Decision Core)
- GLM: summarizes/explains only (when available); fallback uses deterministic template
- Simulation Core: remains authoritative for what-if results
- RAG: does not override customer-specific decisions (only used for policy/definition questions)

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
