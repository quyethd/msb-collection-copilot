# RULE_BASE_V1 --- MSB Collection Decision Copilot

**Version:** 1.0 --- LOCKED FOR V1 BUILD

> Codex MUST NOT add/reinterpret collection rules. Missing rules remain
> UNKNOWN/CONFIGURABLE.

## 0. Precedence

`POLICY → ROUTE → SUPPRESS → PTP/NEXT_ACTION → SCORE → TREATMENT → CHANNEL → WHEN → EXPLAIN`

High score MUST NOT override hard policy.

## 1. Aggregation / baseline

-   **AGG-001 \[MSB-CONFIRMED\]**
    `total_outstanding_cif = SUM(outstanding_amount)` của các khoản vay
    thuộc CIF.
-   **AGG-002 \[MSB-CONFIRMED\]** `max_dpd_cif = MAX(dpd)`.
-   **BASE-001 \[MSB-CONFIRMED\]** baseline ưu tiên dựa trên tổng dư nợ
    CIF + MAX DPD.
-   **BASE-002 \[PROTOTYPE-RULE\]** để benchmark deterministic: sort
    `total_outstanding_cif DESC, max_dpd_cif DESC, cif ASC`. Tie-break
    không được gọi là official MSB formula.

## 2. Routing

-   **ROUTE-001 \[MSB-CONFIRMED\]** Heatmap=RED,
    Segment∈{RED,ORANGE,YELLOW}, MAX_DPD\>=5 → base CALL.
-   **ROUTE-002 \[MSB-CONFIRMED\]** cùng điều kiện nhưng MAX_DPD\<5 →
    base CBS.
-   **ROUTE-003 \[MSB-CONFIRMED\]** challenge-set có thể CALL→CBS hoặc
    CBS→CALL.
-   **ROUTE-004 \[CONFIGURABLE\]** chi tiết challenge rule chưa có;
    synthetic dùng explicit `challenge_override_route`.
-   **ROUTE-005 \[PROTOTYPE-RULE\]** ngoài điều kiện trên → OTHER/NONE
    trong prototype.

## 3. PTP

-   **PTP-001 \[PROTOTYPE-RULE\]** chưa tới promise date và chưa paid đủ
    → OPEN.
-   **PTP-002 \[USER-CONFIRMED\]** actual_paid \>= promised → KEPT.
-   **PTP-003 \[USER-CONFIRMED\]** 0 \< actual_paid \< promised →
    PARTIAL.
-   **PTP-004 \[PROTOTYPE-RULE\]\[CONFIGURABLE\]** paid=0 sau
    `promise_date + grace_days` → BROKEN; demo default grace=1 ngày.
-   **PTP-005 \[PROTOTYPE-RULE\]** fulfillment=`min(actual/promised,1)`
    nếu promised\>0.
-   **PTP-006 \[MSB-CONFIRMED\]** PTP ability
    CERTAIN/HIGH/MEDIUM/LOW/VERY_LOW là đánh giá của nhân viên.
-   **PTP-007 \[PROTOTYPE-RULE\]** ability assessment chỉ là supporting
    willingness signal.

## 4. Operation/contact taxonomy

-   **OUTCOME-001 \[MSB-CONFIRMED\]** UTC=không liên lạc; PTP=hứa trả;
    NPTP=hứa trả không rõ; RTP=từ chối; NIN=sai số; THIRT=người thứ 3;
    NA=hẹn gọi lại.
-   **OUTCOME-002 \[MSB-CONFIRMED\]** CALL/SMS/ZALO/EMAIL; next channel
    còn có thể FIELD/LETTER.
-   **OUTCOME-003 \[MSB-CONFIRMED\]** `call_history.status` là trạng
    thái kỹ thuật; `operation_result` là kết quả nghiệp vụ. Không được
    đồng nhất.

## 5. Contactability \[PROTOTYPE-RULE\]

Derive attempts 7/30d, technical success, business contact success, UTC
ratio, failed streak, avg talk duration, days since success, best time
window. - **CONTACT-002** NIN → strong VERIFY_CONTACT signal. -
**CONTACT-003** NA + valid next_action_date → CALLBACK; explicit next
action precedence.

## 6. Cashflow \[PROTOTYPE-RULE\]

Derive inflow 3/7/30d, outflow, net cashflow, recent large inflow,
salary-like income, 90d stability, liquidity-to-due. - **CASH-001**
cashflow = ability/timing evidence, không tự động = willingness. -
**CASH-002** good cashflow không tự suppress CALL; high DPD + good
inflow có thể tăng timing opportunity.

## 7. Recovery Opportunity Score \[PROTOTYPE-RULE\]\[CONFIGURABLE\]

`score = urgency + ability + willingness + contactability + timing + strategic`

  Component                Max
  ---------------------- -----
  Business Urgency          20
  Ability To Pay            25
  Willingness               20
  Contactability            15
  Timing Opportunity        15
  Strategic Adjustment       5

Weights/thresholds MUST nằm trong config.

-   **SCORE-URG-001:** MAX DPD, outstanding percentile/log-normalized,
    overdue PTP.
-   **SCORE-ABL-001:** recent inflow, liquidity-to-due, income
    stability, salary/business-like income, net cashflow.
-   **SCORE-WIL-001:** kept/partial/broken PTP, fulfillment,
    payment-after-contact, PTP/NPTP/RTP, limited employee assessment.
-   **SCORE-CON-001:** contact ratio, UTC, NIN/THIRT, talk evidence,
    channel/time success.
-   **SCORE-TIM-001:** PTP timing, recent inflow, next_action_date,
    successful contact window.
-   **SCORE-STR-001:** default 0 nếu chưa cấu hình.

## 8. Self-cure \[PROTOTYPE-RULE\]\[CONFIGURABLE\]

-   **SELF-001:** candidate = low DPD + historical quick cures + healthy
    cashflow + no broken PTP + no escalation.
-   **SELF-002:** route CALL có thể treatment WAIT_SELF_CURE; route
    không đổi.
-   **SELF-003:** high DPD + good cashflow không được self-cure chỉ vì
    cashflow tốt.

## 9. Treatment

CBS: `WAIT, REMIND, CONTACT, CALLBACK, VERIFY_CONTACT`. CALL:
`WAIT_SELF_CURE, CONTACT, PTP_FOLLOW_UP, PTP_RECOVERY, PARTIAL_PAYMENT, CALLBACK, VERIFY_CONTACT, ESCALATE`.

-   **TREAT-001:** NA + valid next action → CALLBACK.
-   **TREAT-002:** NIN → VERIFY_CONTACT.
-   **TREAT-003:** broken PTP + ability/recent inflow → strong
    PTP_RECOVERY.
-   **TREAT-004:** PARTIAL → PARTIAL_PAYMENT/PTP_FOLLOW_UP tùy timing.
-   **TREAT-005:** self-cure candidate → WAIT_SELF_CURE (CALL) hoặc
    WAIT/REMIND (CBS).
-   **TREAT-006 \[CONFIGURABLE\]:** RTP/repeated broken PTP có thể tăng
    escalation.

## 10. Channel \[PROTOTYPE-RULE\]

`CALL,SMS,ZALO,EMAIL,FIELD,NONE`. - CALLBACK → CALL trừ explicit
override. - VERIFY_CONTACT không blind-call số đã biết invalid. - WAIT
có thể NONE. - CBS low urgency có thể digital-first; preference
configurable.

## 11. WHEN \[PROTOTYPE-RULE\]

Time windows: 08--10, 10--12, 13--15, 15--17, 17--19. - explicit
next_action_date precedence. - PTP due/broken + recent inflow có thể
tăng urgency.

## 12. Explanation

Mọi recommendation trả: route, total score, breakdown, treatment,
channel, when, top reasons, rule IDs, evidence. LLM chỉ diễn đạt
evidence do tools trả về; không invent reason.

## 13. Simulation

Clone snapshot → apply override → same engine → before/after
score/rank/components/treatment/channel/when/rules. **Không mutate
source.**

## 14. Gates

-   0 hard routing violations.
-   SUM outstanding/MAX DPD reconcile.
-   PARTIAL không thành KEPT nếu chưa đủ.
-   Technical status không thay operation outcome.
-   Simulation không mutate.
-   Score bounded 0--100.
-   Recommendation có rule IDs + evidence.

## 15. Agent/GreenNode boundary

- **AGENT-001 [LOCKED]:** Deterministic Policy/Rule Engine là source of truth cho routing, score, treatment, channel và timing logic đã khóa.
- **AGENT-002 [LOCKED]:** GreenNode MaaS/LLM được phép lập kế hoạch tool call, tổng hợp và giải thích; không được tự invent hoặc override rule.
- **AGENT-003 [LOCKED]:** Agent response phải dựa trên structured output từ tools.
- **AGENT-004 [LOCKED]:** Nếu model output xung đột hard rule, hard rule thắng và conflict phải log.
- **AGENT-005 [LOCKED]:** What-if phải gọi lại cùng deterministic engine; không để LLM tự “ước lượng” score/rank.
- **AGENT-006 [LOCKED]:** Runtime/platform policy của GreenNode không được dùng thay collection business policy.
