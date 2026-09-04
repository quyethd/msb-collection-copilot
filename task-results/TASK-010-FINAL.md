# TASK-010 FINAL REPORT

## Final Status

TASK-010 PASS — IMPACT / AEV ENGINE PROVEN

## Goal

Đo lường giá trị vận hành tiềm năng của Collection Decision Copilot bằng output deterministic đã chấp nhận, giả định có thể chỉnh sửa và công thức minh bạch. Không ước tính recovery uplift.

## Impact Architecture

`src/msb_impact/engine.py` đọc `ToolRepository` (TASK-001 đến TASK-005), gọi NBA TASK-007A để đọc quyết định, lấy ranking từ `context.ranking`, rồi trả `ImpactReport`. Engine không ghi dữ liệu và không thay đổi routing, score, NBA, event hoặc simulation.

## Measured Metrics

Trên synthetic portfolio hiện tại: `total_customers=3000`; `decisions_available=3000`; `decision_coverage_rate=1.0`; `auto_triaged_customers=3000`; `call_route_customers=1740`; `call_route_but_no_call_now=32`; `potential_call_avoidance_rate=0.0183908046`; `active_contact_recommendations=1933`.

Ranking: Spearman `0.2725424`; Top-10 overlap `0`; Top-50 overlap `0`; Top-100 overlap `6`; promoted `1415`; demoted `1585`.

## Configurable Assumptions

Giả định minh họa, có thể thay đổi: 250 ngày làm việc/năm; 100 khách/ngày; 3 phút xem xét thủ công/khách; 0,5 phút/khách khi có Copilot; 3 phút/cuộc gọi; 100.000 VND/giờ.

## Formulas

Review hours = daily customers × minutes/customer × working days / 60. Calls/day = daily customers × potential call avoidance rate. Call hours = calls/day × average call minutes × working days / 60. Total hours = review hours saved + call hours saved. Operational cost = total hours × staff cost/hour. AEV estimate = operational cost saved; no recovery uplift.

## Derived Estimates

Default run: baseline review `1250,0` giờ; Copilot review `208,3` giờ; review saved `1041,7` giờ; calls/day `1,8391`; call saved `23,0` giờ; total saved `1064,7` giờ; operational cost and AEV estimate `106.465.517,24 VND`.

## Baseline vs Copilot

Baseline là thứ tự dư nợ + DPD; Copilot đọc thêm các output Recovery Opportunity/NBA đã chấp nhận. Ranking difference != proven recovery improvement.

## CALL Route / No-Call-Now Metric

Có 1.740 khách thuộc route CALL; 32 khách trong đó có channel NONE hoặc treatment WAIT/WAIT_SELF_CURE. Đây là “tiềm năng tránh cuộc gọi chưa cần thiết”, không phải số cuộc gọi thực tế đã giảm.

## AEV Estimate

`aev_estimate_vnd = total_hours_saved * staff_cost_per_hour_vnd = 1064,6552 * 100000 = 106.465.517,24 VND`.

Ước tính theo giả định đầu vào. Không phải số liệu vận hành thực tế và không bao gồm recovery uplift.

## Provenance

Mỗi metric có metadata `MEASURED_FROM_DEMO_DATA`, `CONFIGURABLE_ASSUMPTION` hoặc `DERIVED_ESTIMATE`, kèm source/formula.

## API

`POST /demo/impact` dùng Bearer auth, nhận `{ "assumptions": {...} }`, trả ImpactReport; không trả secrets.

## UI

Đã thêm mục “Tác động dự kiến” với bốn phần: đo được ngay; baseline vs Copilot; input giả định chỉnh sửa được; giá trị vận hành ước tính và cách tính. Disclaimer tiếng Việt luôn hiển thị. Không có recovery metric/ROI claim trong primary UI.

## Live QA

BACKEND_REGRESSION=PASS. TASK-007A `11/11`, TASK-007B `48/48`, TASK-008 `47/47`, TASK-008B `67/67`, TASK-010 impact `5/5`.

LIVE_IMPACT_QA=PASS. Real backend + Vite frontend + Chromium đã mở trang “Tác động dự kiến”; không dùng frontend fixture.

MEASURED_METRICS_STABLE=PASS. Default và modified đều có measured: 3000, 3000, 1.0, 3000, 1740, 32, 0.0183908046, 1933; ranking 0.2725424 / 0 / 0 / 6 / 1415 / 1585.

ASSUMPTION_SENSITIVITY=PASS. `daily_customers_reviewed` 100 → 200; derived total hours `1064.7` → `2129.3`; AEV estimate `106465517.24` → `212931034.48` VND.

AEV_DISCLAIMER_VISIBLE=PASS. Cùng visible section có “Ước tính theo giả định đầu vào” và “Không phải số liệu vận hành thực tế”; assumptions editable không bị ẩn.

API default PASS: measured values như trên. API modified `daily_customers_reviewed=200` PASS: measured giữ nguyên; derived total hours `2129,3`, AEV `212.931.034,48 VND`, thay đổi theo tỷ lệ. Chromium review PASS với real API.

## Tests

Impact backend: `5/5` PASS. TASK-007A `11/11`, TASK-007B `48/48`, TASK-008 `47/47`, TASK-008B `67/67` PASS. Frontend Vitest `3/3` PASS; TypeScript/Vite production build PASS.

## Anti Fake Metric Audit

Không có recovery uplift mặc định, không có production staffing/time claim, không có guaranteed savings language; call wording là “32 khách thuộc tuyến gọi điện nhưng hiện chưa cần gọi ngay”. `ANTI_FAKE_METRIC_GATE=PASS`

## Screenshots reviewed

- `task-results/task010-screenshots/impact-default.png`
- `task-results/task010-screenshots/impact-modified.png`

Measured metrics không đổi; derived values đổi; assumptions, disclaimer và money formatting dễ đọc; UI không bị English technical jargon chi phối.

## Business Drift

TASK-010 chỉ đọc accepted outputs. `BUSINESS_SEMANTICS_DRIFT=0`

## Files Created

- `src/msb_impact/__init__.py`
- `src/msb_impact/engine.py`
- `tests/test_impact.py`
- `task-results/TASK-010-FINAL.md`

## Files Modified

- `tool_server.py`
- `frontend/src/main.tsx`
- `frontend/src/styles.css`

## Git Status

Working tree có các thay đổi TASK-009 có sẵn và thay đổi TASK-010; không commit.

## Commit Status

NOT COMMITTED — WAITING FOR PRODUCT OWNER APPROVAL
