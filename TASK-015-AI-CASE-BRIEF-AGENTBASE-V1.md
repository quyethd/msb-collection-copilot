# TASK-015-AI-CASE-BRIEF-AGENTBASE-V1

## 0. Task identity

**Task ID:** `TASK-015-AI-CASE-BRIEF-AGENTBASE-V1`

**Project:** MSB Trợ Lý Thu Hồi Nợ  
**Repository:** `/opt/msb-collection-copilot`  
**Branch:** `master`

**Goal:** Bổ sung AI Case Brief V1 dùng GreenNode AgentBase theo mô hình **bounded orchestration**, áp dụng cho mọi CIF, nhưng **giữ nguyên kiến trúc FE + BE hiện tại, giữ nguyên Decision Core và toàn bộ business semantics đã chốt**.

---

## 1. Quyết định kiến trúc đã khóa

AI Case Brief V1 là **capability bổ sung**, không phải kiến trúc thay thế.

```text
Existing FE
  ↓
Existing BE / authenticated app flow
  ↓
AI Case Brief module
  ↓
GreenNode AgentBase — bounded planner
  ↓
Read-only / compute tools trong allowlist
  ↓
Canonical Case Context
  ↓
GreenNode MaaS / GLM 5.2
  ↓
Structured response
  ↓
Fact / decision validator
  ↓
Existing FE customer page
```

### Nguyên tắc bất biến

- Giữ nguyên FE architecture hiện tại.
- Giữ nguyên BE architecture hiện tại.
- Không refactor sang framework mới.
- Không thay routing hiện tại.
- Không thay auth contract hiện tại.
- Không thay Decision Core.
- Không thay Recovery Opportunity score.
- Không thay NBA precedence.
- Không thay Routing CALL/CBS.
- Không thay PTP rules.
- Không thay treatment selection.
- Không thay channel selection.
- Không thay existing simulation semantics.
- Không thay existing Zalo flow.
- Không thay existing RAG authority.

Nếu phải sửa code cũ, chỉ sửa **bounded, backward-compatible, có regression test**.

---

## 2. Architectural gates

```text
User / Active CIF
        ↓
BOUNDARY 1 — Session / Auth / Active-CIF gate
        ↓
BOUNDARY 2 — AgentBase bounded planning gate
        ↓
BOUNDARY 3 — Tool allowlist / permission gate
        ↓
BOUNDARY 4 — Canonical Case Context normalization
        ↓
BOUNDARY 5 — Decision authority gate
        ↓
BOUNDARY 6 — Optional knowledge grounding gate
        ↓
BOUNDARY 7 — GLM structured generation
        ↓
BOUNDARY 8 — Schema + fact + decision validation
        ↓
BOUNDARY 9 — Safe fallback
        ↓
UI render
```

### Authority hierarchy

```text
1. Decision Core
2. Canonical business facts
3. Simulation Core
4. Grounded knowledge sources
5. AgentBase planner
6. GLM wording / explanation
```

AgentBase chỉ được quyết định:

> **Cần gọi công cụ nào để lấy đủ bằng chứng cho câu hỏi hiện tại?**

AgentBase không được quyết định:

> **Khách hàng này nên làm gì về mặt nghiệp vụ?**

---

## 3. Scope V1

### Bao gồm

- AI Case Brief cho mọi CIF hợp lệ.
- Active CIF lấy từ application state.
- GreenNode AgentBase bounded orchestration.
- Tool registry.
- Tool schemas.
- Tool descriptions chất lượng cao.
- Minimum-tool selection.
- Canonical Case Context builder.
- Decision snapshot.
- Conditional RAG.
- Baseline + simulation state.
- GreenNode MaaS / GLM 5.2 structured generation.
- Strict validator.
- Deterministic fallback.
- Cache/versioning.
- Audit metadata.
- Customer-page AI Case Brief UI.
- Follow-up Q&A trên đúng CIF đang mở.
- Tool-selection evaluation.
- Golden scenario evaluation.
- Bounded production deployment.

### Không bao gồm

- Zalo integration cho Case Brief.
- Customer-facing bot.
- Auto call/SMS/Zalo/email.
- Create/modify PTP.
- New ML propensity model.
- New score.
- New business/routing/treatment/channel rule.
- Policy override.
- AgentBase write/action tools.
- Landing update.
- Autonomous agent loop.
- AgentBase bắt buộc phải sống để customer page hoạt động.

---

## 4. AI Case Brief — business definition

Tên UI:

> **Tóm tắt AI cho hồ sơ**

Tên kỹ thuật:

> `AI Case Brief`

Mục tiêu: với bất kỳ CIF nào, officer đọc trong khoảng 15–30 giây và hiểu được:

1. Hồ sơ đang ở trạng thái nào.
2. Vì sao hệ thống đưa ra kết quả hiện tại.
3. Bằng chứng quan trọng nhất.
4. Điểm nào officer cần tập trung.
5. Dữ liệu/nguồn nào đang thiếu hoặc cần tham khảo.

AI Case Brief **không được tạo quyết định mới**.

---

## 5. FE integration — giữ nguyên kiến trúc cũ

Chỉ thêm một block/card vào customer page hiện có.

```text
Customer Header
↓
Current Decision Summary
↓
AI Case Brief
↓
Existing Evidence / Details
```

### Trạng thái UI

```text
IDLE
LOADING
READY
FALLBACK
ERROR
```

Không được:

- block toàn bộ customer page trong lúc gọi AI;
- làm mất Decision Summary hiện tại;
- thay route/page structure;
- sửa sidebar/navigation ngoài phạm vi cần thiết.

Có thể thêm ô:

> **Hỏi thêm về hồ sơ này**

Active CIF phải lấy từ application state. Khi đổi CIF phải clear case-local context.

---

## 6. Baseline vs Simulation

Case Brief có 2 state:

```text
BASELINE
SIMULATION
```

Simulation phải hiển thị rõ:

> **Đang xem kịch bản mô phỏng — dữ liệu gốc không thay đổi.**

Backend truyền explicit state, không để GLM tự đoán.

Simulation result phải đến từ existing Simulation Core.

---

# 7. Tool registry V1

AgentBase chỉ được thấy allowlist:

```text
get_customer_360
get_current_decision
get_cashflow_summary
get_ptp_context
get_contact_history
get_score_breakdown
simulate_decision
find_knowledge
```

Có thể bổ sung sau nếu source hiện tại thật sự cần:

```text
get_payment_history
get_recent_case_changes
```

---

# 8. Tool permission model

## READ

```text
get_customer_360
get_current_decision
get_cashflow_summary
get_ptp_context
get_contact_history
get_score_breakdown
find_knowledge
```

## COMPUTE

```text
simulate_decision
```

## ACTION — không expose

```text
send_zalo
send_sms
send_email
make_call
create_ptp
update_ptp
update_customer
change_route
change_score
override_policy
```

---

# 9. Tool specification contract

Mỗi tool phải có:

- name;
- purpose;
- input schema;
- output schema;
- when_to_use;
- when_not_to_use;
- authority;
- timeout;
- fallback;
- test cases.

Không viết description kiểu “lấy dữ liệu X” chung chung.

---

# 10. get_customer_360

### Description

```text
Purpose:
Lấy thông tin tổng quan hiện tại của một CIF.

Use when:
- hỏi DPD;
- tổng dư nợ;
- phân khúc;
- trạng thái hồ sơ;
- facts tổng quan.

Do NOT use when:
- chỉ hỏi policy/định nghĩa chung;
- chỉ hỏi PTP;
- chỉ hỏi Decision Core result.

Authority:
Facts only. Does not decide route, score, treatment or channel.
```

---

# 11. get_current_decision

### Description

```text
Purpose:
Lấy kết quả chính thức hiện tại từ Decision Core.

Use when user asks:
- giờ nên làm gì;
- vì sao gọi/chờ/nhắc;
- điểm hiện tại;
- route;
- treatment;
- channel;
- quyết định hiện tại.

Important:
This is the authoritative source for route, score, treatment and channel.

Never infer or replace these values using another tool or model.
```

---

# 12. get_cashflow_summary

### Description

```text
Purpose:
Lấy các tín hiệu dòng tiền gần đây của một CIF.

Use when:
- hỏi tiền vào / dòng tiền;
- tín hiệu tự thanh toán;
- thay đổi tài chính gần đây;
- lý do WAIT_SELF_CURE;
- giả định liên quan inflow.

Do NOT use when:
- chỉ hỏi CALL/CBS;
- chỉ hỏi PTP;
- hỏi policy chung không gắn CIF.

Important:
Facts only. Does not determine treatment, channel or score.
```

---

# 13. get_ptp_context

### Description

```text
Purpose:
Lấy cam kết thanh toán gần nhất và trạng thái PTP.

Use when user mentions:
- PTP;
- cam kết;
- hứa trả;
- thất hứa;
- thanh toán một phần;
- đã hẹn trả chưa;
- cam kết gần nhất;
- treatment liên quan PTP.

Important:
Return observed PTP facts only.
Do not infer willingness or intent beyond available data.
```

---

# 14. get_contact_history

### Description

```text
Purpose:
Lấy summary lịch sử liên hệ gần đây.

Use when:
- hỏi lần gọi gần nhất;
- đã liên hệ chưa;
- khách có bắt máy không;
- kết quả cuộc gọi;
- callback;
- VERIFY_CONTACT;
- thay đổi từ lần liên hệ trước.

Important:
Prefer summarized contact facts.
Do not return large raw call-history payloads unless necessary.
```

---

# 15. get_score_breakdown

### Description

```text
Purpose:
Lấy breakdown canonical của Recovery Opportunity score.

Use when:
- hỏi vì sao điểm là X;
- thành phần kéo điểm lên/xuống;
- ability/willingness/contactability/timing;
- giải thích score.

Important:
Recovery Opportunity is a prioritization score, not payment probability.
Never recalculate or modify it using the language model.
```

---

# 16. simulate_decision

### Description

```text
Purpose:
Tính lại Decision Core trong một kịch bản giả định.

Use ONLY when user explicitly asks:
- nếu...
- giả sử...
- điều gì xảy ra nếu...
- nếu tiền vào bằng 0...
- nếu PTP thay đổi...

Never mutate original customer data.
Every output must be marked SIMULATION.
Do not call for factual questions about current state.

Simulation Core remains authoritative.
The language model only explains the result.
```

---

# 17. find_knowledge

### Description

```text
Purpose:
Tra cứu quy trình, định nghĩa, chính sách và tài liệu nghiệp vụ có nguồn.

Use when:
- CALL/CBS nghĩa là gì;
- PTP nghĩa là gì;
- policy/rule hoạt động ra sao;
- thuật ngữ nghiệp vụ;
- hướng dẫn nghiệp vụ chung.

Do NOT use to determine:
- current treatment;
- current score;
- current channel;
- current route.

For customer-specific decisions use get_current_decision.

Knowledge must not override Decision Core.
```

---

# 18. Bounded AgentBase planner

Planner rules:

```text
You are a bounded tool planner for MSB Collection Copilot.

Your job is to select the minimum set of allowed tools needed to answer the user's question.

Rules:
1. Never create business decisions.
2. get_current_decision is authoritative for route, score, treatment and channel.
3. Prefer factual tools before knowledge retrieval.
4. Use find_knowledge only for policy/definition or when facts are insufficient.
5. Use simulate_decision only for explicit hypothetical questions.
6. Reuse existing context before another tool call.
7. Never call a tool only “just in case”.
8. Never call write/action tools.
9. Stop when sufficient evidence is available.
10. Never infer active CIF; it must come from application state.
11. Never mix facts from different CIFs.
12. Never present simulation output as current-state fact.
```

Limits:

```text
MAX_TOOL_CALLS=5
MAX_PLANNING_ROUNDS=2
MAX_RAG_CALLS=1
MAX_SIMULATION_CALLS=1
MAX_AGENT_TIME_SECONDS=8
```

Nếu vượt giới hạn: fallback deterministic orchestration.

---

# 19. Initial Brief orchestration

Logical goal:

```text
build_case_brief(cif)
```

Luôn cần current decision. Các tool khác chỉ gọi khi relevant.

RAG không được gọi mặc định cho mọi CIF.

---

# 20. Follow-up Q&A orchestration

Logical goal:

```text
answer_case_question(cif, question, current_context)
```

Ví dụ:

```text
“PTP thế nào?”
→ get_ptp_context

“Tại sao chưa gọi?”
→ get_current_decision + get_cashflow_summary

“CALL khác CBS thế nào?”
→ find_knowledge

“Nếu tuần này không có tiền vào thì sao?”
→ get_current_decision + simulate_decision
```

---

# 21. Canonical Case Context Builder

Tool results phải qua `CaseContextBuilder`.

Output logic:

```json
{
  "cif": "string",
  "as_of": "datetime",
  "state": "BASELINE|SIMULATION",
  "customer": {},
  "decision": {},
  "score_breakdown": {},
  "cashflow": {},
  "ptp": {},
  "contact": {},
  "simulation": null,
  "knowledge": [],
  "missing_data": [],
  "data_quality": {}
}
```

Không hardcode golden CIF.

---

# 22. GLM role

GreenNode MaaS / GLM 5.2:

- tóm tắt;
- diễn giải;
- chuyển canonical facts thành câu trả lời dễ đọc.

Không dùng để:

- tính score;
- chọn route;
- chọn treatment;
- chọn channel;
- override policy.

---

# 23. Structured output

```json
{
  "headline": "string",
  "summary": "string",
  "key_evidence": [
    {
      "label": "string",
      "value": "string",
      "reason": "string",
      "source": "customer360|cashflow|ptp|contact|decision|score|knowledge|simulation"
    }
  ],
  "decision_explanation": ["string"],
  "officer_focus": ["string"],
  "knowledge_refs": [
    {
      "title": "string",
      "source_id": "string"
    }
  ],
  "missing_data": ["string"],
  "state": "BASELINE|SIMULATION",
  "disclaimer": "AI hỗ trợ tóm tắt và giải thích; quyết định nghiệp vụ do Bộ máy quyết định xác định."
}
```

Không có model-generated:

```text
recommended_action
new_score
new_route
new_channel
new_treatment
payment_probability
```

---

# 24. GLM system prompt contract

```text
Bạn là Trợ lý Thu hồi Nợ dành cho cán bộ MSB.

Nhiệm vụ:
TÓM TẮT và GIẢI THÍCH dữ liệu được cung cấp.

Bạn KHÔNG có quyền:
- thay đổi tuyến xử lý;
- tính hoặc sửa Recovery Opportunity score;
- thay đổi treatment;
- chọn/thay đổi channel;
- tạo chính sách nghiệp vụ;
- suy đoán dữ liệu không được cung cấp.

Decision Snapshot là kết quả chính thức từ Decision Core.
Simulation Snapshot là kết quả chính thức từ Simulation Core.

Mọi diễn giải phải nhất quán tuyệt đối với snapshot tương ứng.

Chỉ sử dụng:
1. Canonical Case Context.
2. Knowledge snippets có nguồn.

Nếu dữ liệu không tồn tại:
hãy nói rõ "chưa có dữ liệu".

Không suy diễn:
- ý định thanh toán;
- khả năng tài chính;
- nguyên nhân quá hạn;
- tình trạng liên hệ
nếu không có bằng chứng.

Trả đúng JSON schema.

Ngôn ngữ:
tiếng Việt ngắn gọn, nghiệp vụ, dễ đọc.

Đối tượng:
Collection Officer.

Mục tiêu:
giúp cán bộ hiểu hồ sơ trong khoảng 15–30 giây.
```

---

# 25. Validator — P0

Pipeline:

```text
GLM output
↓
JSON schema
↓
CIF validation
↓
score parity
↓
route/treatment/channel parity
↓
numeric fact validation
↓
simulation-state validation
↓
citation validation
↓
PASS → render
FAIL → fallback
```

Reject nếu:

- wrong CIF;
- wrong score;
- wrong route/treatment/channel;
- baseline/simulation bị lẫn;
- invented numeric fact;
- citation không tồn tại;
- wording mâu thuẫn Decision Core.

---

# 26. Fallback 3 tầng

```text
LEVEL 1
AgentBase + dynamic tools + optional RAG + GLM + validator
→ Smart Brief

LEVEL 2
Static CaseContextBuilder + existing canonical tools + GLM + validator
→ Standard AI Brief

LEVEL 3
Deterministic template
→ Safe Basic Brief
```

Customer page luôn phải hoạt động.

---

# 27. Cache

Cache key tối thiểu:

```text
cif
data_version_or_hash
decision_version_or_hash
simulation_hash
prompt_version
tool_registry_version
```

TTL khởi điểm:

```text
5–15 phút
```

Dữ liệu thay đổi → invalid cache.

---

# 28. Audit metadata

```json
{
  "cif": "string",
  "generated_at": "datetime",
  "case_context_hash": "string",
  "decision_snapshot_hash": "string",
  "prompt_version": "string",
  "tool_registry_version": "string",
  "agent_path": "AGENTBASE|STATIC|DETERMINISTIC",
  "tools_used": [],
  "model": "glm-5.2",
  "knowledge_refs": [],
  "validation_result": "PASS|FAIL",
  "latency_ms": 0
}
```

Không log secret hoặc full sensitive prompt không cần thiết.

---

# 29. Security

- Dùng auth/session contract hiện tại.
- Không tạo public unauthenticated Case Brief endpoint.
- Không expose server API key ở frontend.
- Không log secrets.
- Không expose write/action tools.
- Tool server internal auth giữ nguyên.
- Active CIF do application state cung cấp.
- Không cho model tự đổi CIF.

---

# 30. Tool-selection evaluation

Tạo 50–100 utterances.

Targets:

```text
TOOL_SELECTION_ACCURACY >= 90%
WRONG_TOOL_RATE <= 5%
UNNECESSARY_TOOL_RATE <= 15%
MAX_TOOL_CALL_BREACH = 0

DECISION_PARITY = 100%
SCORE_PARITY = 100%

WRONG_CIF = 0
SIMULATION_CONTEXT_LEAK = 0
UNSUPPORTED_DECISION_CLAIM = 0
```

---

# 31. Golden evaluation

Dùng 20 Golden scenarios.

Kiểm:

- đúng CIF;
- đúng score;
- đúng route;
- đúng treatment;
- đúng channel;
- missing-data safe;
- no unsupported fact;
- no raw internal leak;
- simulation state đúng;
- citation hợp lệ.

Có thể structural-validate 3.000 synthetic CIF mà không gọi GLM 3.000 lần.

---

# 32. Business canaries

### SYN002846

```text
route=CALL
treatment=WAIT_SELF_CURE
channel=NONE
score=47
```

Breakdown:

```text
8 / 20
20 / 25
4 / 20
11 / 15
4 / 15
0 / 5
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

---

# 33. Regression scope

Bắt buộc:

- customer page;
- Decision Core canaries;
- simulation;
- Web Copilot;
- auth/session;
- RAG smoke;
- `/app/zalo` smoke.

Không chạy giant unrelated suites nếu source không đổi.

---

# 34. Performance

- Customer page first render không block bởi AI Brief.
- AgentBase path có hard timeout.
- No infinite tool loop.
- Fallback phải hoạt động.

Thu thập:

```text
agent latency
tool latency
GLM latency
total brief latency
cache hit/miss
fallback rate
```

---

# 35. AgentBase availability

```text
AgentBase healthy
→ bounded dynamic orchestration

AgentBase unavailable/timeout
→ static canonical orchestration

GLM unavailable/validation fail
→ deterministic template
```

---

# 36. Public wording

Tên UI:

> **Tóm tắt AI cho hồ sơ**

Public explanation:

> **GreenNode giúp Trợ lý hiểu câu hỏi, thu thập đúng dữ liệu cần thiết và diễn giải kết quả. Bộ máy quyết định vẫn giữ quyền xác định kết quả nghiệp vụ.**

Không public internal planner/tool/fallback terminology.

---

# 37. Demo 30–40 giây

1. Mở CIF.
2. Click `Tóm tắt AI cho hồ sơ`.
3. Brief xuất hiện.
4. Hỏi `Tại sao hôm nay chưa cần gọi?`
5. Hỏi `Nếu tiền vào 7 ngày bằng 0 thì sao?`
6. Chốt:

> **Decision Core quyết định đúng. GreenNode giúp cán bộ hiểu và hành động nhanh hơn.**

---

# 38. Implementation responsibilities

Giữ conventions hiện tại, nhưng responsibility phải tách rõ:

```text
AgentToolRegistry
AgentPlannerAdapter
CaseContextBuilder
CaseBriefGenerator
CaseBriefValidator
CaseBriefFallback
CaseBriefCache
CaseBriefAudit
```

Không nhét toàn bộ vào `tool_server.py`.

---

# 39. API surface

Thêm endpoint theo convention hiện tại, authenticated.

Logical APIs:

```text
generate case brief
follow-up case question
```

Không tạo public endpoint.

Không thay semantics endpoint cũ.

---

# 40. Workflow

```text
INSPECT
→ DESIGN
→ IMPLEMENT
→ UNIT TEST
→ TOOL-SELECTION EVAL
→ GOLDEN EVAL
→ REGRESSION
→ SELF-REVIEW
→ RETEST
→ VERY AUDIT
→ COMMIT
→ DEPLOY
→ PRODUCTION VALIDATION
→ CLOSEOUT
```

---

# 41. Very Audit

Audit:

1. FE architecture unchanged.
2. BE architecture preserved.
3. Decision Core unchanged.
4. Business semantics unchanged.
5. Tool allowlist bounded.
6. No action tools.
7. Tool descriptions match actual behavior.
8. Agent loop bounded.
9. Active CIF safe.
10. Simulation state safe.
11. RAG conditional.
12. Validator blocks contradictions.
13. Fallback works.
14. Customer page survives AI failure.
15. No secret exposure.
16. Existing Zalo unaffected.
17. Existing Web Copilot unaffected.
18. Golden canaries preserved.

Required:

```text
VERY_AUDIT=PASS
```

---

# 42. Task result file

Create:

`task-results/TASK-015-AI-CASE-BRIEF-AGENTBASE-V1-FINAL.md`

Record:

```text
TASK_ID=TASK-015-AI-CASE-BRIEF-AGENTBASE-V1

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

AGENTBASE_BOUNDED=PASS
TOOL_ALLOWLIST=PASS
ACTION_TOOLS_EXPOSED=NO
TOOL_DESCRIPTIONS_AUDITED=PASS

CASE_CONTEXT_BUILDER=PASS
STRUCTURED_OUTPUT=PASS
VALIDATOR=PASS
FALLBACK_LEVEL_1=PASS
FALLBACK_LEVEL_2=PASS
FALLBACK_LEVEL_3=PASS
CACHE_VERSIONING=PASS

TOOL_SELECTION_ACCURACY=<actual>
WRONG_TOOL_RATE=<actual>
UNNECESSARY_TOOL_RATE=<actual>
MAX_TOOL_CALL_BREACH=0

DECISION_PARITY=100%
SCORE_PARITY=100%
WRONG_CIF=0
SIMULATION_CONTEXT_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0

SYN002846=PASS
SYN000746=PASS
BUSINESS_SEMANTICS_DRIFT=0

FRONTEND_TESTS=PASS
BACKEND_RELEVANT_TESTS=PASS
AGENTBASE_TESTS=PASS
GOLDEN_EVAL=PASS

LOCAL_UI_QA=PASS
VERY_AUDIT=PASS

READY_TO_COMMIT=YES/NO
```

---

# 43. Commit

Nếu mọi pre-commit gate PASS:

Suggested message:

`Add bounded AgentBase AI Case Brief`

Không push.

---

# 44. Production deployment

- Backup trước deploy.
- Deploy theo mechanism hiện có.
- Chỉ restart service thực sự cần.
- Không restart unrelated services.
- Không thay DNS/TLS.
- Không thay GreenNode platform config ngoài wiring additive thật sự cần thiết.

---

# 45. Production QA

Tối thiểu:

1. Customer page load bình thường khi AI chưa xong.
2. Generate Brief cho ít nhất 3 CIF khác loại.
3. SYN002846 đúng.
4. Follow-up: score, cashflow, PTP, contact, knowledge, simulation.
5. AgentBase path hoạt động.
6. Forced AgentBase failure → Level 2.
7. Forced GLM/validation failure → Level 3.
8. Switch CIF → clear context.
9. Web Copilot vẫn hoạt động.
10. `/app/zalo` vẫn hoạt động.
11. Session/auth preserved.

Nếu server DNS vẫn intercept, browser QA dùng hostname-preserving DNS pin, không disable TLS verification.

---

# 46. Rollback

Rollback phải đưa hệ thống về pre-TASK-015 mà không ảnh hưởng TASK-013/TASK-014.

Rollback trigger:

- customer page regression;
- business semantic drift;
- Decision parity < 100%;
- wrong CIF;
- simulation context leak;
- auth regression;
- AI failure blocks customer page;
- uncontrolled AgentBase loop;
- secret exposure.

---

# 47. Final closure gates

```text
TASK_015_CLOSED=YES

ARCHITECTURE_PRESERVED=PASS
DECISION_CORE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

AGENTBASE_BOUNDED=PASS
TOOL_ALLOWLIST=PASS
TOOL_DESCRIPTIONS_AUDITED=PASS
ACTION_TOOLS_EXPOSED=NO

TOOL_SELECTION_ACCURACY>=90%
WRONG_TOOL_RATE<=5%
UNNECESSARY_TOOL_RATE<=15%
MAX_TOOL_CALL_BREACH=0

DECISION_PARITY=100%
SCORE_PARITY=100%
WRONG_CIF=0
SIMULATION_CONTEXT_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0

FALLBACK_LEVEL_1=PASS
FALLBACK_LEVEL_2=PASS
FALLBACK_LEVEL_3=PASS

SYN002846=PASS
SYN000746=PASS

APPLICATION_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS

VERY_AUDIT=PASS
ROLLBACK_REQUIRED=NO
PUSH=NO
```

---

# 48. Stop rules

Stop và báo blocker nếu:

- AgentBase runtime/API không support bounded tool orchestration như contract;
- tool schema hiện tại không đủ an toàn và cần đổi business API lớn;
- cần sửa Decision Core;
- cần expose write tools;
- cần thay FE/BE architecture;
- auth/session phải đổi;
- AgentBase trở thành single point of failure;
- decision parity không đạt 100%.

Không lách gate để hoàn thành demo.

---

# 49. Final design principle

> **AgentBase chọn đúng công cụ.  
> Decision Core giữ quyền quyết định.  
> GLM giải thích bằng ngôn ngữ tự nhiên.  
> Validator giữ câu trả lời trung thực.  
> Fallback giữ hệ thống luôn hoạt động.**
