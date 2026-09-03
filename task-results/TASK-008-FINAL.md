# TASK-008 FINAL REPORT

## Final Status

TASK-008 PASS — DECISION SIMULATION ENGINE PROVEN

## What Was Built

A small, deterministic, demo-oriented Decision Simulation Engine that answers:

"Nếu tình trạng khách hàng thay đổi, quyết định thu hồi có thay đổi không,
và thay đổi vì lý do gì?"

The engine applies temporary what-if changes to an immutable copy of the
customer snapshot, replays the accepted TASK-007A NBA engine, and produces
a structured before/after/diff comparison with Vietnamese display labels.

The original customer data is NEVER mutated.
The simulation NEVER duplicates business rules.
The LLM NEVER calculates simulation results.

## Simulation Architecture

```
CURRENT CUSTOMER SNAPSHOT (from TASK-005 via ToolRepository)
        ↓
APPLY WHAT-IF CHANGES (deep copy, modify only explicit fields)
        ↓
TEMPORARY SIMULATION SNAPSHOT (immutable, never written back)
        ↓
EXISTING DETERMINISTIC ENGINES (msb_nba.engine.decide — TASK-007A)
        ↓
NEW DECISION (NBADecision from accepted engine)
        ↓
DECISION DIFF (structured field-by-field comparison)
        ↓
OPTIONAL GREENNODE EXPLANATION (LLM explains, never calculates)
```

## Supported Changes

| Field | Description | Validation |
|---|---|---|
| inflow_7d | Tiền vào 7 ngày gần nhất | integer |
| net_cashflow_30d | Dòng tiền ròng 30 ngày | integer |
| ptp_state | Trạng thái cam kết thanh toán | NONE, OPEN, KEPT, PARTIAL, BROKEN |
| promise_date | Ngày cam kết thanh toán | YYYY-MM-DD or null |
| source_next_action_date | Ngày dự kiến xử lý tiếp theo | ISO datetime or null |
| latest_business_outcome | Kết quả tương tác gần nhất | UTC, PTP, NPTP, RTP, THIRT, NIN, NA or null |

Unknown fields: REJECTED (INVALID_ARGUMENT).
Invalid values: REJECTED (INVALID_ARGUMENT).
Unknown CIF: NOT_FOUND.

## Immutable Data Proof

The simulation engine uses `copy.deepcopy(context)` to create a temporary
snapshot. Changes are applied only to the copy. The original repository
data is never modified.

Verified by `TestImmutableSnapshot`:
- `test_context_unchanged_after_simulation`: context before == context after
- `test_all_contexts_unchanged_after_multiple_simulations`: multiple CIFs, multiple changes, all unchanged

## Deterministic Replay Proof

The simulation engine calls `msb_nba.engine.decide(modified_context, calls, DEFAULT_CONFIG)`
— the exact same function used by TASK-007A. No business rules are duplicated.

Verified by `TestReplayUsesNbaEngine`:
- `test_before_decision_matches_decide`: before decision == `decide(original_context, calls)`
- `test_after_decision_from_modified_context`: after decision == `decide(modified_context, calls)`

## Decision Diff Proof

The diff engine compares these fields:
- final_route
- recovery_opportunity_score
- treatment
- channel
- objective
- when
- rule_id
- reason_code

Plus the changed input fields (inflow_7d, net_cashflow_30d, ptp_state, etc.)

Each diff entry: `{"field": "...", "before": ..., "after": ...}`

Verified by `TestDecisionDiff`:
- `test_diff_contains_changed_fields`
- `test_diff_before_after_values`

## Agent SIMULATE Proof

TASK-007B's SIMULATE mode previously returned `TASK_008_REQUIRED`.
Now SIMULATE is enabled:

```
User → SIMULATE(cif, changes)
  → simulate_decision tool
  → SimulationEngine.simulate(cif, changes)
  → structured before/after/diff
  → AgentResponse with simulation data
  → optional LLM Vietnamese explanation
```

The LLM receives ONLY the completed simulation result.
The LLM NEVER calculates the new decision.
The LLM NEVER changes before/after/diff/rule_id/treatment/channel/objective/when/score.

Verified by `TestLlmCannotModifyResult`:
- `test_adversarial_llm_preserves_simulation`: adversarial LLM content does not change simulation
- `test_simulation_identical_with_without_llm`: simulation result is identical with and without LLM

## Vietnamese Demo Labels

### Treatment Labels

| Internal | Vietnamese |
|---|---|
| WAIT | Chờ theo dõi |
| WAIT_SELF_CURE | Chờ khách hàng tự thanh toán |
| REMIND | Nhắc thanh toán |
| CONTACT | Liên hệ khách hàng |
| PTP_FOLLOW_UP | Theo dõi cam kết thanh toán |
| PTP_RECOVERY | Xử lý cam kết thanh toán không thực hiện |
| PARTIAL_PAYMENT | Theo dõi khoản thanh toán một phần |
| CALLBACK | Gọi lại theo lịch hẹn |
| VERIFY_CONTACT | Xác minh thông tin liên hệ |
| ESCALATE | Chuyển mức xử lý cao hơn |

### Channel Labels

| Internal | Vietnamese |
|---|---|
| CALL | Gọi điện |
| SMS | Tin nhắn SMS |
| ZALO | Zalo |
| EMAIL | Email |
| NONE | Chưa cần liên hệ |

### Field Labels

| Internal | Vietnamese |
|---|---|
| inflow_7d | Tiền vào 7 ngày gần nhất |
| net_cashflow_30d | Dòng tiền ròng 30 ngày |
| ptp_state | Trạng thái cam kết thanh toán |
| promise_date | Ngày cam kết thanh toán |
| treatment | Hành động đề xuất |
| channel | Kênh xử lý |
| recovery_opportunity_score | Điểm cơ hội thu hồi |
| reason_code | Lý do quyết định |
| final_route | Tuyến xử lý |

## Hero Scenario A

**SCENARIO_A_CASHFLOW_CHANGE** — GOLDEN_G03

Changes: `{"inflow_7d": 20000000, "net_cashflow_30d": 50000000}`

Before:
- Hành động: Liên hệ khách hàng
- Kênh: Gọi điện
- Quy tắc: NBA-900 (Xử lý mặc định)

After:
- Hành động: Chờ khách hàng tự thanh toán
- Kênh: Chưa cần liên hệ
- Quy tắc: NBA-300 (Đáp ứng điều kiện chờ tự thanh toán)

Diff:
- treatment: CONTACT → WAIT_SELF_CURE
- channel: CALL → NONE
- rule_id: NBA-900 → NBA-300
- inflow_7d: 0 → 20000000
- net_cashflow_30d: 0 → 50000000

Vietnamese explanation: Sau khi xuất hiện dòng tiền tích cực trong những ngày gần đây, khách hàng đáp ứng các điều kiện để ưu tiên chờ tự thanh toán thay vì liên hệ ngay.

## Hero Scenario B

**SCENARIO_B_BROKEN_PROMISE** — SYN000141

Changes: `{"ptp_state": "BROKEN"}`

Before:
- Hành động: Chờ khách hàng tự thanh toán
- Kênh: Chưa cần liên hệ
- Quy tắc: NBA-300 (Đáp ứng điều kiện chờ tự thanh toán)

After:
- Hành động: Xử lý cam kết thanh toán không thực hiện
- Kênh: Gọi điện
- Quy tắc: NBA-210 (Cam kết không thực hiện, có dòng tiền gần đây)

Diff:
- treatment: WAIT_SELF_CURE → PTP_RECOVERY
- channel: NONE → CALL
- rule_id: NBA-300 → NBA-210
- ptp_state: NONE → BROKEN

Vietnamese explanation: Khách hàng không thực hiện cam kết thanh toán trước đó, vì vậy hệ thống chuyển từ chờ theo dõi sang chủ động xử lý.

## Hero Scenario C

**SCENARIO_C_OPEN_PROMISE** — GOLDEN_G03

Changes: `{"ptp_state": "OPEN", "promise_date": "2026-09-15"}`

Before:
- Hành động: Liên hệ khách hàng
- Kênh: Gọi điện
- Quy tắc: NBA-900 (Xử lý mặc định)

After:
- Hành động: Theo dõi cam kết thanh toán
- Kênh: Gọi điện
- Thời điểm: Theo ngày cam kết: 2026-09-15
- Quy tắc: NBA-230 (Đang cam kết thanh toán)

Diff:
- treatment: CONTACT → PTP_FOLLOW_UP
- objective: PAYMENT → PTP_KEEP
- when: BEST_WINDOW → SOURCE_DATE (2026-09-15)
- rule_id: NBA-900 → NBA-230
- ptp_state: NONE → OPEN
- promise_date: null → 2026-09-15

Vietnamese explanation: Khách hàng đã có ngày cam kết thanh toán cụ thể, vì vậy hệ thống chuyển sang theo dõi cam kết vào đúng thời điểm thay vì tiếp tục liên hệ theo cách mặc định.

## SYN002846 Scenario

**SYN002846_REVERSE_SELF_CURE**

Changes: `{"inflow_7d": 0, "net_cashflow_30d": 0}`

Before:
- Hành động: Chờ khách hàng tự thanh toán
- Kênh: Chưa cần liên hệ
- Quy tắc: NBA-300 (CALL_SELF_CURE)

After:
- Hành động: Liên hệ khách hàng
- Kênh: Gọi điện
- Quy tắc: NBA-900 (CALL_DEFAULT)

Diff:
- treatment: WAIT_SELF_CURE → CONTACT
- channel: NONE → CALL
- rule_id: NBA-300 → NBA-900
- inflow_7d: 48000000 → 0
- net_cashflow_30d: 168000000 → 0

Vietnamese explanation: Sau khi dòng tiền gần đây giảm, khách hàng không còn đáp ứng các điều kiện để tiếp tục chờ tự thanh toán. Hệ thống vì vậy chuyển sang đề xuất liên hệ.

This is the reverse of the hero case: route is CALL, self-cure was active,
reducing cashflow removes self-cure eligibility, and the decision reverts
to CONTACT (NBA-900).

## Public Tool Allowlist

The tool server uses an explicit allowlist. Only these tools are exposed externally:

```
PUBLIC_TOOL_ALLOWLIST = frozenset({
    "get_customer_360",
    "get_next_best_action",
    "simulate_decision",
})
```

All other registered tools (get_portfolio, get_collection_history,
get_cashflow_intelligence, get_collection_policy, get_recovery_opportunity)
are blocked at the tool server with HTTP 404.

Verified by `TestToolServerAllowlist`:
- `test_allowlist_is_explicit_and_tight`
- `test_non_public_tool_blocked`: 5 non-public tools return 404
- `test_simulate_decision_accessible_via_tool_server`

## Security

| Control | Status |
|---|---|
| Immutable snapshot | PASS — deep copy, original data never mutated |
| No filesystem access | PASS — simulation only reads from repository |
| No shell execution | PASS |
| No SQL passthrough | PASS |
| No arbitrary Python invocation | PASS |
| Explicit tool allowlist | PASS — only 3 tools exposed |
| reasoning_content | Not exposed in any response |
| Secrets | Not in source, not in response, not in artifacts |
| No fabricated metrics | No recovery_rate, amount_recovered, ROI, AEV, etc. |

## Regression Tests

### Compilation

```
python -m compileall -q src tests main.py tool_server.py  -> COMPILE_EXIT=0
```

### Accepted Business Tests (regression)

| Test file | Tests | Result |
|---|---|---|
| test_synthetic_data.py | 4 | OK |
| test_policy_engine.py | 25 | OK |
| test_recovery_engine.py | 26 | OK |
| test_evaluation_engine.py | 13 | OK |
| test_context_assembly.py | 14 | OK |
| test_tools.py | 16 | OK |
| test_nba.py | 11 | OK |
| test_task007b_spike.py | 5 | OK |
| test_task007b.py | 48 | OK |

Accepted subtotal: 162 passed, 0 failed, 0 skipped

### TASK-008 Simulation Tests

| Test class | Tests | Result |
|---|---|---|
| TestUnknownCif | 2 | OK |
| TestUnsupportedField | 2 | OK |
| TestInvalidPtpState | 2 | OK |
| TestImmutableSnapshot | 2 | OK |
| TestReplayUsesNbaEngine | 2 | OK |
| TestBeforeMatchesTask007A | 1 | OK |
| TestAfterFromModifiedSnapshot | 1 | OK |
| TestDecisionDiff | 2 | OK |
| TestNoDecisionChange | 2 | OK |
| TestSyn002846Reproducible | 1 | OK |
| TestBrokenPtpScenario | 2 | OK |
| TestOpenPtpScenario | 2 | OK |
| TestLlmCannotModifyResult | 2 | OK |
| TestReasoningContentNeverExposed | 2 | OK |
| TestVietnameseLabels | 6 | OK |
| TestNoFabricatedMetrics | 2 | OK |
| TestToolServerAllowlist | 3 | OK |
| TestRegressionsPreserved | 4 | OK |
| TestDisplayProjection | 4 | OK |
| TestAllHeroScenarios | 3 | OK |

TASK-008 subtotal: 47 passed, 0 failed, 0 skipped

### Required Test Coverage (18 areas)

| # | Required test | Covered by |
|---|---|---|
| 1 | unknown CIF → NOT_FOUND | TestUnknownCif |
| 2 | unsupported change field → validation error | TestUnsupportedField |
| 3 | invalid PTP state → validation error | TestInvalidPtpState |
| 4 | original customer state remains unchanged | TestImmutableSnapshot |
| 5 | replay uses accepted deterministic NBA engine | TestReplayUsesNbaEngine |
| 6 | before decision matches normal TASK-007A output | TestBeforeMatchesTask007A |
| 7 | after decision is produced from modified snapshot | TestAfterFromModifiedSnapshot |
| 8 | decision diff is correct | TestDecisionDiff |
| 9 | no decision change returns decision_changed=false | TestNoDecisionChange |
| 10 | SYN002846 simulation is reproducible | TestSyn002846Reproducible |
| 11 | broken PTP scenario | TestBrokenPtpScenario |
| 12 | open PTP scenario | TestOpenPtpScenario |
| 13 | LLM cannot modify simulation result | TestLlmCannotModifyResult |
| 14 | reasoning_content never exposed | TestReasoningContentNeverExposed |
| 15 | Vietnamese display labels exist | TestVietnameseLabels |
| 16 | no future-task business metrics fabricated | TestNoFabricatedMetrics |
| 17 | tool server uses explicit allowlist | TestToolServerAllowlist |
| 18 | TASK-001 through TASK-007B regressions remain PASS | TestRegressionsPreserved + all regression suites |

### Total

```
209 tests run, 209 passed, 0 failed, 0 skipped
```

## Business Drift

BUSINESS_SEMANTICS_DRIFT=0

Verified via `git diff HEAD -- src/msb_nba/ src/msb_policy/ src/msb_recovery/ src/msb_synthetic/ src/msb_context/ src/msb_evaluation/` = empty.

Accepted business engines unchanged:

- TASK-001 (src/msb_synthetic/) — unchanged
- TASK-002 (src/msb_policy/) — unchanged
- TASK-003 (src/msb_recovery/) — unchanged
- TASK-004 (src/msb_evaluation/) — unchanged
- TASK-005 (src/msb_context/) — unchanged
- TASK-006 (src/msb_tools/) — tool #8 registered, tool count updated, allowlist added
- TASK-007A (src/msb_nba/) — unchanged
- TASK-007B (src/msb_agent/) — SIMULATE mode enabled, simulation field added

The simulation engine delegates to `msb_nba.engine.decide` (TASK-007A).
No business rules duplicated.

## Files Created

| File | Purpose |
|---|---|
| src/msb_simulation/__init__.py | Simulation module package |
| src/msb_simulation/models.py | SimulationResult, DecisionSnapshot, DiffEntry, supported changes |
| src/msb_simulation/labels.py | Vietnamese display labels for fields, treatments, channels, reasons |
| src/msb_simulation/engine.py | SimulationEngine — immutable snapshot, replay, diff |
| src/msb_simulation/display.py | Display projection for demo/UI consumption |
| src/msb_simulation/scenarios.py | Hero demo scenarios A, B, C, SYN002846 |
| tests/test_task008.py | 47 tests covering all 18 required test areas |
| task-results/TASK-008-FINAL.md | This report |

## Files Modified

| File | Change |
|---|---|
| main.py | Updated parse_payload call for 4-tuple (mode, cif, message, changes) |
| src/msb_agent/models.py | Added simulation field to AgentResponse; updated AGENT_VERSION to TASK-008-V1 |
| src/msb_agent/router.py | parse_payload now extracts changes from payload |
| src/msb_agent/runtime.py | Replaced SIMULATE stub with real simulation via simulate_decision tool |
| src/msb_tools/tools.py | Added simulate_decision tool function (delegates to SimulationEngine) |
| src/msb_tools/registry.py | Registered simulate_decision as tool #8 |
| src/msb_tools/schemas.py | Added SimulateDecisionOutput schema, tool entry, description; tool_count=8 |
| src/msb_tools/validate.py | Updated tool count to 8; added PUBLIC_TOOL_ALLOWLIST |
| tests/test_task007b.py | Updated SIMULATE tests for enabled mode; updated registry count to 8 |
| tests/test_tools.py | Updated registry, schema count, samples for 8 tools |
| tool_server.py | Replaced generic TOOL_REGISTRY dispatch with explicit PUBLIC_TOOL_ALLOWLIST |

## Git Status

```
M main.py
M src/msb_agent/models.py
M src/msb_agent/router.py
M src/msb_agent/runtime.py
M src/msb_tools/registry.py
M src/msb_tools/schemas.py
M src/msb_tools/tools.py
M src/msb_tools/validate.py
M tests/test_task007b.py
M tests/test_tools.py
M tool_server.py
?? src/msb_simulation/
?? tests/test_task008.py
?? task-results/TASK-008-FINAL.md
```

Tracked modifications: 11
Untracked files: 3 (simulation module, test file, report)

## Commit Status

NOT COMMITTED — WAITING FOR PRODUCT OWNER APPROVAL
