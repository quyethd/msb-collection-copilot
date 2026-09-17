# Score Label User-Facing Fix Report

## Root Cause

Three issues:

1. **Production service stale**: The tool_server systemd service was running since Sep 16 (before TASK-018C code changes). It had old code that used `semantics.TREATMENT_VN.get(name, str(name))` for score components, which fell through to raw English enum names.

2. **Case brief context**: `src/msb_case_brief/context_builder.py` passed raw `component_breakdown` (containing `BUSINESS_URGENCY`, `ABILITY_TO_PAY`, etc.) to the LLM without mapping to Vietnamese labels.

3. **Routing gap**: "cho tôi xem chi tiết điểm" resolved to `CUSTOMER_SUMMARY` instead of `SCORE_BREAKDOWN` because "chi tiet" was not in the score breakdown markers, while "cho toi xem" matched case summary markers.

## Files Changed

| File | Change |
|---|---|
| `src/msb_agent/semantics.py` | Added "chi tiet" to score breakdown conditions (both CIF-specific and generic paths) |
| `src/msb_case_brief/context_builder.py` | Map component names via `map_score_component()` before passing to LLM |

## Production Response (After Fix)

```
Intent: SCORE_BREAKDOWN
Summary: Điểm cơ hội thu hồi của SYN002846 là 47/100.
Sections:
  • Mức khẩn cấp nghiệp vụ: 8/20
  • Khả năng thanh toán: 20/25
  • Mức sẵn sàng thanh toán: 4/20
  • Khả năng tiếp cận: 11/15
  • Thời điểm thuận lợi: 4/15
  • Điều chỉnh chiến lược: 0/5
  Tổng hợp các thành phần: 47.
```

## Test Results

| Question | Intent | Raw Enums | VN Labels | 47 | Pass |
|---|---|---|---|---|---|
| cách tính điểm | SCORE_BREAKDOWN | 0 | YES | YES | PASS |
| Cách tính điểm | SCORE_BREAKDOWN | 0 | YES | YES | PASS |
| Điểm 47 được tính như thế nào? | SCORE_BREAKDOWN | 0 | YES | YES | PASS |
| điểm này tính sao? | SCORE_BREAKDOWN | 0 | YES | YES | PASS |
| giải thích điểm | SCORE_BREAKDOWN | 0 | YES | YES | PASS |
| cho tôi xem chi tiết điểm | SCORE_BREAKDOWN | 0 | YES | YES | PASS |
| diem nay tinh sao | SCORE_BREAKDOWN | 0 | YES | YES | PASS |

## Regression

```
TASK017=410/410 PASS
TASK018=770/770 PASS
TASK018C=31/31 PASS
MICRO_PATCH=9/9 PASS
TOTAL=1220/1220 PASS
```

## Deploy

Production tool_server restarted via `systemctl restart msb-collection-tool-server.service`.
Production replay verified via HTTPS API call — all 6 Vietnamese labels present, 0 raw enums.
