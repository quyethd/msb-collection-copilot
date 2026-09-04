# TASK-009B FINAL REPORT — MSB COLLECTION ASSISTANT RESPONSE UX

## Final Status

TASK-009B PASS — MSB COLLECTION ASSISTANT UX PROVEN

## Objective

Improve ONLY the user-facing GreenNode Agent response experience. The Copilot drawer
previously exposed developer-oriented output (DETERMINISTIC DECISION blocks, raw
treatment/channel/objective codes, raw `when` JSON, English AI explanation). This is
unacceptable for Collection Officers and competition judges.

The deterministic decision itself is correct and unchanged. Business rules, routing,
treatment/channel/objective/when, TASK-007A decisions, and TASK-010 are untouched.

## Product Name

- Primary MSB name: **MSB Trợ lý Quyết định Thu hồi**
- Short navigation name: **Trợ lý Thu hồi**
- Drawer/header: **Hỏi Trợ lý Thu hồi**
- Secondary attribution only: **Vận hành bởi GreenNode AI**

GreenNode branding is secondary to MSB product branding throughout the frontend
(sidebar brand, drawer eyebrow, answer footer).

## Files Changed

| File | Change |
|---|---|
| `src/msb_agent/models.py` | Added `sections`, `technical`, `question_intent` fields to `AgentResponse`; bumped `AGENT_VERSION` to `TASK-009B-V1`; always emits `sections` in `to_dict`. |
| `src/msb_agent/router.py` | Added `detect_question_intent()` — maps Vietnamese questions to `WHY_NO_CALL`, `SUMMARY`, `CHANGE_FACTORS`. |
| `src/msb_agent/runtime.py` | Rewrote all summaries/prompts to natural Vietnamese; added intent-aware structured answers with `sections`; added `technical` from NBA; fallback templates are Vietnamese; keeps deterministic decisions untouched. |
| `tests/test_task009b.py` | New suite — 21 tests covering all 15 required areas. |
| `tests/test_task007b.py` | Updated 2 assertions to reflect the new UX (PLAN summary is Vietnamese; no `DETERMINISTIC DECISION`/`AI EXPLANATION` headings). Determinism assertions unchanged. |
| `tests/test_task008.py` | Updated `AGENT_VERSION` assertion to `TASK-009B-V1` (agent presentation layer). Simulation semantics unchanged. |
| `tests/test_task008b.py` | Updated `AGENT_VERSION` assertion to `TASK-009B-V1` (same reason). |
| `frontend/src/main.tsx` | Copilot drawer renders structured `sections`; product naming updated; no raw code dump. |
| `frontend/src/styles.css` | Added `.ans-sections` / `.ans-sec` styling for the structured answer. |
| `frontend/src/ui-contract.test.ts` | Updated label to `Hỏi Trợ lý Thu hồi`. |

## Response Contract

The Agent layer emits a structured payload. Human-facing text is in `summary`/`sections`.
Developer-oriented values live only in the separate `technical` object (and the existing
`decision`/`evidence` structured data) — never in the primary human text.

```json
{
  "summary": "Đề xuất: Chờ khách hàng tự thanh toán. ...",
  "sections": [
    { "title": "Đề xuất hiện tại", "content": "Chờ khách hàng tự thanh toán" },
    { "title": "Vì sao?", "items": ["...", "..."] },
    { "title": "Cán bộ cần làm gì?", "content": "Chưa cần liên hệ tại thời điểm này. ..." }
  ],
  "technical": {
    "rule_id": "NBA-300",
    "treatment": "WAIT_SELF_CURE",
    "channel": "NONE",
    "reason_code": "CALL_SELF_CURE",
    "final_route": "CALL",
    "objective": "PAYMENT"
  },
  "question_intent": "WHY_NO_CALL"
}
```

`technical` remains separate from the primary human-facing text. The frontend never
has to parse Markdown headings like `**DETERMINISTIC DECISION:**`.

## SYN002846 — Question A Example (live, actual tool values)

Question: **"Tại sao hôm nay chưa nên gọi khách hàng này?"**

> **Đề xuất hiện tại**
> Chờ khách hàng tự thanh toán
>
> **Vì sao?**
> - Khách hàng đang quá hạn 11 ngày.
> - Trong 7 ngày gần nhất có 48 triệu đồng tiền vào.
> - Dòng tiền ròng 30 ngày gần nhất là 168 triệu đồng.
> - Hiện chưa có cam kết thanh toán cần xử lý ngay.
> - Với các tín hiệu hiện tại, khách hàng đáp ứng điều kiện để ưu tiên chờ tự
>   thanh toán thay vì liên hệ ngay.
>
> **Cán bộ cần làm gì?**
> Chưa cần liên hệ tại thời điểm này. Tiếp tục theo dõi thay đổi về dòng tiền
> và cam kết thanh toán.

This matches the required SYN002846 meaning exactly and uses actual tool values
(dpd=11, inflow_7d=48m, net_cashflow_30d=168m, ptp_state=NONE). Values are not
hardcoded — they are derived from the live `get_next_best_action` evidence.

## Three Suggested-Question Examples

**A. "Tại sao hôm nay chưa nên gọi khách hàng này?"** → `WHY_NO_CALL`
- Structured `Đề xuất hiện tại` / `Vì sao?` / `Cán bộ cần làm gì?` sections with
  grounded evidence.

**B. "Tóm tắt nhanh tình trạng khách hàng này."** → `SUMMARY`
- 3–5 concise business sentences (overdue, outstanding, recent inflow, promise
  status, recommended action). No field dumping.

**C. "Điều gì có thể làm quyết định thay đổi?"** → `CHANGE_FACTORS`
- Explains only factors supported by accepted simulation/event contracts:
  change in recent cashflow, a new payment promise, a promise not kept, or new
  interaction results. No invented future business rules.

## Fallback Proof

When GreenNode MaaS is unavailable (`llm_client=None`, as in the demo tool_server
path), the deterministic/template fallback is ALWAYS natural Vietnamese. Verified
end-to-end against the live `/demo/copilot` endpoint:

```
Question A (SYN002846) → "Đề xuất: Chờ khách hàng tự thanh toán. Khách hàng đang
quá hạn 11 ngày. Trong 7 ngày gần nhất có 48 triệu đồng tiền vào. ..."

Question (SYN000123)  → "Đề xuất: Chờ theo dõi. Khách hàng đang quá hạn 1 ngày.
Dòng tiền ròng 30 ngày gần nhất là -8.281.693 đồng. ..."
```

No developer-oriented English appears in the fallback.

## Unknown / Missing Data

Missing fields are not invented and never surface as `null` / `None` / `N/A` /
`undefined` to business users. Natural wording is used (e.g.
"Hiện chưa có cam kết thanh toán cần xử lý ngay." or
"Chưa có dữ liệu về cam kết thanh toán."). Covered by
`TestUnknownDataNotFabricated`.

## Agent Role & Vietnamese Style

The Agent never implies "AI quyết định khách hàng này". It uses phrasing such as
"Hệ thống đề xuất…", "Dựa trên thông tin hiện có…", "các tín hiệu hiện tại cho
thấy…", "đáp ứng các điều kiện để ưu tiên…". It never states unsupported certainty
like "khách hàng chắc chắn sẽ trả". Chain-of-thought is never exposed.

## GreenNode Prompt

All GreenNode system/instruction prompts were rewritten (runtime.py) to:
- answer Vietnamese by default,
- follow the user's actual question,
- use only provided deterministic evidence,
- not repeat internal JSON,
- not output chain-of-thought,
- not reinterpret or recommend a different action,
- stay concise enough for a Collection Officer.

## Tests

### TASK-009B suite (`tests/test_task009b.py`) — 21 tests, PASS

| Required area | Covered by |
|---|---|
| 1. SYN002846 answer is Vietnamese | `TestSyn002846VietnameseResponse` |
| 2. no primary WAIT_SELF_CURE leakage | `TestNoPrimaryLeakage` |
| 3. no primary raw JSON leakage | `TestNoRawJsonLeakage` |
| 4. no "DETERMINISTIC DECISION" heading | `TestNoDeveloperHeadings` |
| 5. no "AI EXPLANATION" heading | `TestNoAiExplanationHeading` |
| 6. actual deterministic decision unchanged | `TestDeterministicDecisionUnchanged` |
| 7. unknown data is not fabricated | `TestUnknownDataNotFabricated` |
| 8. question A gets reason-focused answer | `TestQuestionIntentRouting` / `TestSyn002846VietnameseResponse` |
| 9. question B gets summary-focused answer | `TestQuestionIntentRouting` |
| 10. question C gets change-factor-focused answer | `TestQuestionIntentRouting` |
| 11. fallback is Vietnamese | `TestFallbackVietnamese` |
| 12. reasoning_content never exposed | `TestReasoningContentNeverExposed` |
| 13. technical details remain available separately | `TestTechnicalDetailsSeparate` |
| 14. TASK-007B regression remains PASS | `TestTask007bRegression` |
| 15. TASK-008 / TASK-008B semantics unchanged | `TestTask008SemanticsUnchanged` |

### Backend regression run (this session)

| Suite | Count | Result |
|---|---|---|
| test_task009b (new) | 21 | PASS |
| test_task007b | 48 | PASS |
| test_task008 | 47 | PASS |
| test_task008b | 67 | PASS |
| test_nba | 11 | PASS |
| test_policy_engine | 25 | PASS |
| test_recovery_engine | 26 | PASS |
| test_synthetic_data | 4 | PASS |
| test_context_assembly | 14 | PASS |
| test_evaluation_engine | 13 | PASS |
| **Backend subtotal** | **276** | **PASS** |

Note: `test_tools.py::test_persisted_schema_matches_source_and_validates_responses`
requires the TASK-006 build artifact `build/tools/tool_schemas.json` to exist in the
environment. `build/` was not present in this checkout; `src/msb_tools/` has zero diff
from HEAD, so this is a pre-existing environmental artifact requirement, not caused by
TASK-009B. (A TASK-007B tool-server test likewise required `build/synthetic-data`, which
was generated and the test then passed.)

### Frontend

- `npm run build`: PASS (TypeScript + Vite production build).
- `vitest run`: 3/3 PASS.

## Business Drift

BUSINESS_SEMANTICS_DRIFT=0

`git diff HEAD -- src/msb_nba/ src/msb_policy/ src/msb_recovery/ src/msb_simulation/
src/msb_synthetic/ src/msb_context/ src/msb_evaluation/ src/msb_demo/ src/msb_tools/` = empty.

Accepted business engines unchanged:
- TASK-001 (src/msb_synthetic/) — unchanged
- TASK-002 (src/msb_policy/) — unchanged
- TASK-003 (src/msb_recovery/) — unchanged
- TASK-004 (src/msb_evaluation/) — unchanged
- TASK-005 (src/msb_context/) — unchanged
- TASK-006 (src/msb_tools/) — unchanged
- TASK-007A (src/msb_nba/) — unchanged
- TASK-008 (src/msb_simulation/) — unchanged
- TASK-008B (src/msb_demo/) — unchanged

TASK-009B only changed the Agent presentation layer (`src/msb_agent/`) and the frontend.
No business rules, decisions, routing, or event semantics were modified.

## Commit Status

NOT COMMITTED — WAITING FOR PRODUCT OWNER APPROVAL

## Verdict

TASK-009B PASS — MSB COLLECTION ASSISTANT UX PROVEN
