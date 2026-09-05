# TASK-011F — SYSTEM OVERVIEW LANDING PAGE (FINAL)

## Status
**TASK-011F PASS — READY TO CHERRY-PICK INTO MASTER**

```
IMPLEMENTATION=PASS
CONTENT=PASS
AGENTBASE_STATUS_UPDATED=PASS
MSB_AGENT_EVAL_UPDATED=PASS
ROADMAP_UPDATED=PASS
TESTS=PASS
BUILD=PASS
SECRET_AUDIT=PASS
CONTENT_TRUTH_AUDIT=PASS

INTEGRATION=WAIT
DEPLOY=NO
```

## Verification gates
```
TASK011F_TESTS=PASS      # 27/27 (23 system-overview + 4 ui-contract)
FRONTEND_REGRESSION=PASS # existing frontend tests unaffected
BUILD=PASS               # tsc -b && vite build (production)
SECRET_AUDIT=PASS        # no secrets, no credentials, no reasoning_content, no internal endpoint
CONTENT_TRUTH_AUDIT=PASS # no false AgentBase pending wording, no future roadmap as shipped,
                         # no NBA-300 in business UI, no runtime IDs in marketing
```

## Scope
Premium, self-contained "System Overview" landing page for MSB "Trợ lý Thu hồi Nợ — Powered by GreenNode AI".
Built in the isolated worktree `/opt/msb-collection-copilot-task011f` (branch `task-011f-system-overview`).
Master was NOT modified. Committed on the branch only; INTEGRATION=WAIT until cherry-pick is approved.

## Files (committed)
- `frontend/src/pages/system-overview/content.ts` — all page data.
- `frontend/src/pages/system-overview/SystemOverviewPage.tsx` — page component (named + default export), props `onOpenOverview`, `onOpenCustomer(cif)`, `ctaOverviewLabel`, `ctaCustomerLabel`.
- `frontend/src/pages/system-overview/system-overview.css` — all styles scoped under `.system-overview-page`.
- `frontend/src/pages/system-overview/SystemOverviewPage.test.tsx` — 23 vitest cases.
- `task-results/TASK-011F-SYSTEM-OVERVIEW-LANDING-FINAL.md` — this report.

## Preview files decision
`frontend/preview.html` + `frontend/preview.tsx` were development-only preview helpers
(mount `SystemOverviewPage` with stub callbacks, console-log handlers).
They are NOT required for production integration and were **removed** (not committed).
If a local preview is needed again they can be regenerated trivially; they never belonged in the production commit.

## AgentBase status (updated)
Replaced the stale wording `"Đang hoàn thiện kiểm chứng AgentBase live end-to-end"`
with the verified statement:
- `"Đã kiểm chứng AgentBase kết nối công cụ quyết định và giữ nguyên kết quả nghiệp vụ."`

The trust section now explains, backed by live PASS evidence from TASK-011:
- Quyết định nghiệp vụ đến từ các quy tắc deterministic.
- AgentBase truy xuất công cụ nghiệp vụ trước khi giải thích câu hỏi quyết định.
- Khách hàng chưa biết (unknown CIF) không bị bịa dựng thông tin.
- Yêu cầu can thiệp (override) không làm thay đổi quyết định nghiệp vụ đã chấp nhận.
- Lý do suy luận nội bộ (private reasoning) không được tiết lộ.
- Safety statement: "Thiết kế giảm rủi ro AI tự suy diễn quyết định nghiệp vụ."

No runtime IDs, credentials, internal endpoint URLs, private prompts or chain-of-thought are exposed.
Runtime version 7 is NOT shown in the business UI.

## Agent evaluation module (updated)
Master now ships a real module `src/msb_agent_eval/` (evaluator.py + scenarios.py).
The System Overview module section now presents it in business-friendly form:
- Module card: `msb_agent_eval` — "Đánh giá độ tin cậy của Trợ lý."
- Checks shown under the card:
  - kiểm tra Agent dùng đúng công cụ nghiệp vụ
  - so khớp quyết định Agent với deterministic engine
  - kiểm tra khách hàng chưa biết không bị bịa dựng
  - kiểm tra override guardrail
  - kiểm tra không lộ lý do suy luận nội bộ
Each item maps to proven TASK-011 evidence (tool_use_success, decision_fidelity,
unknown_no_fabrication, guardrail_pass, private_reasoning_leak). No capabilities are invented.

## Roadmap (replaced)
Generic/unapproved items (chat history, recursion, multi-tenant, RBAC, generic scheduling) are absent.
Only the approved roadmap is shown, in Vietnamese-facing labels:
- **Đã có trong bản demo**: Decision Intelligence · CALL / CBS · Recovery Opportunity · Next Best Action · What-if Simulation · GreenNode Agent
- **Hướng phát triển tiếp theo**: Outcome feedback · Pilot / A-B evaluation · Learning-to-rank · Channel optimization · Treatment optimization · Portfolio monitoring
- Disclaimer: "Những mục trong nhóm Hướng phát triển tiếp theo chưa phải tính năng đã triển khai."

## Landing story (preserved)
The page answers the 10 questions in order, for hackathon judges / collection officers /
managers / architecture reviewers — not a technical manual:
1. Sản phẩm dành cho ai (audience + benefit cards)
2. Vấn đề hiện tại (4 pain cards)
3. Hệ thống giải quyết gì (hero + WHY/WHAT)
4. Một quyết định được tạo như thế nào (WHO/WHY/WHAT/WHEN + decision pipeline)
5. GreenNode AI đóng vai trò gì (pipeline statements + AI làm gì / AI không làm gì)
6. Hệ thống đảm bảo đáng tin cậy ra sao (6 rule layers + trust section)
7. Kiến trúc hoạt động thế nào (architecture + modules)
8. Người dùng có thể hỏi gì (sample questions + FAQ)
9. Hệ thống hiện đã làm được gì (roadmap "Đã có trong bản demo")
10. Hướng phát triển tiếp theo (roadmap "Hướng phát triển tiếp theo")

## Hero / product message
- Thesis: "Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo."
- Promise: "Đúng khách hàng · Đúng hành động · Đúng thời điểm · Lý do rõ ràng"
- Vietnamese-first UI; English kept only for domain jargon (CALL/CBS, DPD, PTP) and code identifiers.

## Hero case SYN002846 (accepted facts)
DPD = 11 ngày · Tiền vào 7 ngày = 48 triệu đồng · Dòng tiền ròng 30 ngày = 168 triệu đồng ·
Không có cam kết thanh toán đang mở · Tuyến xử lý = CALL · Hành động = Chờ khách hàng tự thanh toán · Kênh = Không liên hệ ngay.
Key message: "Thuộc tuyến CALL không có nghĩa hôm nay nhất thiết phải gọi." (pain card + FAQ only, business-friendly wording).
No NBA-300 in the business UI. WHAT-IF shows the same customer switching to "Liên hệ khách hàng" when
Tiền vào 7 ngày = 0 and Dòng tiền ròng = 0 (deterministic simulation, unchanged source data).

## Architecture
- Flows shown: Người dùng → Giao diện MSB → API ứng dụng → Decision Core → dữ liệu mô phỏng; and
  Người dùng hỏi Trợ lý → GreenNode AgentBase → công cụ nghiệp vụ → Decision Core → Agent giải thích kết quả.
- Statement included: "GreenNode không phải yếu tố trang trí" — Agent is used for natural-language
  interaction, tool selection, grounded explanation, investigation and simulation;
  the deterministic engine owns the collection decision.

## Team footer (locked)
- Debt Radar
- Hà Đức Quyết — DigiLenO — Trưởng nhóm
- Phạm Huy Khánh — DigiLenO
- Nguyễn Thị Phương — DC
- MSB AI Hackathon 2026
No titles invented for Khánh or Phương.

## Integration instructions (for cherry-pick / master)
1. Cherry-pick the single TASK-011F commit onto master.
2. Copy `frontend/src/pages/system-overview/` is included in the commit; mount `<SystemOverviewPage/>`
   at `/gioi-thieu` (or page state `system-overview`); wire `onOpenCustomer`/`onOpenOverview` to existing routing.
3. `src/msb_agent_eval/` already exists on master — no backend change needed for the module card.
4. Re-run `tsc -b && vite build` and the vitest suite on master.
5. `vite.config.ts` needs no change (this page makes no backend proxy calls).
6. INTEGRATION=WAIT (do not merge/deploy until cherry-pick is approved); DEPLOY=NO.

## Constraints respected
- Work isolated to `/opt/msb-collection-copilot-task011f`. Master not touched.
- Only TASK-011F files staged and committed. No cherry-pick, no deploy performed.
- No backend/policy/rule changes. No production runtime changes.