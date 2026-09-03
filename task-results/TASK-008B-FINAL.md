# TASK-008B FINAL REPORT

## Final Status

TASK-008B PASS — LIVE DECISION EVENT DEMO PROVEN

## Purpose

A small event-driven demo layer that proves this story:

"Sự kiện nghiệp vụ mới xảy ra → hệ thống tự đánh giá lại khách hàng → quyết định có thể thay đổi → GreenNode Agent giải thích ngay vì sao."

This is a demo integration layer only. It is NOT a generic event platform, NOT Kafka,
NOT a workflow engine, NOT a notification platform. It is a small explicit adapter
with three supported event types, in-memory demo state, a per-CIF timeline, and
Vietnamese explanation.

The demo language says: "API mô phỏng sự kiện nghiệp vụ" — a mock event API,
a sample integration point for future real data sources.

## Three Supported Events

| Event Type | Vietnamese Display | Effect |
|---|---|---|
| CASH_IN_RECEIVED | Có tiền vào mới | Add amount to inflow_7d and net_cashflow_30d in demo overlay |
| PAYMENT_PROMISE_CREATED | Có cam kết thanh toán mới | Set ptp_state=OPEN, promise_date=supplied value |
| PAYMENT_PROMISE_BROKEN | Không thực hiện cam kết thanh toán | Set ptp_state=BROKEN |

No fourth event type is supported. Unsupported events return `UNSUPPORTED_EVENT`.

Validation:
- CASH_IN_RECEIVED: amount must be a positive integer (> 0)
- PAYMENT_PROMISE_CREATED: promise_date must be a valid YYYY-MM-DD date
- PAYMENT_PROMISE_BROKEN: no data required

## API Contract

### POST /demo/events

Request:
```json
{
  "event_id": "demo-event-001",
  "event_type": "CASH_IN_RECEIVED",
  "cif": "GOLDEN_G03",
  "occurred_at": "2026-09-03T10:03:00",
  "data": {"amount": 30000000}
}
```

Response:
```json
{
  "status": "success",
  "event": {...},
  "cif": "GOLDEN_G03",
  "before": {...},
  "after": {...},
  "decision_changed": true,
  "diff": [...],
  "timeline_entry": {...},
  "display": {...},
  "explanation": "...",
  "demo_version": "TASK-008B-V1",
  "synthetic_data": true,
  "demo_only": true
}
```

Structured errors:
- `INVALID_ARGUMENT` — invalid event data (amount <= 0, bad date, etc.)
- `NOT_FOUND` — CIF not found in accepted synthetic data
- `UNSUPPORTED_EVENT` — event_type not in the three supported types
- `UNAUTHORIZED` — missing or invalid Bearer token

### GET /demo/timeline/{cif}

Returns the in-memory timeline for the CIF in chronological application order:
```json
{
  "status": "success",
  "cif": "GOLDEN_G03",
  "timeline": [
    {
      "timestamp": "2026-09-03T10:03:00",
      "event_type": "CASH_IN_RECEIVED",
      "event_label": "Có tiền vào mới",
      "before_action": "CONTACT",
      "after_action": "WAIT_SELF_CURE",
      "decision_changed": true,
      "changed_factors": [...],
      "rule_before": "NBA-900",
      "rule_after": "NBA-300"
    }
  ],
  "demo_only": true
}
```

### POST /demo/reset/{cif}

Resets the demo overlay and timeline for the CIF. Does NOT modify accepted source data.
```json
{
  "status": "success",
  "cif": "GOLDEN_G03",
  "reset": true,
  "demo_only": true
}
```

## Demo State Architecture

```
ACCEPTED CUSTOMER SNAPSHOT (from TASK-005 via ToolRepository — immutable)
        +
DEMO EVENT OVERLAY (in-memory, per-CIF, per-process)
        =
CURRENT DEMO STATE (temporary, non-persistent)
```

The demo state is:
- Per-process only (in-memory Python dict)
- No PostgreSQL writes
- No modification to accepted synthetic data
- No Redis, no external storage
- Restart resets demo state
- Clearly marked `demo_only: true` in all responses

When an event is received:
1. Load current demo state for CIF (original + overlay, or original if no overlay)
2. Calculate BEFORE decision using `msb_nba.engine.decide` (TASK-007A)
3. Apply event to demo overlay
4. Replay deterministic decision using existing TASK-007A engine
5. Produce AFTER decision
6. Generate exact deterministic diff
7. Store a small timeline entry in memory

## Original Data Protection

The demo engine uses `copy.deepcopy(context)` to create temporary snapshots.
The overlay is applied only to the copy. The original repository data is never modified.

Verified by `TestOriginalDataUnchanged`:
- `test_context_unchanged_after_event`: context before == context after
- `test_all_contexts_unchanged_after_multiple_events`: multiple CIFs, multiple events, all unchanged
- `test_source_files_unchanged`: source CSV/JSON file hashes unchanged after events

## Timeline

In-memory only, per-CIF. NOT an audit database.

Each entry contains:
- timestamp (event occurred_at)
- event_type (internal enum)
- event_label (Vietnamese display)
- before_action / after_action (treatment codes)
- decision_changed (boolean)
- changed_factors (list of diff entries)
- rule_before / rule_after (rule IDs)

Timeline preserves chronological application order (not sorted by timestamp).
Reset clears the timeline for that CIF.

## GreenNode Explanation Contract

After event processing, the engine produces a Vietnamese explanation.

The LLM (if provided) receives ONLY the completed structured event result and generates
a Vietnamese explanation. The LLM MUST NOT:
- calculate before decision
- calculate after decision
- mutate diff
- change treatment, channel, objective, when, rule_id
- modify event state

LLM output goes ONLY into the `explanation` field.

Verified by `TestExplanationCannotChangeDecision`:
- `test_adversarial_llm_preserves_decision`: adversarial LLM content does not change decision
- `test_adversarial_llm_preserves_diff`: diff is identical with and without adversarial LLM
- `test_explanation_is_string`: explanation is always a string

Explanation language rules:
- Uses "đáp ứng điều kiện" (meets conditions)
- Uses "tín hiệu hiện tại" (current signals)
- Uses "hệ thống chuyển đề xuất" (system switches recommendation)
- Does NOT claim "khách chắc chắn sẽ trả" (customer will definitely pay)
- Does NOT claim "AI biết khách sẽ trả" (AI knows customer will pay)

## Public Route Security

All three demo routes require Bearer authentication (same as existing tool routes):

| Route | Method | Auth Required |
|---|---|---|
| /demo/events | POST | Yes |
| /demo/timeline/{cif} | GET | Yes |
| /demo/reset/{cif} | POST | Yes |

No generic routes are exposed. The following are all rejected with 404:
- `/demo/action`
- `/demo/`
- `/demo/events/extra`
- `/events`
- `/tools/demo`

Existing public tool allowlist remains explicit and unchanged:
```
PUBLIC_TOOL_ALLOWLIST = frozenset({"get_customer_360", "get_next_best_action", "simulate_decision"})
```

Verified by `TestAuthRequired`, `TestPublicRoutesExplicit`, `TestToolAllowlistRemainsTight`.

## Hero Flow 1 — Có tiền vào mới

**CIF:** GOLDEN_G03
**Event:** CASH_IN_RECEIVED, amount=30,000,000

### Before
- Hành động: Liên hệ khách hàng (CONTACT)
- Kênh: Gọi điện (CALL)
- Quy tắc: NBA-900 (CALL_DEFAULT)

### Event
```json
{
  "event_type": "CASH_IN_RECEIVED",
  "cif": "GOLDEN_G03",
  "occurred_at": "2026-09-03T10:03:00",
  "data": {"amount": 30000000}
}
```

### After
- Hành động: Chờ khách hàng tự thanh toán (WAIT_SELF_CURE)
- Kênh: Chưa cần liên hệ (NONE)
- Quy tắc: NBA-300 (CALL_SELF_CURE)

### Diff
- treatment: CONTACT → WAIT_SELF_CURE
- channel: CALL → NONE
- rule_id: NBA-900 → NBA-300
- reason_code: CALL_DEFAULT → CALL_SELF_CURE
- inflow_7d: 0 → 30000000
- net_cashflow_30d: 0 → 30000000

### Vietnamese explanation
"Hệ thống vừa ghi nhận thêm 30 triệu đồng tiền vào. Sau khi đánh giá lại các tín hiệu hiện tại, khách hàng đáp ứng điều kiện để tiếp tục chờ tự thanh toán thay vì cần liên hệ ngay."

## Hero Flow 2 — Có cam kết thanh toán mới

**CIF:** SYN000123
**Event:** PAYMENT_PROMISE_CREATED, promise_date=2026-09-04

### Before
- Hành động: Chờ theo dõi (WAIT)
- Quy tắc: NBA-920 (OTHER_DEFAULT)

### Event
```json
{
  "event_type": "PAYMENT_PROMISE_CREATED",
  "cif": "SYN000123",
  "occurred_at": "2026-09-03T14:20:00",
  "data": {"promise_date": "2026-09-04"}
}
```

### After
- Hành động: Theo dõi cam kết thanh toán (PTP_FOLLOW_UP)
- Kênh: Gọi điện (CALL)
- Thời điểm: Theo ngày cam kết: 2026-09-04
- Quy tắc: NBA-230 (OPEN_PTP)

### Diff
- treatment: WAIT → PTP_FOLLOW_UP
- channel: NONE → CALL
- objective: INFORMATION_COLLECTION → PTP_KEEP
- rule_id: NBA-920 → NBA-230
- reason_code: OTHER_DEFAULT → OPEN_PTP
- ptp_state: NONE → OPEN
- promise_date: null → 2026-09-04

### Vietnamese explanation
"Khách hàng vừa đưa ra cam kết thanh toán vào ngày 2026-09-04. Sau khi đánh giá lại, hệ thống chuyển sang theo dõi cam kết thanh toán thay vì tiếp tục đề xuất hiện tại."

## Hero Flow 3 — Không thực hiện cam kết thanh toán

**CIF:** SYN000141
**Event:** PAYMENT_PROMISE_BROKEN

### Before
- Hành động: Chờ khách hàng tự thanh toán (WAIT_SELF_CURE)
- Quy tắc: NBA-300 (CALL_SELF_CURE)

### Event
```json
{
  "event_type": "PAYMENT_PROMISE_BROKEN",
  "cif": "SYN000141",
  "occurred_at": "2026-09-03T15:10:00",
  "data": {}
}
```

### After
- Hành động: Xử lý cam kết thanh toán không thực hiện (PTP_RECOVERY)
- Kênh: Gọi điện (CALL)
- Quy tắc: NBA-210 (BROKEN_PTP_RECENT_INFLOW)

### Diff
- treatment: WAIT_SELF_CURE → PTP_RECOVERY
- channel: NONE → CALL
- rule_id: NBA-300 → NBA-210
- reason_code: CALL_SELF_CURE → BROKEN_PTP_RECENT_INFLOW
- ptp_state: NONE → BROKEN

### Vietnamese explanation
"Khách hàng không thực hiện cam kết thanh toán đã đưa ra. Sau khi đánh giá lại các tín hiệu hiện tại, hệ thống chuyển sang xử lý cam kết thanh toán không thực hiện."

## Reset / Replay Proof

The demo can be replayed reproducibly:

1. Send event → decision changes, timeline has 1 entry
2. Reset → overlay cleared, timeline cleared
3. Send same event again → identical before/after/diff

Verified by `TestResetReplayProof`:
- `test_replay_after_reset_produces_same_result`: before/after/diff identical after reset+replay
- `test_full_demo_cycle`: full cycle (event → verify → reset → replay → verify identical)

SYN002846 baseline is preserved: its accepted decision (WAIT_SELF_CURE, NBA-300)
remains unchanged after reset. Original synthetic data is never modified.

## Manual Demo Commands

### Send a demo event

```bash
curl -X POST \
  http://127.0.0.1:18080/demo/events \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id": "demo-001",
    "event_type": "CASH_IN_RECEIVED",
    "cif": "GOLDEN_G03",
    "occurred_at": "2026-09-03T10:03:00",
    "data": {"amount": 30000000}
  }'
```

### View timeline

```bash
curl -X GET \
  http://127.0.0.1:18080/demo/timeline/GOLDEN_G03 \
  -H 'Authorization: Bearer <TOKEN>'
```

### Reset demo state for a CIF

```bash
curl -X POST \
  http://127.0.0.1:18080/demo/reset/GOLDEN_G03 \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### Promise created event

```bash
curl -X POST \
  http://127.0.0.1:18080/demo/events \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id": "demo-002",
    "event_type": "PAYMENT_PROMISE_CREATED",
    "cif": "SYN000123",
    "occurred_at": "2026-09-03T14:20:00",
    "data": {"promise_date": "2026-09-04"}
  }'
```

### Promise broken event

```bash
curl -X POST \
  http://127.0.0.1:18080/demo/events \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id": "demo-003",
    "event_type": "PAYMENT_PROMISE_BROKEN",
    "cif": "SYN000141",
    "occurred_at": "2026-09-03T15:10:00",
    "data": {}
  }'
```

No real secrets in this report. Replace `<TOKEN>` with the actual `COLLECTION_TOOL_API_KEY`.

## Tests

### TASK-008B Demo Event Tests

| Test class | Tests | Result |
|---|---|---|
| TestCashInReceivedValid | 2 | OK |
| TestCashInReceivedInvalidAmount | 4 | OK |
| TestPaymentPromiseCreatedValid | 2 | OK |
| TestPaymentPromiseCreatedInvalidDate | 3 | OK |
| TestPaymentPromiseBrokenValid | 2 | OK |
| TestUnsupportedEventRejected | 2 | OK |
| TestUnknownCifNotFound | 2 | OK |
| TestOriginalDataUnchanged | 3 | OK |
| TestDemoOverlayPersists | 2 | OK |
| TestResetRemovesOverlay | 2 | OK |
| TestResetRemovesTimeline | 2 | OK |
| TestTimelineChronologicalOrder | 2 | OK |
| TestBeforeEqualsCurrentDemoState | 2 | OK |
| TestAfterUsesDeterministicReplay | 2 | OK |
| TestDiffDeterministic | 3 | OK |
| TestExplanationCannotChangeDecision | 3 | OK |
| TestReasoningContentNeverExposed | 3 | OK |
| TestDuplicateEventIdHandled | 3 | OK |
| TestAuthRequired | 6 | OK |
| TestPublicRoutesExplicit | 1 | OK |
| TestToolAllowlistRemainsTight | 2 | OK |
| TestRegressionsPreserved | 6 | OK |
| TestEventLabels | 2 | OK |
| TestHeroFlows | 4 | OK |
| TestResetReplayProof | 2 | OK |

TASK-008B subtotal: **67 passed, 0 failed, 0 skipped**

### Required Test Coverage (23 areas)

| # | Required test | Covered by |
|---|---|---|
| 1 | CASH_IN_RECEIVED valid event | TestCashInReceivedValid |
| 2 | CASH_IN_RECEIVED amount <= 0 rejected | TestCashInReceivedInvalidAmount |
| 3 | PAYMENT_PROMISE_CREATED valid | TestPaymentPromiseCreatedValid |
| 4 | promise_date invalid rejected | TestPaymentPromiseCreatedInvalidDate |
| 5 | PAYMENT_PROMISE_BROKEN valid | TestPaymentPromiseBrokenValid |
| 6 | unsupported fourth event rejected | TestUnsupportedEventRejected |
| 7 | unknown CIF → NOT_FOUND | TestUnknownCifNotFound |
| 8 | original accepted data unchanged | TestOriginalDataUnchanged |
| 9 | demo overlay persists across sequential events | TestDemoOverlayPersists |
| 10 | reset removes overlay | TestResetRemovesOverlay |
| 11 | reset removes timeline | TestResetRemovesTimeline |
| 12 | timeline chronological order | TestTimelineChronologicalOrder |
| 13 | before decision equals current demo state decision | TestBeforeEqualsCurrentDemoState |
| 14 | after decision uses deterministic TASK-007A replay | TestAfterUsesDeterministicReplay |
| 15 | diff is deterministic | TestDiffDeterministic |
| 16 | event explanation cannot change decision | TestExplanationCannotChangeDecision |
| 17 | reasoning_content never exposed | TestReasoningContentNeverExposed |
| 18 | duplicate event_id handled safely | TestDuplicateEventIdHandled |
| 19 | auth required for event endpoint | TestAuthRequired |
| 20 | auth required for reset | TestAuthRequired |
| 21 | public routes are explicit | TestPublicRoutesExplicit |
| 22 | existing public tool allowlist remains tight | TestToolAllowlistRemainsTight |
| 23 | TASK-001 through TASK-008 regressions remain PASS | TestRegressionsPreserved + all regression suites |

## Regression

### Compilation

```
python -m compileall -q src tests main.py tool_server.py  -> COMPILE_EXIT=0
```

### Accepted Business Tests (regression)

| Test file | Result |
|---|---|
| test_nba.py | OK (11 tests) |
| test_task007b.py (key classes) | OK |
| test_task008.py | OK (47 tests) |
| test_task008b.py | OK (67 tests) |

All existing regression suites remain PASS. The demo layer is purely additive.

## Business Drift

BUSINESS_SEMANTICS_DRIFT=0

Verified via `git diff HEAD -- src/msb_nba/ src/msb_policy/ src/msb_recovery/ src/msb_synthetic/ src/msb_context/ src/msb_evaluation/ src/msb_simulation/` = empty.

Accepted business engines unchanged:
- TASK-001 (src/msb_synthetic/) — unchanged
- TASK-002 (src/msb_policy/) — unchanged
- TASK-003 (src/msb_recovery/) — unchanged
- TASK-004 (src/msb_evaluation/) — unchanged
- TASK-005 (src/msb_context/) — unchanged
- TASK-006 (src/msb_tools/) — unchanged
- TASK-007A (src/msb_nba/) — unchanged
- TASK-007B (src/msb_agent/) — unchanged
- TASK-008 (src/msb_simulation/) — unchanged

TASK-008B is only: event adapter + temporary demo state + timeline + explanation.
No business rules duplicated. The demo engine delegates to `msb_nba.engine.decide` (TASK-007A).

## Files Created

| File | Purpose |
|---|---|
| src/msb_demo/__init__.py | Demo module package |
| src/msb_demo/models.py | DemoEvent, TimelineEntry, DecisionSnapshot, DiffEntry, event types, labels |
| src/msb_demo/engine.py | DemoEventEngine — in-memory overlay, event processing, diff, Vietnamese explanation |
| tests/test_task008b.py | 67 tests covering all 23 required test areas |
| task-results/TASK-008B-FINAL.md | This report |

## Files Modified

| File | Change |
|---|---|
| tool_server.py | Added three explicit demo routes (/demo/events, /demo/timeline/{cif}, /demo/reset/{cif}) with Bearer auth; added demo engine singleton; version bump to 0.4 |

## Git Status

```
M tool_server.py
?? src/msb_demo/
?? tests/test_task008b.py
?? task-results/TASK-008B-FINAL.md
```

Tracked modifications: 1
Untracked files: 3 (demo module, test file, report)

## Commit Status

NOT COMMITTED — WAITING FOR PRODUCT OWNER APPROVAL
