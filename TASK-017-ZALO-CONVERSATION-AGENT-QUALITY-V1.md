# TASK-017-ZALO-CONVERSATION-AGENT-QUALITY-V1

## 0. Task identity

**Task ID:** `TASK-017-ZALO-CONVERSATION-AGENT-QUALITY-V1`  
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

Nâng chất lượng hội thoại của **Bot Trợ lý Thu hồi Nợ - MSB trên Zalo** để cán bộ có thể hỏi tự nhiên hơn, dùng nhiều cách diễn đạt khác nhau, follow-up ngắn, slang, typo nhẹ và multi-turn mà bot vẫn hiểu đúng ý, giữ đúng CIF/ngữ cảnh, chọn đúng công cụ và không làm lệch Decision Core.

Mục tiêu chính:

> **Không bắt người dùng phải nhớ câu demo.**

Bot phải chuyển từ:

> “hiểu tốt các câu đã dự kiến”

sang:

> **“hiểu được nhiều cách nói tự nhiên trong phạm vi nghiệp vụ đã cho phép.”**

TASK-017 **không thay Decision Core** và **không mở quyền cho AI tự quyết định nghiệp vụ**.

---

# 2. Root-cause hypothesis từ transcript thực tế

## 2.1. Paraphrase intent quá cứng — P0

Các câu gần nghĩa nhưng kết quả khác nhau:

```text
Hôm nay tôi phải làm gì
→ hiểu TODAY_WORKLIST

Nay tao phải làm gì
→ fallback

Hôm nay tôi cần thao tác gì
→ fallback

Tôi cần làm gì
→ fallback
```

Yêu cầu:
mọi cách nói tương đương phải resolve cùng intent khi context phù hợp.

## 2.2. Follow-up context yếu — P0

```text
Bot: Anh/Chị muốn hỏi tiếp về quyết định, dòng tiền hay mô phỏng nào?
User: Quyết định
→ bot fallback
```

Bot phải dùng `pending_clarification` hoặc `last_topic` để hiểu câu trả lời ngắn.

## 2.3. Topic continuity sai — P0

```text
User: Call là gì
Bot: giải thích CALL

User: Cbs thì sao
Bot: trả customer summary của active CIF
```

Expected:
`CBS thì sao` phải tiếp tục topic `ROUTING_CALL_CBS`, không bị active CIF override.

## 2.4. Score-related routing sai — P0

```text
User: Giải thích cif SYN001346
User: Điểm được tính như thế nào
→ bot đi RAG vào tài liệu đánh giá 40 câu hỏi
```

Trong active-CIF context, câu này phải ưu tiên score breakdown của CIF.

Chỉ câu như:

```text
Hệ thống đánh giá AI được chấm thế nào?
```

mới đi evaluation knowledge.

## 2.5. Explain-priority yếu — P0

```text
Vì sao lại xem SYN000746
Vì sao cần xem SYN001346
Vì sao tao cần xem sny001346
Vì sao cần xem cif của ngày hôm nay
```

Expected:
giải thích vì sao CIF nằm trong worklist/priority today dựa trên canonical score/decision/evidence.

## 2.6. Simulation no-change follow-up yếu — P1

```text
Nếu có thêm 300 tr trong vòng 7 ngày thì sao
→ decision không đổi

Làm sao để thấy thay đổi
→ bot lặp lại đúng kết quả cũ
```

Expected:
giải thích vì sao không đổi và nếu engine hỗ trợ thì gợi ý 1–2 biến giả định có ý nghĩa hơn, không tự bịa rule.

## 2.7. Ambiguous hypothetical xử lý kém — P1

```text
Khách không trả nợ thì sao
```

Không nên trả customer summary.

Nếu ambiguity thực sự còn tồn tại, bot nên hỏi clarification có ích:

> “Anh/Chị muốn mô phỏng khách không thực hiện cam kết hiện tại, hay hỏi quy trình xử lý chung?”

## 2.8. Duplicate / no-response — P0

Transcript có dấu hiệu:

- cùng một câu knowledge có nhiều response lặp;
- một số câu không thấy response;
- có tình huống pairing/reconnect bị lỗi.

TASK-017 phải inspect riêng:

```text
update_id
message_id
polling cursor
dedupe cache
retry/outbox
worker restart
pairing state
```

Không được coi mọi lỗi là NLU.

---

# 3. Architectural principle

Giữ kiến trúc hiện tại.

```text
Incoming Zalo message
        ↓
Text normalization
        ↓
Conversation state
        ↓
High-confidence deterministic resolver
        ↓ nếu chưa đủ chắc
Bounded AgentBase
        ↓
Minimum approved tool selection
        ↓
Existing canonical business tools
        ↓
Decision / Simulation / Knowledge
        ↓
Response composition
        ↓
Decision/fact/context validator
        ↓
Dedup / delivery guard
        ↓
Zalo
```

Không thay transport architecture nếu không có blocker thật.

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
```

AgentBase không được:

- thay route;
- thay score;
- thay treatment;
- thay channel;
- tự tạo PTP;
- tự gọi khách;
- override Decision Core.

---

# 5. Scope

## Bao gồm

- Zalo message normalization.
- Intent/paraphrase quality.
- Follow-up resolution.
- Topic continuity.
- Active CIF memory.
- Pending clarification state.
- Today-worklist understanding.
- Priority explanation.
- Score explanation.
- Knowledge-vs-case disambiguation.
- Simulation follow-up explanation.
- AgentBase bounded fallback/planning.
- Tool-selection quality.
- Duplicate update protection.
- No-response reliability.
- Pairing/reconnect diagnostics nếu liên quan.
- Real transcript replay tests.
- Auto-generated paraphrase tests.
- Multi-turn tests.
- Adversarial/state tests.
- Production Zalo live roundtrip validation.

## Không bao gồm

- New Decision Core rules.
- New score formula.
- New routing logic.
- New NBA rule.
- New PTP semantics.
- New Zalo transport architecture.
- New frontend feature.
- Customer-facing collection bot.
- Outbound call/SMS/email automation.
- Landing changes.
- New ML model.

---

# 6. Conversation state model

Conversation state tối thiểu:

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
```

Rules:

- `active_cif` chỉ đổi khi user nói rõ CIF hợp lệ hoặc flow canonical đã chọn CIF.
- đổi CIF → clear case-local follow-up/simulation context.
- `last_topic` không được bị active CIF overwrite nếu follow-up ngắn đang rõ nghĩa.
- `pending_clarification` phải ưu tiên khi user trả lời một từ/ngắn.
- reconnect không được tự trộn context của chat khác.

---

# 7. Text normalization

Normalization phải hỗ trợ:

- lowercase/case-insensitive;
- trim whitespace;
- dấu câu;
- slang phổ biến;
- typo nhẹ;
- viết tắt;
- có dấu/không dấu nếu implementation hiện tại support được an toàn.

Ví dụ cần hiểu tương đương:

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

Không được normalize CIF sai.

Ví dụ typo:

```text
sny001346
```

Có thể correction khi confidence cao và chỉ có một CIF gần nhất hợp lệ.

Nếu mơ hồ:
clarify, không tự chọn.

---

# 8. Canonical intent coverage

Tối thiểu phải cover:

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
UNKNOWN
```

Không bắt buộc rename enum hiện tại nếu codebase đã có canonical names khác.

---

# 9. TODAY_WORKLIST behavior

Các câu sau phải resolve cùng intent khi không có case-local follow-up mạnh hơn:

```text
Hôm nay tao phải làm gì
Nay tao phải làm gì
Hôm nay tôi phải làm gì
Hôm nay tôi cần thao tác gì
Tôi cần làm gì
Có việc gì cần xử lý hôm nay
Hôm nay ưu tiên gì
Việc hôm nay?
```

Expected response:

- số hồ sơ có quyết định;
- số hồ sơ CALL nhưng chưa cần gọi ngay;
- top priority CIF;
- mỗi CIF nên có score/action ngắn nếu payload support;
- không nói “đã có trong bảng tin sáng” nếu bot có dữ liệu trực tiếp.

---

# 10. EXPLAIN_PRIORITY behavior

Queries:

```text
Vì sao lại xem SYN000746
Vì sao cần xem SYN001346
Vì sao tao cần xem SYN001346
Tại sao khách này nằm top hôm nay
Vì sao phải ưu tiên hồ sơ này
```

Expected:

- identify CIF;
- current score;
- current decision;
- key evidence;
- reason it is in today list.

Không chỉ trả customer summary.

Không invent ranking reason nếu worklist source không cung cấp.

---

# 11. Score conversation

## SCORE_VALUE

```text
điểm bao nhiêu
điểm khách này
score của khách này
```

→ canonical score.

## SCORE_BREAKDOWN

```text
điểm được tính thế nào
điểm tính dựa trên gì
vì sao điểm chỉ 69
khả năng thanh toán sao được 24 điểm
```

Nếu active CIF tồn tại:
ưu tiên score breakdown của CIF.

Không route vào evaluation corpus.

---

# 12. Knowledge-topic continuity

Ví dụ:

```text
CALL là gì
→ knowledge CALL

CBS thì sao
→ knowledge CBS

khác nhau ở đâu
→ compare CALL/CBS
```

`active_cif` không được giành intent trong chuỗi này.

---

# 13. Clarification behavior

Clarification là hành vi hợp lệ khi ambiguity thật.

Ví dụ:

```text
Khách không trả nợ thì sao
```

Expected:

> Anh/Chị muốn:
> 1. mô phỏng khách không thực hiện cam kết hiện tại, hay
> 2. hỏi quy trình xử lý chung?

Nếu user trả:

```text
Quyết định
```

hoặc:

```text
mô phỏng
```

bot phải resolve từ `pending_clarification`, không fallback.

---

# 14. Simulation follow-up

Simulation flow phải support:

```text
Nếu tiền vào 7 ngày bằng 0 thì sao
→ simulation

thế giờ làm gì
→ after-state action

vì sao lại đổi
→ explain simulation

làm sao để thấy thay đổi
→ explain no-change or suggest supported variables

quay lại dữ liệu thật
→ baseline
```

Nếu simulation không đổi:
bot phải giải thích dựa trên canonical precedence/rule evidence hiện có.

Không tự bịa hypothetical unsupported by Simulation Core.

---

# 15. AgentBase use

AgentBase chỉ dùng khi deterministic resolver/context không đủ chắc.

Boundaries:

```text
MAX_TOOL_CALLS <= 5
MAX_PLANNING_ROUNDS <= 2
MAX_RAG_CALLS <= 1
MAX_SIMULATION_CALLS <= 1
```

AgentBase chỉ thấy existing approved read/compute tools.

Không expose action tools.

---

# 16. Tool descriptions

Audit tool descriptions reused from TASK-015.

Nếu Zalo orchestration dùng cùng tool registry thì reuse.

Không fork tool descriptions thành một bộ khác nếu không cần.

Descriptions phải giúp phân biệt:

- case-specific score vs evaluation score;
- customer decision vs knowledge;
- simulation vs current state;
- PTP vs generic customer summary;
- contact-history vs current action.

---

# 17. Response composition

Persona cần thống nhất.

Preferred persona:

- lịch sự;
- ngắn;
- dễ đọc trên Zalo;
- hiểu slang nhưng không bắt chước slang thô.

Khuyến nghị:
`Anh/Chị` cho người dùng, `Trợ lý` hoặc `tôi` cho bot.

Không dùng raw internal enums trong response nếu có public label.

---

# 18. Duplicate-response protection

Inspect và test:

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

Acceptance:

```text
DUPLICATE_RESPONSE_RATE=0
```

---

# 19. No-response reliability

Acceptance:

```text
NO_RESPONSE_RATE=0
```

Trong supported scope, mỗi user message phải:

- trả answer;
- hoặc clarification;
- hoặc safe fallback;
- nhưng không im lặng.

---

# 20. Pairing / reconnect reliability

Inspect lifecycle:

- pairing state;
- worker state;
- recipient target;
- reconnect;
- session expiration.

Không redesign transport.

Nếu lỗi do external provider state không sửa được:
report truthfully.

---

# 21. Real Conversation Regression Corpus

Transcript thực tế phải trở thành regression corpus.

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

Expected results phải được human/canonical-contract label trước khi optimization.

OpenCode không được tự đổi expected label để làm đẹp metric.

Required:

```text
REAL_TRANSCRIPT_REPLAY=PASS
```

---

# 22. Auto-generated paraphrase evaluation

Từ mỗi canonical seed intent, tự sinh paraphrase set.

Các biến thể:

- casual;
- formal;
- slang;
- typo nhẹ;
- không dấu;
- đảo từ;
- câu ngắn;
- câu dài;
- follow-up fragment.

Important:

- label intent kế thừa seed;
- generated text không được tự tạo expected business output;
- canonical tools/Decision Core quyết định expected business truth.

---

# 23. Multi-turn evaluation

## Sequence A — knowledge continuity

```text
CALL là gì
CBS thì sao
Khác nhau ở đâu
```

## Sequence B — active CIF score

```text
Giải thích SYN001346
Điểm bao nhiêu
Điểm dựa trên gì
Khả năng thanh toán 24 điểm vì sao
```

## Sequence C — simulation

```text
Giải thích SYN002846
Nếu tiền vào 7 ngày bằng 0 thì sao
Thế giờ làm gì
Vì sao lại đổi
Quay lại dữ liệu thật
```

## Sequence D — clarification

```text
Khách không trả nợ thì sao
Mô phỏng
```

## Sequence E — switch CIF

```text
Giải thích SYN001346
Điểm bao nhiêu
Chuyển sang SYN000746
Điểm bao nhiêu
```

Required:
no cross-CIF leakage.

---

# 24. Adversarial/state evaluation

Test:

- wrong/typo CIF;
- nonexistent CIF;
- duplicate message id;
- duplicate update id;
- delayed retry;
- reconnect;
- worker restart if safe;
- AgentBase timeout;
- RAG timeout;
- simulation no-change;
- simulation then CIF switch;
- greeting after active CIF;
- knowledge topic after active CIF;
- clarification answer one-word;
- repeated “Alo”.

---

# 25. Metrics / gates

Required targets:

```text
IN_SCOPE_INTENT_ACCURACY >= 95%
PARAPHRASE_INTENT_ACCURACY >= 95%
FOLLOWUP_RESOLUTION_ACCURACY >= 95%

IN_SCOPE_FALLBACK_RATE <= 3%
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
UNSUPPORTED_DECISION_CLAIM = 0

MAX_TOOL_CALL_BREACH = 0
REAL_TRANSCRIPT_REPLAY = PASS
```

---

# 26. Business canaries

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

Use current canonical production result as source of truth.
Do not hardcode transcript values if current fixture differs.
Inspect actual fixture before assertions.

---

# 27. Regression scope

Run relevant regression:

- Zalo conversation tests;
- AgentBase planner tests;
- tool-selection tests;
- Decision canaries;
- simulation;
- RAG knowledge;
- auth/session adapter;
- duplicate protection;
- Web Copilot smoke;
- `/app/zalo` UI smoke.

No frontend landing changes expected.

TASK-016 must remain untouched.

---

# 28. Source scope

Allowed:

- Zalo conversation module;
- conversation state;
- intent/router;
- AgentBase conversation adapter;
- shared tool registry only if backward-compatible;
- Zalo tests/evals;
- bounded test utilities;
- task report.

Do not change:

- landing;
- Decision Core business logic;
- score formula;
- routing;
- NBA;
- PTP semantics;
- frontend app architecture.

Required:

```text
TASK016_LANDING_CHANGED=NO
DECISION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
```

---

# 29. Workflow

```text
INSPECT
→ REPRODUCE REAL TRANSCRIPT FAILURES
→ ROOT-CAUSE CLASSIFY
→ DESIGN
→ ADD REGRESSION TESTS FIRST
→ IMPLEMENT
→ AUTO-GENERATE PARAPHRASE TESTS
→ MULTI-TURN TESTS
→ ADVERSARIAL TESTS
→ METRICS
→ SELF-REVIEW
→ RETEST
→ VERY AUDIT
→ COMMIT
→ BACKUP
→ DEPLOY
→ LIVE ZALO ROUNDTRIP
→ CLOSEOUT
```

---

# 30. Test-first rule

For each confirmed transcript bug:

1. reproduce;
2. add failing regression;
3. fix;
4. rerun;
5. keep regression permanently.

Do not merely tune prompt until manual example works.

---

# 31. Very Audit

Before commit, independently verify:

1. Decision Core unchanged.
2. Business semantics unchanged.
3. TASK-016 landing unchanged.
4. AgentBase remains bounded.
5. No action tools exposed.
6. Follow-up state isolated by chat.
7. CIF isolation.
8. Simulation isolation.
9. Knowledge topic continuity.
10. Duplicate protection.
11. No silent message drop.
12. Score questions route correctly.
13. Priority explanation works.
14. Clarification works.
15. Real transcript replay passes.
16. Metrics meet gates.

Required:

```text
VERY_AUDIT=PASS
```

---

# 32. Task report

Create:

`task-results/TASK-017-ZALO-CONVERSATION-AGENT-QUALITY-V1-FINAL.md`

Record:

```text
TASK_ID=TASK-017-ZALO-CONVERSATION-AGENT-QUALITY-V1

PREVIOUS_HEAD=<actual>
TASK017_COMMIT=<sha>

TASK016_LANDING_CHANGED=NO
DECISION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

REAL_TRANSCRIPT_REPLAY=PASS

IN_SCOPE_INTENT_ACCURACY=<actual>
PARAPHRASE_INTENT_ACCURACY=<actual>
FOLLOWUP_RESOLUTION_ACCURACY=<actual>

IN_SCOPE_FALLBACK_RATE=<actual>
WRONG_TOOL_RATE=<actual>
UNNECESSARY_TOOL_RATE=<actual>

WRONG_CIF=0
CROSS_CIF_CONTEXT_LEAK=0
SIMULATION_CONTEXT_LEAK=0

DUPLICATE_RESPONSE_RATE=0
NO_RESPONSE_RATE=0

DECISION_PARITY=100%
SCORE_PARITY=100%

RAW_ENUM_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0
MAX_TOOL_CALL_BREACH=0

ZALO_TESTS=PASS
AGENTBASE_TESTS=PASS
RAG_SMOKE=PASS
WEB_COPILOT_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS

VERY_AUDIT=PASS

READY_TO_DEPLOY=YES/NO
```

---

# 33. Commit

If all pre-deploy gates pass:

Suggested commit:

`Improve Zalo conversation quality and AgentBase routing`

No push.

---

# 34. Production deployment

Before deploy:

- backup production;
- record rollback point.

Restart only the Zalo worker/backend component actually required.

Do not restart unrelated services.

---

# 35. Production live roundtrip

Must perform real Zalo roundtrip after deploy.

Suggested live sequence:

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
```

Also test:

```text
Khách không trả nợ thì sao
```

Expected:
useful clarification, not customer-summary fallback.

Required:

```text
PRODUCTION_ZALO_LIVE_ROUNDTRIP=PASS
```

---

# 36. Production reliability checks

Verify:

```text
PRODUCTION_DUPLICATE_RESPONSE_RATE=0
PRODUCTION_NO_RESPONSE_RATE=0
PRODUCTION_WRONG_CIF=0
PRODUCTION_CONTEXT_LEAK=0
PRODUCTION_DECISION_PARITY=100%
PRODUCTION_SCORE_PARITY=100%
```

If actual provider/network prevents a reliable result:
report truthful blocker; never fabricate PASS.

---

# 37. Rollback triggers

Rollback if:

- Decision parity < 100%;
- wrong CIF;
- cross-chat/CIF context leak;
- duplicate responses;
- supported messages silently dropped;
- AgentBase loop exceeds bounds;
- Zalo pairing breaks;
- existing Web Copilot regression;
- security/auth regression;
- business semantics drift.

Rollback must preserve TASK-013 through TASK-016.

---

# 38. Final closeout gates

```text
TASK_017_CLOSED=YES

REAL_TRANSCRIPT_REPLAY=PASS

IN_SCOPE_INTENT_ACCURACY>=95%
PARAPHRASE_INTENT_ACCURACY>=95%
FOLLOWUP_RESOLUTION_ACCURACY>=95%

IN_SCOPE_FALLBACK_RATE<=3%
WRONG_TOOL_RATE<=3%
UNNECESSARY_TOOL_RATE<=15%

WRONG_CIF=0
CROSS_CIF_CONTEXT_LEAK=0
SIMULATION_CONTEXT_LEAK=0

DUPLICATE_RESPONSE_RATE=0
NO_RESPONSE_RATE=0

DECISION_PARITY=100%
SCORE_PARITY=100%

RAW_ENUM_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0
MAX_TOOL_CALL_BREACH=0

PRODUCTION_ZALO_LIVE_ROUNDTRIP=PASS

WEB_COPILOT_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS

TASK016_LANDING_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

VERY_AUDIT=PASS
ROLLBACK_REQUIRED=NO
PUSH=NO
```

---

# 39. Final principle

> **Hiểu linh hoạt hơn, nhưng quyết định không tự do hơn.**

> **AgentBase giúp bot hiểu câu hỏi và chọn đúng công cụ; Decision Core vẫn giữ quyền quyết định nghiệp vụ.**

> **Conversation quality phải được chứng minh bằng transcript replay, paraphrase tests, multi-turn tests và live Zalo roundtrip — không chỉ bằng vài câu demo.**
