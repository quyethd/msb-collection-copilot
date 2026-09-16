# TASK-017-COPILOT-CONVERSATION-AGENT-QUALITY-V1

## 0. Task identity

**Task ID:** `TASK-017-COPILOT-CONVERSATION-AGENT-QUALITY-V1`  
**Project:** MSB Trợ Lý Thu Hồi Nợ  
**Repository:** `/opt/msb-collection-copilot`  
**Branch:** `master`

**Accepted baseline before TASK-017:**

- TASK-013 Zalo integration: CLOSED
- TASK-014 Landing story/demo: CLOSED
- TASK-015 AI Case Brief + bounded AgentBase: PRODUCTION CLOSED
- TASK-016 Landing pitch refinement: PRODUCTION CLOSED

**Expected starting master HEAD:**

`429adeaf81f1fc884c0c6f15550414d0b5e776e5`

---

# 1. Objective

Nâng chất lượng hội thoại **dùng chung cho Web Copilot và Zalo Bot** để cán bộ có thể hỏi tự nhiên, dùng nhiều cách diễn đạt khác nhau, follow-up ngắn, slang, typo nhẹ và multi-turn mà hệ thống vẫn:

- hiểu đúng intent;
- giữ đúng active CIF;
- không để active CIF chiếm sai global intent;
- giữ đúng topic;
- chọn đúng tool;
- phân biệt đúng case question với knowledge question;
- phân biệt baseline với simulation;
- không làm lệch Decision Core;
- không rơi về generic customer summary khi không hiểu;
- không duplicate;
- không silent/no-response.

Mục tiêu chính:

> **Không bắt người dùng phải nhớ câu demo.**

Và:

> **Web và Zalo phải hiểu cùng một câu hỏi theo cùng một semantic contract.**

TASK-017 **không thay Decision Core** và **không mở quyền cho AI tự quyết định nghiệp vụ**.

---

# 2. Root cause confirmed from real Web + Zalo transcript

Các log thực tế cho thấy đây không chỉ là lỗi Zalo. Web Copilot cũng có lỗi hội thoại tương tự.

## 2.1. Active-CIF hijack — P0

Ví dụ Web:

```text
active_cif = SYN001346

User: hôm nay tao cần làm gì
→ bot trả summary SYN001346

User: điểm của cif đc tính ntn
→ bot trả summary SYN001346

User: alo
→ bot trả summary SYN001346

User: giải thích cách tính điểm
→ bot trả summary SYN001346
```

Đây là lỗi kiến trúc fallback.

Không được có behavior:

```text
UNKNOWN + active_cif
→ CURRENT_CASE_SUMMARY
```

Expected precedence:

```text
1. GREETING / HELP
2. TODAY_WORKLIST / global operational intents
3. Explicit CIF in current message
4. Explicit case intent
5. Pending clarification
6. Last-topic follow-up
7. Bounded AgentBase semantic resolution
8. Explicit generic case-summary request
9. Clarification
10. Safe fallback
```

`active_cif` chỉ là context để hoàn thiện một intent đã xác định, không phải intent mặc định.

Required:

```text
ACTIVE_CIF_HIJACK_RATE=0
```

---

## 2.2. Paraphrase intent quá cứng — P0

Các câu gần nghĩa cho kết quả khác nhau:

```text
Hôm nay tôi phải làm gì
→ TODAY_WORKLIST

Nay tao phải làm gì
→ fallback

Hôm nay tôi cần thao tác gì
→ fallback

Tôi cần làm gì
→ fallback
```

Expected:
resolve cùng intent khi context phù hợp.

---

## 2.3. Follow-up context yếu — P0

Ví dụ:

```text
Bot: Anh/Chị muốn hỏi tiếp về quyết định, dòng tiền hay mô phỏng nào?
User: Quyết định
→ fallback
```

Expected:
resolve qua `pending_clarification`.

---

## 2.4. Topic continuity sai — P0

Ví dụ:

```text
User: CALL là gì
→ knowledge CALL

User: CBS thì sao
→ customer summary do active CIF
```

Expected:
`CBS thì sao` tiếp tục topic `ROUTING_CALL_CBS`.

---

## 2.5. Score routing sai — P0

Ví dụ:

```text
Giải thích SYN001346
Điểm được tính như thế nào
→ RAG evaluation docs
```

Expected:
`SCORE_BREAKDOWN(active_cif)`.

Chỉ khi user nói rõ:

```text
Hệ thống đánh giá AI được chấm thế nào?
```

mới đi evaluation knowledge.

---

## 2.6. Explain-priority yếu — P0

Ví dụ:

```text
Vì sao lại xem SYN000746
Vì sao cần xem SYN001346
Vì sao tao cần xem sny001346
```

Expected:
giải thích why-in-worklist dựa trên score, decision, evidence.

Không chỉ customer summary.

---

## 2.7. Simulation no-change follow-up yếu — P1

Ví dụ:

```text
Nếu có thêm 300tr trong vòng 7 ngày thì sao
→ decision không đổi

Làm sao để thấy thay đổi
→ lặp lại kết quả cũ
```

Expected:
giải thích vì sao không đổi dựa trên canonical precedence/rule evidence.

---

## 2.8. Ambiguous hypothetical xử lý kém — P1

Ví dụ:

```text
Khách không trả nợ thì sao
```

Không trả generic summary.

Expected clarification:

> Anh/Chị muốn mô phỏng khách không thực hiện cam kết hiện tại, hay hỏi quy trình xử lý chung?

---

## 2.9. Duplicate / no-response — P0

Transcript có dấu hiệu:

- nhiều response gần giống cho một câu;
- một số câu không có response;
- reconnect/pairing không ổn định.

Inspect:

```text
update_id
message_id
polling cursor
dedupe cache
retry/outbox
worker restart
pairing state
```

Không coi mọi lỗi là NLU.

---

## 2.10. Raw enum leak — P0

Ví dụ:

```text
Cam kết thanh toán: OPEN
```

Public response phải map:

```text
OPEN       → Đang mở
KEPT       → Đã thực hiện
PARTIAL    → Thanh toán một phần
BROKEN     → Không thực hiện cam kết
EXPIRED    → Hết hạn
CANCELLED  → Đã hủy
NONE       → Chưa có cam kết
```

Required:

```text
RAW_ENUM_LEAK=0
```

---

## 2.11. Web SVG/text rendering leak — P1

Nếu Web chat thực sự hiển thị text như:

```text
svgTrợ lý Thu hồi Nợ
```

thì phải inspect renderer/accessibility/copy extraction.

Required:

```text
WEB_CHAT_SVG_TEXT_LEAK=0
```

Nếu chỉ xuất hiện do browser copy semantics mà không hiển thị visual thì document evidence và không sửa mù quáng.

---

# 3. Architectural principle

Giữ kiến trúc FE + BE hiện tại.

Không refactor toàn bộ hệ thống sang một conversation framework mới.

Target semantic architecture:

```text
                 User
                  │
         ┌────────┴────────┐
         │                 │
        Web               Zalo
         │                 │
         └────────┬────────┘
                  ↓
       Shared Semantic Contract
                  ↓
      Text normalization / state
                  ↓
 High-confidence deterministic resolver
                  ↓ nếu chưa đủ chắc
      Bounded AgentBase resolution
                  ↓
       Approved read/compute tools
                  ↓
 Facts / Decision / Simulation / Knowledge
                  ↓
       Response truth validator
                  ↓
         Channel formatter only
         ├─ Web
         └─ Zalo
```

Nếu Web và Zalo đang dùng router implementation khác nhau:
- không bắt buộc refactor lớn;
- nhưng phải đạt **semantic parity** qua shared contract/tests.

---

# 4. Authority hierarchy

```text
1. Decision Core
2. Canonical business facts
3. Simulation Core
4. Grounded knowledge
5. Conversation state
6. AgentBase tool planner
7. GLM wording
8. Channel formatter
```

AgentBase không được:

- thay route;
- thay score;
- thay treatment;
- thay channel;
- tự tạo PTP;
- tự gọi khách;
- override Decision Core;
- thực hiện write/outbound actions.

---

# 5. Scope

## Bao gồm

- Web Copilot conversation quality.
- Zalo conversation quality.
- Shared semantic contract.
- Message normalization.
- Intent/paraphrase quality.
- Follow-up resolution.
- Topic continuity.
- Active CIF safety.
- Pending clarification.
- Today-worklist.
- Priority explanation.
- Score explanation.
- Case-vs-knowledge disambiguation.
- Simulation follow-up explanation.
- Bounded AgentBase semantic/tool resolution.
- Response formatter labels.
- Duplicate protection.
- No-response reliability.
- Pairing/reconnect diagnostics cho Zalo nếu cần.
- Web/Zalo parity tests.
- Real transcript replay.
- Auto-generated paraphrase tests.
- Multi-turn tests.
- Adversarial/state tests.
- Production Web + Zalo validation.

## Không bao gồm

- New Decision Core rules.
- New score formula.
- New routing logic.
- New NBA rule.
- New PTP semantics.
- New Zalo transport architecture.
- Landing changes.
- New frontend architecture.
- Customer-facing collection bot.
- Outbound call/SMS/email automation.
- New ML model.
- Agent action/write tools.

---

# 6. Conversation state model

State tối thiểu:

```text
active_cif
last_intent
last_topic
last_decision
last_simulation
pending_clarification
last_worklist
last_tool_context
last_response_kind
last_message_id
channel
```

Rules:

- `active_cif` chỉ đổi khi user nói rõ CIF hợp lệ hoặc flow canonical chọn CIF.
- đổi CIF → clear case-local follow-up/simulation.
- `last_topic` được ưu tiên cho follow-up knowledge ngắn.
- `pending_clarification` được ưu tiên khi user trả lời một từ/ngắn.
- greeting/global intent không bị active CIF hijack.
- reconnect/chat isolation không được trộn context.

---

# 7. Intent precedence — P0 contract

Resolver precedence bắt buộc:

```text
1. GREETING / HELP
2. TODAY_WORKLIST / GLOBAL_OPERATIONAL
3. EXPLICIT_CIF_IN_MESSAGE
4. EXPLICIT_CASE_INTENT
5. PENDING_CLARIFICATION
6. LAST_TOPIC_FOLLOWUP
7. BOUNDED_AGENTBASE_SEMANTIC_RESOLUTION
8. EXPLICIT_GENERIC_CASE_SUMMARY
9. CLARIFICATION
10. SAFE_FALLBACK
```

Không dùng:

```text
UNKNOWN + active_cif
→ CURRENT_CASE_SUMMARY
```

---

# 8. Text normalization

Support:

- lowercase/case-insensitive;
- trim;
- punctuation;
- slang;
- typo nhẹ;
- viết tắt;
- no-diacritic variants nếu an toàn;
- common Vietnamese chat shorthand.

Ví dụ:

```text
hôm nay tôi phải làm gì
nay tao phải làm gì
hôm nay tôi cần thao tác gì
tôi cần làm gì
nay làm gì
việc hôm nay?
hôm nay ưu tiên gì
hnay làm j
```

CIF typo:

```text
sny001346
```

Có thể correct khi:
- confidence cao;
- unique nearest valid CIF.

Nếu mơ hồ:
clarify.

---

# 9. Canonical intent coverage

Tối thiểu:

```text
GREETING
HELP
TODAY_WORKLIST
CURRENT_CASE_SUMMARY
CURRENT_CASE_ACTION
EXPLAIN_PRIORITY
EXPLAIN_DECISION
SCORE_VALUE
SCORE_BREAKDOWN
CASHFLOW
PTP
CONTACT_HISTORY
KNOWLEDGE
SIMULATION
SIMULATION_EXPLANATION
CLARIFICATION_RESPONSE
ACTIVE_CIF_QUERY
RETURN_TO_BASELINE
UNKNOWN
```

Không cần rename enum hiện tại nếu semantics tương đương.

---

# 10. TODAY_WORKLIST behavior

Các câu sau phải resolve cùng intent:

```text
Hôm nay tao phải làm gì
Nay tao phải làm gì
Hôm nay tôi phải làm gì
Hôm nay tôi cần thao tác gì
Tôi cần làm gì
Có việc gì cần xử lý hôm nay
Hôm nay ưu tiên gì
Việc hôm nay?
hnay làm j
```

Ngay cả khi:

```text
active_cif=SYN001346
```

thì vẫn phải là TODAY_WORKLIST.

Expected response:

- tổng số hồ sơ có decision;
- số CALL nhưng chưa cần gọi ngay;
- top CIF;
- score/action nếu payload support;
- không nói “đã có trong bảng tin sáng” nếu hệ thống có data trực tiếp.

---

# 11. Active-CIF hijack regression

Với:

```text
active_cif=SYN001346
```

các câu:

```text
alo
xin chào
hôm nay tôi phải làm gì
CALL là gì
CBS thì sao
điểm được tính như thế nào
```

phải resolve theo đúng intent tương ứng.

Không câu nào được tự động thành CURRENT_CASE_SUMMARY trừ khi user nói:

```text
tóm tắt khách này
khách này thế nào
cho tôi xem tình trạng khách này
```

Required:

```text
ACTIVE_CIF_HIJACK_RATE=0
GENERIC_SUMMARY_FALLBACK_RATE<=1%
```

---

# 12. EXPLAIN_PRIORITY behavior

Support:

```text
Vì sao lại xem SYN000746
Vì sao cần xem SYN001346
Vì sao tao cần xem SYN001346
Tại sao khách này nằm top hôm nay
Vì sao phải ưu tiên hồ sơ này
```

Expected:

- CIF;
- score;
- current decision;
- key evidence;
- worklist/priority reason nếu canonical source có.

Không invent ranking reason.

---

# 13. Score behavior

## SCORE_VALUE

```text
điểm bao nhiêu
điểm khách này
score khách này
```

→ canonical score.

## SCORE_BREAKDOWN

```text
điểm được tính thế nào
điểm của cif đc tính ntn
điểm tính dựa trên gì
giải thích cách tính điểm
vì sao điểm chỉ 69
khả năng thanh toán 24 điểm vì sao
```

Nếu active CIF:
→ score breakdown của CIF.

Không route vào evaluation corpus.

Evaluation knowledge chỉ dùng khi user nói rõ:

```text
bộ test đánh giá hệ thống
evaluation
hệ thống AI được chấm như thế nào
```

---

# 14. Knowledge-topic continuity

Sequence:

```text
CALL là gì
→ knowledge CALL

CBS thì sao
→ knowledge CBS

Khác nhau ở đâu
→ compare CALL/CBS
```

`active_cif` không được giành intent.

---

# 15. Clarification behavior

Ví dụ:

```text
Khách không trả nợ thì sao
```

Expected:

> Anh/Chị muốn mô phỏng khách không thực hiện cam kết hiện tại, hay hỏi quy trình xử lý chung?

Nếu user trả:

```text
mô phỏng
quyết định
quy trình
```

resolve từ `pending_clarification`.

Không fallback.

---

# 16. Simulation follow-up

Support:

```text
Nếu tiền vào 7 ngày bằng 0 thì sao
→ simulation

Thế giờ làm gì
→ after-state action

Vì sao lại đổi
→ explain after-state

Làm sao để thấy thay đổi
→ explain no-change / supported factors

Quay lại dữ liệu thật
→ baseline
```

Nếu simulation no-change:
giải thích theo canonical precedence/rule evidence.

Không bịa unsupported simulation variable.

---

# 17. AgentBase use

AgentBase chỉ dùng khi deterministic resolver/context chưa đủ chắc.

Bounds:

```text
MAX_TOOL_CALLS <= 5
MAX_PLANNING_ROUNDS <= 2
MAX_RAG_CALLS <= 1
MAX_SIMULATION_CALLS <= 1
```

Chỉ approved read/compute tools.

No write/action tools.

AgentBase được:

- resolve ambiguous semantic intent;
- choose minimum relevant tools;
- use active CIF only after intent is identified;
- maintain follow-up context.

---

# 18. Tool descriptions

Reuse TASK-015 tool registry/descriptions nếu có thể.

Không fork bộ tool descriptions khác cho Web/Zalo nếu không cần.

Audit để phân biệt:

- case score vs evaluation score;
- decision vs knowledge;
- simulation vs current state;
- PTP vs generic summary;
- contact history vs current action;
- today worklist vs active case.

---

# 19. Response composition

Persona thống nhất:

- hiểu slang;
- không mirror slang thô;
- ngắn;
- nghiệp vụ;
- phù hợp Web và Zalo.

Preferred:

- user address: `Anh/Chị`
- bot: `tôi` / `Trợ lý`

Không mix tùy tiện:

```text
tao
bạn
Anh/Chị
```

Raw enum phải map sang public label.

---

# 20. Public enum mapping

Ít nhất PTP:

```text
OPEN       → Đang mở
KEPT       → Đã thực hiện
PARTIAL    → Thanh toán một phần
BROKEN     → Không thực hiện cam kết
EXPIRED    → Hết hạn
CANCELLED  → Đã hủy
NONE       → Chưa có cam kết
```

Tương tự các raw enum khác nếu đang leak.

Required:

```text
RAW_ENUM_LEAK=0
```

---

# 21. Duplicate-response protection

Inspect:

```text
message_id
update_id
polling offset/cursor
dedupe key
dedupe TTL
retry
outbox
worker restart
network retry
```

Required:

```text
DUPLICATE_RESPONSE_RATE=0
```

---

# 22. No-response reliability

Trong supported scope mỗi inbound phải:

- answer;
- clarification;
- safe fallback;

không silent.

Required:

```text
NO_RESPONSE_RATE=0
```

---

# 23. Web/Zalo semantic parity

Cùng:

- message;
- active CIF;
- conversation state;

Web và Zalo phải resolve cùng semantic intent và canonical business result.

Channel formatter có thể khác wording/format.

Required:

```text
WEB_ZALO_INTENT_PARITY >= 98%
WEB_ZALO_DECISION_PARITY = 100%
WEB_ZALO_SCORE_PARITY = 100%
```

---

# 24. Real Web Regression Corpus

Seed tối thiểu:

```text
active_cif=SYN001346

hôm nay tao cần làm gì
→ TODAY_WORKLIST

điểm của cif đc tính ntn
→ SCORE_BREAKDOWN

alo
→ GREETING

xin chào
→ GREETING

giải thích cách tính điểm
→ SCORE_BREAKDOWN
```

Required:

```text
WEB_REAL_TRANSCRIPT_REPLAY=PASS
```

---

# 25. Real Zalo Regression Corpus

Seed tối thiểu:

```text
Alo
Nay tao phải làm gì
Hôm nay tao phải làm gì
Hôm nay tôi phải làm gì
Hôm nay tôi cần thao tác gì
Tôi cần làm gì

Giải thích cif: syn001346
Điểm được tính như thế nào
Tao đang thao tác với cif nào
Giải thích cách tính điểm

Nếu có thêm 300 tr trong vòng 7 ngày thì sao
Khách không trả nợ thì sao

Vì sao lại xem syn000746
Vì sao cần xem syn001346
Vì sao tao cần xem sny001346
Quyết định
Vì sao cần xem cif của ngày hôm nay
Hỏi về quyết định
Tao nói thế nào mày mới hiểu

Cách tính điểm của cif syn000746
Điểm tính dựa trên gì

Call là gì
Cbs thì sao
Khác nhau giữa call + cbs

Nếu có tiền vào trong 7 ngày thì cần làm gì
Làm sao để thấy thay đổi
```

Required:

```text
ZALO_REAL_TRANSCRIPT_REPLAY=PASS
```

---

# 26. Auto-generated paraphrase evaluation

Sinh ít nhất khoảng:

```text
300–500 utterances
```

nếu practical.

Các nhóm:

- formal;
- casual;
- slang;
- typo nhẹ;
- không dấu;
- viết tắt;
- short fragments;
- reordered wording;
- active-CIF present;
- global intent while active-CIF present;
- follow-up fragment.

Expected intent kế thừa canonical seed.

Không để generator tự sửa expected label.

---

# 27. Multi-turn evaluation

## A. Knowledge continuity

```text
CALL là gì
CBS thì sao
Khác nhau ở đâu
```

## B. Active CIF score

```text
Giải thích SYN001346
Điểm bao nhiêu
Điểm dựa trên gì
Khả năng thanh toán 24 điểm vì sao
```

## C. Simulation

```text
Giải thích SYN002846
Nếu tiền vào 7 ngày bằng 0 thì sao
Thế giờ làm gì
Vì sao lại đổi
Quay lại dữ liệu thật
```

## D. Clarification

```text
Khách không trả nợ thì sao
Mô phỏng
```

## E. Switch CIF

```text
Giải thích SYN001346
Điểm bao nhiêu
Chuyển sang SYN000746
Điểm bao nhiêu
```

## F. Active CIF global intent

```text
Giải thích SYN001346
Alo
Hôm nay tôi phải làm gì
CALL là gì
```

None may fallback to SYN001346 summary.

---

# 28. Adversarial/state evaluation

Test:

- typo CIF;
- nonexistent CIF;
- duplicate message/update;
- delayed retry;
- reconnect;
- AgentBase timeout;
- RAG timeout;
- simulation no-change;
- simulation then CIF switch;
- greeting after active CIF;
- global intent after active CIF;
- knowledge topic after active CIF;
- one-word clarification;
- repeated `Alo`;
- Web/Zalo same query parity.

---

# 29. Metrics / gates

Required:

```text
IN_SCOPE_INTENT_ACCURACY >= 95%
PARAPHRASE_INTENT_ACCURACY >= 95%
FOLLOWUP_RESOLUTION_ACCURACY >= 95%

IN_SCOPE_FALLBACK_RATE <= 3%
GENERIC_SUMMARY_FALLBACK_RATE <= 1%

ACTIVE_CIF_HIJACK_RATE = 0

WRONG_TOOL_RATE <= 3%
UNNECESSARY_TOOL_RATE <= 15%

WRONG_CIF = 0
CROSS_CIF_CONTEXT_LEAK = 0
SIMULATION_CONTEXT_LEAK = 0

DUPLICATE_RESPONSE_RATE = 0
NO_RESPONSE_RATE = 0

DECISION_PARITY = 100%
SCORE_PARITY = 100%

RAW_ENUM_LEAK = 0
WEB_CHAT_SVG_TEXT_LEAK = 0
UNSUPPORTED_DECISION_CLAIM = 0
MAX_TOOL_CALL_BREACH = 0

WEB_ZALO_INTENT_PARITY >= 98%
WEB_ZALO_DECISION_PARITY = 100%
WEB_ZALO_SCORE_PARITY = 100%

WEB_REAL_TRANSCRIPT_REPLAY = PASS
ZALO_REAL_TRANSCRIPT_REPLAY = PASS
```

---

# 30. Business canaries

Preserve:

### SYN002846

```text
route=CALL
treatment=WAIT_SELF_CURE
channel=NONE
score=47
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

Use current canonical fixture as source of truth.

Không hardcode transcript values nếu fixture hiện tại khác.

---

# 31. Regression scope

Run:

- Web Copilot conversation tests;
- Zalo conversation tests;
- AgentBase planner;
- shared semantic resolver;
- tool selection;
- Decision canaries;
- simulation;
- RAG knowledge;
- auth/session;
- dedupe;
- `/app/zalo` UI smoke;
- customer page smoke.

TASK-016 landing must remain untouched.

---

# 32. Source scope

Allowed:

- shared conversation semantics;
- Web Copilot router/adapter;
- Zalo conversation router/adapter;
- conversation state;
- normalization;
- AgentBase semantic adapter;
- shared tool registry only if backward-compatible;
- response formatter/enum mapping;
- tests/evals;
- task report.

Do not change:

- landing;
- Decision Core business logic;
- score formula;
- routing;
- NBA;
- PTP semantics;
- simulation core;
- frontend architecture;
- Zalo transport architecture unless fixing a proven reliability bug with minimal scope.

Required:

```text
TASK016_LANDING_CHANGED=NO
DECISION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0
```

---

# 33. Workflow

```text
INSPECT
→ REPRODUCE WEB + ZALO FAILURES
→ ROOT-CAUSE CLASSIFY
→ ADD FAILING REGRESSION TESTS
→ DESIGN SHARED SEMANTIC CONTRACT
→ IMPLEMENT
→ AUTO-GENERATE PARAPHRASE TESTS
→ MULTI-TURN TESTS
→ PARITY TESTS
→ ADVERSARIAL TESTS
→ METRICS
→ SELF-REVIEW
→ RETEST
→ VERY AUDIT
→ COMMIT
→ BACKUP
→ DEPLOY
→ WEB PRODUCTION QA
→ LIVE ZALO ROUNDTRIP
→ CLOSEOUT
```

---

# 34. Test-first rule

Mỗi bug transcript:

1. reproduce;
2. failing regression;
3. fix;
4. rerun;
5. keep test.

Không chỉ tune prompt thủ công đến khi một câu demo chạy.

---

# 35. Very Audit

Verify:

1. Decision Core unchanged.
2. Business semantics unchanged.
3. TASK-016 landing unchanged.
4. Active-CIF hijack = 0.
5. Web/Zalo semantic parity.
6. AgentBase bounded.
7. No action tools.
8. CIF/chat isolation.
9. Simulation isolation.
10. Knowledge continuity.
11. Duplicate protection.
12. No silent response.
13. Score routing.
14. Priority explanation.
15. Clarification.
16. Raw enum mapping.
17. Web SVG text leak.
18. Real Web replay.
19. Real Zalo replay.
20. Metrics meet gates.

Required:

```text
VERY_AUDIT=PASS
```

---

# 36. Task report

Create:

`task-results/TASK-017-COPILOT-CONVERSATION-AGENT-QUALITY-V1-FINAL.md`

Record:

```text
TASK_ID=TASK-017-COPILOT-CONVERSATION-AGENT-QUALITY-V1

PREVIOUS_HEAD=<actual>
TASK017_COMMIT=<sha>

TASK016_LANDING_CHANGED=NO
DECISION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

WEB_REAL_TRANSCRIPT_REPLAY=PASS
ZALO_REAL_TRANSCRIPT_REPLAY=PASS

IN_SCOPE_INTENT_ACCURACY=<actual>
PARAPHRASE_INTENT_ACCURACY=<actual>
FOLLOWUP_RESOLUTION_ACCURACY=<actual>

IN_SCOPE_FALLBACK_RATE=<actual>
GENERIC_SUMMARY_FALLBACK_RATE=<actual>
ACTIVE_CIF_HIJACK_RATE=0

WRONG_TOOL_RATE=<actual>
UNNECESSARY_TOOL_RATE=<actual>

WEB_ZALO_INTENT_PARITY=<actual>
WEB_ZALO_DECISION_PARITY=100%
WEB_ZALO_SCORE_PARITY=100%

WRONG_CIF=0
CROSS_CIF_CONTEXT_LEAK=0
SIMULATION_CONTEXT_LEAK=0

DUPLICATE_RESPONSE_RATE=0
NO_RESPONSE_RATE=0

DECISION_PARITY=100%
SCORE_PARITY=100%

RAW_ENUM_LEAK=0
WEB_CHAT_SVG_TEXT_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0
MAX_TOOL_CALL_BREACH=0

WEB_COPILOT_TESTS=PASS
ZALO_TESTS=PASS
AGENTBASE_TESTS=PASS
RAG_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS

VERY_AUDIT=PASS

READY_TO_DEPLOY=YES/NO
```

---

# 37. Commit

If all pre-deploy gates pass:

Suggested commit:

`Improve shared Copilot conversation quality`

No push.

---

# 38. Production deployment

Before deploy:

- backup;
- record rollback point.

Deploy only required TASK-017 changes.

Restart only services actually required.

Do not redeploy landing.

Do not restart unrelated services.

---

# 39. Production Web QA

Test in real authenticated Web Copilot:

```text
active_cif=SYN001346

hôm nay tao cần làm gì
điểm của cif đc tính ntn
alo
xin chào
giải thích cách tính điểm
```

Required:

```text
PRODUCTION_WEB_REAL_REPLAY=PASS
PRODUCTION_ACTIVE_CIF_HIJACK_RATE=0
PRODUCTION_RAW_ENUM_LEAK=0
PRODUCTION_WEB_CHAT_SVG_TEXT_LEAK=0
```

---

# 40. Production Zalo live roundtrip

Real Zalo sequence:

```text
Xin chào

Nay tao phải làm gì

Vì sao cần xem SYN001346

Điểm tính dựa trên gì

CALL là gì

CBS thì sao

Khác nhau ở đâu

Giải thích SYN002846

Nếu tuần này không có tiền vào thì sao

Thế giờ làm gì

Quay lại dữ liệu thật

Khách không trả nợ thì sao
```

Required:

```text
PRODUCTION_ZALO_LIVE_ROUNDTRIP=PASS
```

---

# 41. Production parity

Use at least 5 matched questions on Web and Zalo with equivalent context.

Required:

```text
PRODUCTION_WEB_ZALO_INTENT_PARITY>=98%
PRODUCTION_WEB_ZALO_DECISION_PARITY=100%
PRODUCTION_WEB_ZALO_SCORE_PARITY=100%
```

---

# 42. Production reliability

Required:

```text
PRODUCTION_DUPLICATE_RESPONSE_RATE=0
PRODUCTION_NO_RESPONSE_RATE=0
PRODUCTION_WRONG_CIF=0
PRODUCTION_CONTEXT_LEAK=0
PRODUCTION_SIMULATION_CONTEXT_LEAK=0
PRODUCTION_UNSUPPORTED_DECISION_CLAIM=0
```

---

# 43. Rollback triggers

Rollback if:

- Decision parity < 100%;
- score parity < 100%;
- active-CIF hijack persists;
- wrong CIF;
- context leak;
- duplicate response;
- no-response;
- AgentBase exceeds bounds;
- pairing breaks;
- Web Copilot regression;
- auth/security regression;
- business semantics drift.

Rollback must preserve TASK-013 through TASK-016.

---

# 44. Final closeout gates

```text
TASK_017_CLOSED=YES

WEB_REAL_TRANSCRIPT_REPLAY=PASS
ZALO_REAL_TRANSCRIPT_REPLAY=PASS

IN_SCOPE_INTENT_ACCURACY>=95%
PARAPHRASE_INTENT_ACCURACY>=95%
FOLLOWUP_RESOLUTION_ACCURACY>=95%

IN_SCOPE_FALLBACK_RATE<=3%
GENERIC_SUMMARY_FALLBACK_RATE<=1%
ACTIVE_CIF_HIJACK_RATE=0

WRONG_TOOL_RATE<=3%
UNNECESSARY_TOOL_RATE<=15%

WEB_ZALO_INTENT_PARITY>=98%
WEB_ZALO_DECISION_PARITY=100%
WEB_ZALO_SCORE_PARITY=100%

WRONG_CIF=0
CROSS_CIF_CONTEXT_LEAK=0
SIMULATION_CONTEXT_LEAK=0

DUPLICATE_RESPONSE_RATE=0
NO_RESPONSE_RATE=0

DECISION_PARITY=100%
SCORE_PARITY=100%

RAW_ENUM_LEAK=0
WEB_CHAT_SVG_TEXT_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0
MAX_TOOL_CALL_BREACH=0

PRODUCTION_WEB_REAL_REPLAY=PASS
PRODUCTION_ZALO_LIVE_ROUNDTRIP=PASS

TASK016_LANDING_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

VERY_AUDIT=PASS
ROLLBACK_REQUIRED=NO
PUSH=NO
```

---

# 45. Final principle

> **Hiểu linh hoạt hơn, nhưng quyết định không tự do hơn.**

> **Active CIF là context, không phải fallback intent.**

> **Web và Zalo phải hiểu cùng một câu hỏi theo cùng một semantic contract.**

> **AgentBase giúp resolve ngôn ngữ và chọn đúng công cụ; Decision Core vẫn giữ quyền quyết định nghiệp vụ.**
