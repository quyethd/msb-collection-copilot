# TASK-018-AGENT-FIRST-CONVERSATION-ORCHESTRATION-V1

## 0. Task identity

**Task ID:** `TASK-018-AGENT-FIRST-CONVERSATION-ORCHESTRATION-V1`  
**Project:** MSB Trợ Lý Thu Hồi Nợ  
**Repository:** `/opt/msb-collection-copilot`  
**Branch:** `master`

Prerequisite:
TASK017_CLOSED=YES

Starting baseline:
branch=master
HEAD=1217e75

TASK017_COMMIT=c200f09
TASK017_CLOSURE_REPORT_COMMIT=1217e75
```

TASK-018 is **NOT** a system-architecture rewrite.

It is a **conversation-layer refactor** that makes GreenNode AgentBase the primary semantic planner while preserving all existing system boundaries, APIs, business logic, transport, frontend, and production architecture.

---

# 1. Objective

Transform the assistant from:

> keyword / if-else / scripted-intent routing with AgentBase as fallback

into:

> **AgentBase-first semantic conversation orchestration**

while keeping:

- Decision Core unchanged;
- Simulation Core unchanged;
- RAG unchanged except for tool usage;
- Web/Zalo external contracts unchanged;
- frontend architecture unchanged;
- Zalo transport unchanged;
- auth/session unchanged;
- tool implementations unchanged unless a narrow bug fix is necessary;
- production topology unchanged.

The assistant should be able to understand natural Vietnamese conversation without requiring users to memorize specific commands or demo phrases.

Primary product goal:

> **The user expresses a business need naturally; the Agent understands it, chooses the minimum approved tools, keeps the conversation context, and produces a grounded answer.**

Primary safety goal:

> **The Agent may understand and orchestrate, but it may not decide banking policy.**

---

# 2. Non-negotiable architectural invariants

TASK-018 must preserve the current architecture.

The following components remain authoritative and must not be redesigned:

```text
Web App
Zalo Bot Transport
Authenticated Backend/API
Decision Core
Simulation Core
Knowledge RAG
GreenNode Vector Database
GreenNode MaaS
Existing business tools
Session/Auth
Production service topology
```

Forbidden:

- moving business rules into prompts;
- moving score calculation into LLM;
- replacing Decision Core with AgentBase;
- changing public API contracts;
- changing Zalo provider/transport;
- changing frontend routing architecture;
- changing database schema unless strictly required for optional conversation state and backward-compatible;
- introducing a new workflow engine;
- creating a second independent business-decision implementation;
- adding autonomous write/action tools;
- removing deterministic safety guards.

Required:

```text
SYSTEM_ARCHITECTURE_CHANGED=NO
DECISION_CORE_CHANGED=NO
SIMULATION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
ZALO_TRANSPORT_CHANGED=NO
FRONTEND_ARCHITECTURE_CHANGED=NO
AUTH_CONTRACT_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0
```

---

# 3. Target architecture

Keep the existing system boundaries.

Only change the internal conversation orchestration responsibility.

## Before

```text
User
 ↓
keyword / if-else / handcrafted intent router
 ↓
known intent?
 ├─ yes → tool
 └─ no  → Agent / fallback / generic summary
 ↓
Decision / RAG / Simulation
 ↓
response
```

## Target

```text
User
 ↓
minimal deterministic safety guards
 ↓
Conversation Context Builder
 ↓
GreenNode AgentBase
    = primary semantic planner
 ↓
structured plan
 ↓
approved read/compute tools
 ↓
Decision Core / Simulation / RAG / Customer facts
 ↓
canonical evidence
 ↓
GLM response composition
 ↓
truth / authority validator
 ↓
existing Web or Zalo formatter
 ↓
User
```

Important:

> **AgentBase becomes the primary semantic planner, not the business authority.**

---

# 4. Responsibility split

## 4.1. AgentBase owns

AgentBase may decide:

- what the user is asking;
- whether current conversation context is sufficient;
- which approved tools are required;
- the minimum sequence of tools;
- whether a clarification is genuinely required;
- whether the user refers to the active CIF;
- whether the user refers to the prior answer, prior simulation, prior list, or prior topic;
- how to combine multiple tool results into one grounded answer.

## 4.2. Decision Core owns

Decision Core exclusively owns:

- route;
- Recovery Opportunity Score;
- score components;
- business precedence;
- treatment;
- channel;
- when;
- deterministic next-best-action result.

## 4.3. Simulation Core owns

Simulation Core exclusively owns:

- supported hypothetical fields;
- recomputation;
- before/after decision;
- baseline preservation.

## 4.4. RAG owns

Knowledge retrieval owns:

- policy/domain/product knowledge;
- source citations;
- knowledge grounding.

## 4.5. Validator owns

Validator must prevent:

- wrong CIF;
- unsupported numeric claims;
- score mismatch;
- route/treatment/channel mismatch;
- baseline/simulation mixing;
- unsupported policy statements;
- raw enum leakage where public labels exist.

---

# 5. Minimal deterministic guards

TASK-018 must NOT remove all deterministic code.

Keep deterministic handling only where it adds safety, protocol correctness, or obvious fast-path behavior.

Allowed deterministic guards include:

```text
auth
session validation
CIF syntax / exact CIF extraction
tool allowlist
tool schema validation
timeouts
max tool calls
dedupe
rate limits
explicit reset / reconnect commands
explicit baseline restore
security boundaries
response validation
known provider protocol commands
```

Optional simple fast paths are allowed for extremely obvious cases such as:

```text
exact greeting
explicit help
exact reset
```

But these must not become the main semantic routing system.

Forbidden pattern:

```text
if user says phrase A → intent X
if user says phrase B → intent X
if user says phrase C → intent X
...
```

Required target:

```text
HANDCRAFTED_UTTERANCE_ROUTING_REDUCED >= 80%
```

This metric refers to semantic phrase-specific routing responsibility, not safety/business rules.

---

# 6. Structured Agent plan

AgentBase must produce a structured plan rather than free-form hidden decisions.

Suggested conceptual schema:

```json
{
  "goal": "explain_score",
  "subject": {
    "cif": "SYN001346",
    "source": "active_context"
  },
  "needs_clarification": false,
  "clarification_question": null,
  "tools": [
    {
      "name": "get_score_breakdown",
      "arguments": {
        "cif": "SYN001346"
      },
      "reason": "User asks how the active CIF score is calculated"
    }
  ],
  "answer_mode": "case_specific"
}
```

Do not expose this raw structure to users.

The implementation may use a different schema if one already exists.

Required properties:

- structured;
- machine-validatable;
- bounded;
- auditable;
- tool names from allowlist only.

---

# 7. Tool policy

Reuse existing approved read/compute tools.

Typical allowed tools include existing equivalents of:

```text
get_today_worklist
get_customer_360
get_current_decision
get_score_breakdown
get_cashflow_summary
get_ptp_context
get_contact_history
simulate_decision
find_knowledge
```

Do not create action tools such as:

```text
send_zalo
send_sms
send_email
make_call
change_route
change_score
change_treatment
create_ptp
update_ptp
update_customer
```

Required:

```text
ACTION_TOOLS_EXPOSED=NO
```

---

# 8. Tool descriptions are part of the Agent contract

Each tool description must clearly define:

```text
Purpose
When to use
When NOT to use
Authority level
Required arguments
Optional arguments
Output semantics
Timeout
Fallback
```

Example semantic distinction:

### get_customer_360

Use when:
- user requests general customer overview;
- assistant needs basic context before another case-specific tool.

Do NOT use as the sole answer when user explicitly asks:
- score;
- score breakdown;
- current decision;
- PTP;
- cashflow;
- contact history;
- simulation;
- today worklist.

### get_score_breakdown

Use when:
- user asks how the score is calculated;
- user asks why score is high/low;
- user asks about one score component;
- user refers to "điểm này", "điểm của khách", "sao lại 69".

---

# 9. Conversation memory

The Agent should receive a compact, explicit context rather than the entire raw chat history.

Minimum state:

```text
active_cif
last_subject
last_goal
last_topic
last_worklist
last_decision
last_score
last_simulation
pending_clarification
conversation_summary
channel
```

The context builder must distinguish:

```text
BASELINE STATE
SIMULATION STATE
KNOWLEDGE TOPIC
WORKLIST CONTEXT
ACTIVE CASE
```

Rules:

- changing CIF clears case-local simulation;
- returning to baseline clears simulation state;
- global questions may ignore active CIF;
- prior worklist can resolve references such as "khách đầu tiên";
- knowledge follow-up can resolve "CBS thì sao?";
- pronouns can resolve only when confidence is sufficient;
- context must never cross user/chat/CIF boundaries.

---

# 10. Natural reference resolution

The Agent should resolve natural references such as:

```text
khách này
nó
thằng đầu tiên
khách thứ 2
cif vừa rồi
điểm nó
quyết định đó
trường hợp trên
nếu thế thì sao
thế giờ làm gì
còn CBS?
còn khách kia?
```

Resolution must use explicit conversation state.

If more than one interpretation is plausible:
clarify.

Never silently choose a CIF when ambiguity remains.

Required:

```text
REFERENCE_RESOLUTION_ACCURACY >= 95%
WRONG_CIF=0
```

---

# 11. Multi-intent questions

The Agent must support questions containing more than one request.

Examples:

```text
SYN001346 đang bao nhiêu điểm và vì sao hôm nay phải xem?
```

Expected:
- score;
- priority explanation;
- minimum required tools.

Example:

```text
CALL với CBS khác nhau thế nào, và khách này đang ở tuyến nào?
```

Expected:
- knowledge comparison;
- current route for active CIF.

Agent should plan multiple approved tools when necessary.

Do not force one-intent-only behavior.

Required:

```text
MULTI_INTENT_SUCCESS_RATE >= 95%
```

---

# 12. Natural multi-turn conversation target

The following style must work without pre-scripted phrase rules:

```text
User: Hôm nay tao cần làm gì?
Assistant: ...

User: Tại sao thằng đầu tiên lại được ưu tiên?
Assistant: ...

User: Điểm nó thấp mà?
Assistant: ...

User: Nếu tuần này nó không có tiền vào thì sao?
Assistant: ...

User: Vậy gọi luôn à?
Assistant: ...

User: Còn khách thứ 2?
Assistant: ...
```

The Agent must infer:

- "thằng đầu tiên" = first CIF from last worklist;
- "nó" = current referenced CIF;
- score question = score context;
- hypothetical = simulation for current CIF;
- "gọi luôn à?" = question about simulated action/channel;
- "khách thứ 2" = second CIF from previous worklist.

No phrase-specific hardcoding.

---

# 13. Clarification policy

Do NOT over-clarify.

Clarification is needed only when:

- CIF reference is ambiguous;
- request may mean business policy or case simulation with materially different outcomes;
- required tool argument cannot be safely inferred;
- unsupported hypothetical requires the user to choose an allowed interpretation.

Good clarification:

> “Anh/Chị muốn mô phỏng khách không thực hiện cam kết hiện tại, hay hỏi quy trình xử lý chung?”

Bad clarification:

> “Anh/Chị muốn hỏi về quyết định, dòng tiền hay mô phỏng nào?”

when the user's intent is already semantically obvious.

Required:

```text
UNNECESSARY_CLARIFICATION_RATE <= 5%
```

---

# 14. Fallback policy

The Agent must not use generic customer summary as the universal fallback.

Fallback hierarchy:

```text
1. Agent resolves intent confidently
2. Agent uses context to resolve reference
3. Agent asks focused clarification
4. Safe scope explanation
```

Forbidden:

```text
UNKNOWN + active_cif
→ generic customer summary
```

Required:

```text
GENERIC_SUMMARY_FALLBACK_RATE <= 1%
ACTIVE_CIF_HIJACK_RATE=0
```

---

# 15. Response quality

Answers should be:

- concise by default;
- professional Vietnamese;
- evidence-based;
- direct;
- context-aware;
- not overloaded with internal terminology.

For case-specific answers, prefer:

```text
Kết luận
→ Lý do chính
→ Bằng chứng
→ Điều cần chú ý / next question if useful
```

Do not expose:

```text
raw JSON
internal tool names
planner rounds
fallback level
internal enum
task IDs
commit IDs
```

---

# 16. Public label mapping

Preserve public-friendly mappings for raw internal values.

At minimum:

```text
OPEN       → Đang mở
KEPT       → Đã thực hiện
PARTIAL    → Thanh toán một phần
BROKEN     → Không thực hiện cam kết
EXPIRED    → Hết hạn
CANCELLED  → Đã hủy
NONE       → Chưa có cam kết
```

Audit route/treatment/channel/other enums for similar leakage.

Required:

```text
RAW_ENUM_LEAK=0
```

---

# 17. Agent boundaries

Hard bounds remain mandatory:

```text
MAX_TOOL_CALLS=5
MAX_PLANNING_ROUNDS=2
MAX_RAG_CALLS=1
MAX_SIMULATION_CALLS=1
MAX_AGENT_TIME_SECONDS<=8
```

If more information is required than allowed:
return the best grounded partial answer or focused clarification.

No loops.

Required:

```text
MAX_TOOL_CALL_BREACH=0
AGENT_LOOP=0
```

---

# 18. Failure / fallback levels

Preserve current safe degradation behavior.

Conceptually:

```text
Level 1:
AgentBase semantic planner
+ dynamic approved tools
+ GLM
+ validator

Level 2:
existing deterministic/static orchestration
+ canonical tools
+ GLM
+ validator

Level 3:
deterministic safe answer/template
```

Important:

TASK-018 must not delete the existing stable fallback path.

Agent-first is the preferred semantic path, not the only survivable path.

Required:

```text
AGENT_FAILURE_FALLBACK=PASS
```

---

# 19. Feature flag / rollout safety

Introduce or reuse a runtime feature flag if practical:

```text
AGENT_FIRST_CONVERSATION_ENABLED=true/false
```

or an equivalent existing configuration.

Requirements:

- default can be controlled without code changes;
- fallback path remains available;
- rollback does not require reverting Decision Core;
- flag does not alter business semantics.

If repository already has a compatible feature flag mechanism:
reuse it.

Do not introduce a new config framework.

---

# 20. Shadow comparison before cutover

Before making Agent-first the production primary path, run the TASK-017 regression corpus through:

```text
OLD RESOLVER
vs
AGENT-FIRST RESOLVER
```

Compare:

- semantic goal;
- CIF;
- tools;
- score;
- decision;
- simulation;
- answer type.

Agent-first must not degrade canonical business correctness.

Required:

```text
SHADOW_COMPARISON=PASS
BUSINESS_RESULT_REGRESSION=0
```

---

# 21. TASK-017 regression suite is immutable gate

All TASK-017 tests/evals become mandatory regression gates.

Do not delete, relax, relabel, or rewrite expected outputs simply to make TASK-018 pass.

Required:

```text
TASK017_REGRESSION_SUITE=100% PASS
TASK017_WEB_REPLAY=PASS
TASK017_ZALO_REPLAY=PASS
```

---

# 22. Expanded Agent intelligence evaluation

In addition to TASK-017 corpus, generate new tests that specifically verify non-scripted conversation ability.

At least:

```text
500+ utterances
100+ multi-turn conversations
50+ reference-resolution cases
30+ multi-intent questions
30+ ambiguous/clarification cases
30+ simulation follow-ups
30+ knowledge follow-ups
```

If practical, exceed these numbers.

Labels must be grounded in canonical business/tool behavior.

Do not let the same Agent generate both test question and expected business truth without deterministic verification.

---

# 23. Paraphrase generalization gate

Hold out a portion of generated/paraphrased utterances from implementation tuning.

Suggested:

```text
TRAIN/TUNING SET: 70%
HOLDOUT SET: 30%
```

Do not inspect/tune phrase-specific rules against the holdout set.

Required:

```text
HOLDOUT_INTENT_ACCURACY >= 95%
```

This gate exists to prove the system generalizes beyond scripted phrases.

---

# 24. Cross-channel semantic parity

Web and Zalo must share the same semantic behavior.

Required:

```text
WEB_ZALO_INTENT_PARITY >= 99%
WEB_ZALO_TOOL_PLAN_PARITY >= 98%
WEB_ZALO_DECISION_PARITY = 100%
WEB_ZALO_SCORE_PARITY = 100%
```

Only channel formatting may differ.

---

# 25. Core quality metrics

Required:

```text
IN_SCOPE_INTENT_ACCURACY >= 97%
HOLDOUT_INTENT_ACCURACY >= 95%
PARAPHRASE_INTENT_ACCURACY >= 97%
FOLLOWUP_RESOLUTION_ACCURACY >= 97%
REFERENCE_RESOLUTION_ACCURACY >= 95%
MULTI_INTENT_SUCCESS_RATE >= 95%

IN_SCOPE_FALLBACK_RATE <= 2%
GENERIC_SUMMARY_FALLBACK_RATE <= 1%
ACTIVE_CIF_HIJACK_RATE = 0
UNNECESSARY_CLARIFICATION_RATE <= 5%

WRONG_TOOL_RATE <= 2%
UNNECESSARY_TOOL_RATE <= 10%

WRONG_CIF = 0
CROSS_CIF_CONTEXT_LEAK = 0
CROSS_CHAT_CONTEXT_LEAK = 0
SIMULATION_CONTEXT_LEAK = 0

DECISION_PARITY = 100%
SCORE_PARITY = 100%

RAW_ENUM_LEAK = 0
UNSUPPORTED_DECISION_CLAIM = 0

MAX_TOOL_CALL_BREACH = 0
AGENT_LOOP = 0
```

---

# 26. Architecture quality metrics

Required:

```text
AGENTBASE_PRIMARY_SEMANTIC_PATH=YES

HANDCRAFTED_UTTERANCE_ROUTING_REDUCED>=80%

DUPLICATED_WEB_ZALO_SEMANTIC_ROUTING=NO
```

Important:

Do not chase these metrics by deleting useful deterministic guards.

The goal is to remove phrase-specific semantic routing, not safety code.

---

# 27. Business canaries

Preserve all existing canaries.

At minimum:

### SYN002846

```text
route=CALL
score=47
treatment=WAIT_SELF_CURE
channel=NONE
```

Simulation:

```text
inflow_7d=0
→ CONTACT / CALL
```

### SYN000746

```text
score=69
```

### SYN001346

Use current canonical production fixture.

Required:

```text
DECISION_PARITY=100%
SCORE_PARITY=100%
```

---

# 28. Security and banking-safety audit

Verify:

- no new public backend exposure;
- no credentials in frontend;
- no secrets in Agent prompt;
- no unrestricted tool execution;
- no write/action tools;
- no cross-user memory;
- no cross-CIF leakage;
- no model-generated score;
- no model-generated business treatment;
- tool arguments validated;
- tool outputs bounded/sanitized.

Required:

```text
SECURITY_REGRESSION=0
ACTION_TOOLS_EXPOSED=NO
FRONTEND_SECRET_LEAK=0
```

---

# 29. Performance

Agent-first must remain usable interactively.

Measure:

```text
p50 response latency
p95 response latency
tool calls per turn
Agent planning time
fallback rate
```

Do not set arbitrary latency PASS unless current infrastructure supports it.

But report actual values.

Suggested target where feasible:

```text
P95_AGENT_PLANNING_SECONDS <= 8
```

If GreenNode/provider latency prevents this:
report actual value rather than hiding it.

---

# 30. Source scope

Allowed:

- conversation orchestration;
- semantic planner adapter;
- context builder;
- AgentBase prompt/instructions;
- tool metadata/descriptions;
- planner output schema;
- response validator;
- Web/Zalo conversation adapters;
- conversation tests/evals;
- feature flag;
- task report.

Do not change:

- Decision Core;
- scoring rules;
- routing rules;
- NBA;
- PTP semantics;
- Simulation Core business logic;
- RAG corpus semantics;
- frontend architecture;
- Zalo transport architecture;
- auth architecture;
- deployment topology.

---

# 31. Implementation strategy

Use incremental migration.

## Phase A — Inspect

Map:

- all current handcrafted routing;
- duplicated Web/Zalo routing;
- AgentBase current invocation points;
- fallback path;
- tool registry;
- state/context.

## Phase B — Characterization tests

Freeze current accepted behavior from TASK-017.

## Phase C — Agent-first adapter

Add AgentBase semantic planner behind existing conversation interface.

Do not rewrite callers.

## Phase D — Shadow evaluation

Old vs new semantic path.

## Phase E — Feature-flagged cutover

Enable Agent-first as primary semantic path.

## Phase F — Remove obsolete phrase routing

Only after regression proves safe.

Do not delete fallback/safety guards.

---

# 32. Test workflow

```text
INSPECT
→ ARCHITECTURE MAP
→ CHARACTERIZATION TESTS
→ AGENT-FIRST DESIGN
→ IMPLEMENT ADAPTER
→ TOOL DESCRIPTION AUDIT
→ CONTEXT BUILDER
→ STRUCTURED PLAN VALIDATION
→ SHADOW COMPARISON
→ PARAPHRASE / HOLDOUT TESTS
→ MULTI-TURN TESTS
→ REFERENCE TESTS
→ MULTI-INTENT TESTS
→ WEB/ZALO PARITY
→ BUSINESS CANARIES
→ PERFORMANCE
→ SELF-REVIEW
→ RETEST
→ VERY AUDIT
→ COMMIT
→ BACKUP
→ FEATURE-FLAGGED DEPLOY
→ PRODUCTION WEB QA
→ PRODUCTION ZALO QA
→ CLOSEOUT
```

---

# 33. Very Audit

Before commit independently verify:

1. System architecture unchanged.
2. Decision Core unchanged.
3. Simulation Core unchanged.
4. Business semantics unchanged.
5. TASK-017 regression suite still passes.
6. AgentBase is primary semantic planner.
7. Handcrafted phrase routing substantially reduced.
8. Safety guards remain.
9. Web/Zalo semantic behavior is shared/parity-tested.
10. No wrong CIF.
11. No cross-chat/CIF context leakage.
12. No simulation leakage.
13. No model-generated business decisions.
14. No action tools.
15. Tool descriptions correctly separate responsibilities.
16. Clarification is focused, not excessive.
17. Reference resolution works.
18. Multi-intent works.
19. Holdout generalization passes.
20. Feature flag rollback works.

Required:

```text
VERY_AUDIT=PASS
```

---

# 34. Production validation scenarios

Use natural conversation, not exact scripted demo phrases.

## Scenario A — Worklist → reference → score → simulation

```text
Hôm nay tao cần xử lý gì?

Tại sao khách đầu tiên lại nằm trên?

Điểm nó có cao không?

Điểm đó hình thành từ đâu?

Nếu tuần này nó không có tiền vào thì sao?

Vậy bây giờ gọi luôn à?

Còn khách thứ hai?
```

## Scenario B — knowledge + case

```text
CALL với CBS khác nhau chỗ nào?

Khách đang mở của tao thuộc tuyến gì?

Tại sao route CALL mà hôm nay lại chưa cần gọi?
```

## Scenario C — ambiguous question

```text
Khách không trả thì sao?
```

Expected:
focused clarification when needed.

## Scenario D — switch CIF

```text
Cho tao xem SYN001346

Điểm nó?

Chuyển sang SYN000746

Còn điểm khách này?

Khách trước là bao nhiêu?
```

## Scenario E — natural pronouns

```text
Giải thích SYN002846

Nếu không có tiền vào tuần này thì sao?

Tại sao lại đổi?

Thế action mới là gì?

Quay lại dữ liệu thật.
```

---

# 35. Production acceptance

Required:

```text
PRODUCTION_AGENTBASE_PRIMARY_SEMANTIC_PATH=PASS

PRODUCTION_TASK017_REGRESSION=PASS

PRODUCTION_DECISION_PARITY=100%
PRODUCTION_SCORE_PARITY=100%

PRODUCTION_WRONG_CIF=0
PRODUCTION_CROSS_CIF_CONTEXT_LEAK=0
PRODUCTION_CROSS_CHAT_CONTEXT_LEAK=0
PRODUCTION_SIMULATION_CONTEXT_LEAK=0

PRODUCTION_ACTIVE_CIF_HIJACK_RATE=0

PRODUCTION_WEB_ZALO_INTENT_PARITY>=99%

PRODUCTION_RAW_ENUM_LEAK=0
PRODUCTION_UNSUPPORTED_DECISION_CLAIM=0

PRODUCTION_WEB_AGENT_CONVERSATION=PASS
PRODUCTION_ZALO_AGENT_CONVERSATION=PASS

FEATURE_FLAG_ROLLBACK_TEST=PASS
```

---

# 36. Rollback triggers

Rollback Agent-first flag if:

- Decision parity < 100%;
- score parity < 100%;
- wrong CIF occurs;
- cross-chat/CIF context leak;
- simulation state leaks;
- Agent loops;
- action tool exposed;
- Web/Zalo semantics diverge materially;
- TASK-017 regression fails;
- auth/security regression;
- business semantics drift.

Rollback must restore prior TASK-017 conversation path without changing Decision Core or production data.

---

# 37. Task report

Create:

`task-results/TASK-018-AGENT-FIRST-CONVERSATION-ORCHESTRATION-V1-FINAL.md`

Include:

```text
TASK_ID=TASK-018-AGENT-FIRST-CONVERSATION-ORCHESTRATION-V1

PREVIOUS_HEAD=<TASK017_FINAL_MASTER_HEAD>
TASK018_COMMIT=<sha>

SYSTEM_ARCHITECTURE_CHANGED=NO
DECISION_CORE_CHANGED=NO
SIMULATION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
ZALO_TRANSPORT_CHANGED=NO
FRONTEND_ARCHITECTURE_CHANGED=NO
AUTH_CONTRACT_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

AGENTBASE_PRIMARY_SEMANTIC_PATH=YES
HANDCRAFTED_UTTERANCE_ROUTING_REDUCED=<actual>
DUPLICATED_WEB_ZALO_SEMANTIC_ROUTING=NO

TASK017_REGRESSION_SUITE=100% PASS
SHADOW_COMPARISON=PASS
BUSINESS_RESULT_REGRESSION=0

IN_SCOPE_INTENT_ACCURACY=<actual>
HOLDOUT_INTENT_ACCURACY=<actual>
PARAPHRASE_INTENT_ACCURACY=<actual>
FOLLOWUP_RESOLUTION_ACCURACY=<actual>
REFERENCE_RESOLUTION_ACCURACY=<actual>
MULTI_INTENT_SUCCESS_RATE=<actual>

IN_SCOPE_FALLBACK_RATE=<actual>
GENERIC_SUMMARY_FALLBACK_RATE=<actual>
ACTIVE_CIF_HIJACK_RATE=0
UNNECESSARY_CLARIFICATION_RATE=<actual>

WRONG_TOOL_RATE=<actual>
UNNECESSARY_TOOL_RATE=<actual>

WEB_ZALO_INTENT_PARITY=<actual>
WEB_ZALO_TOOL_PLAN_PARITY=<actual>
WEB_ZALO_DECISION_PARITY=100%
WEB_ZALO_SCORE_PARITY=100%

WRONG_CIF=0
CROSS_CIF_CONTEXT_LEAK=0
CROSS_CHAT_CONTEXT_LEAK=0
SIMULATION_CONTEXT_LEAK=0

DECISION_PARITY=100%
SCORE_PARITY=100%

RAW_ENUM_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0

MAX_TOOL_CALL_BREACH=0
AGENT_LOOP=0
ACTION_TOOLS_EXPOSED=NO
SECURITY_REGRESSION=0

P50_RESPONSE_LATENCY=<actual>
P95_RESPONSE_LATENCY=<actual>

FEATURE_FLAG_ROLLBACK_TEST=PASS

VERY_AUDIT=PASS
READY_TO_DEPLOY=YES/NO
```

---

# 38. Commit / deployment

Only commit if all pre-production mandatory gates pass.

Suggested commit:

```text
Promote AgentBase to primary conversation planner
```

No push.

Before deploy:

- backup;
- record rollback point;
- enable Agent-first via feature flag;
- restart only required services;
- do not redeploy unrelated components.

---

# 39. Final closeout

Only close when all mandatory gates pass.

Return:

```text
TASK-018 AGENT-FIRST CONVERSATION ORCHESTRATION V1 PRODUCTION CLOSED — PASS

TASK018_COMMIT=<sha>
CLOSURE_REPORT_COMMIT=<sha>
FINAL_MASTER_HEAD=<sha>
BACKUP_PATH=<path>

SYSTEM_ARCHITECTURE_CHANGED=NO
DECISION_CORE_CHANGED=NO
SIMULATION_CORE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

AGENTBASE_PRIMARY_SEMANTIC_PATH=YES
HANDCRAFTED_UTTERANCE_ROUTING_REDUCED=<actual>

TASK017_REGRESSION_SUITE=100% PASS

IN_SCOPE_INTENT_ACCURACY=<actual>
HOLDOUT_INTENT_ACCURACY=<actual>
PARAPHRASE_INTENT_ACCURACY=<actual>
FOLLOWUP_RESOLUTION_ACCURACY=<actual>
REFERENCE_RESOLUTION_ACCURACY=<actual>
MULTI_INTENT_SUCCESS_RATE=<actual>

WRONG_CIF=0
CROSS_CIF_CONTEXT_LEAK=0
CROSS_CHAT_CONTEXT_LEAK=0
SIMULATION_CONTEXT_LEAK=0

DECISION_PARITY=100%
SCORE_PARITY=100%

WEB_ZALO_INTENT_PARITY=<actual>
WEB_ZALO_TOOL_PLAN_PARITY=<actual>

RAW_ENUM_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0

PRODUCTION_WEB_AGENT_CONVERSATION=PASS
PRODUCTION_ZALO_AGENT_CONVERSATION=PASS

FEATURE_FLAG_ROLLBACK_TEST=PASS
VERY_AUDIT=PASS
ROLLBACK_REQUIRED=NO
TASK_018_CLOSED=YES
PUSH=NO
```

If blocked:
report the real blocker only.

Do not start another task.

---

# 40. Final principle

> **AgentBase là bộ não hội thoại, không phải bộ não nghiệp vụ.**

> **Người dùng được nói tự nhiên; Agent tự hiểu, tự chọn công cụ và giữ ngữ cảnh.**

> **Decision Core vẫn là nguồn duy nhất quyết định route, score, treatment và channel.**

> **TASK-018 phải làm Agent thông minh hơn mà không làm hệ thống khó kiểm soát hơn.**
