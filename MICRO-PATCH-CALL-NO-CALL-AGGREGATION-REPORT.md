# MICRO-PATCH — CALL/No-Call Aggregation

## 1. Executive Result

```
PATCH_STATUS=PASS
DEMO_READY=YES
```

## 2. Git State

```
HEAD_BEFORE=fe1de19 (TASK-018C closure)
HEAD_AFTER=414a0e88c4fa9283ea5ec4f7d2115b26bd604d68
RELATION_TO_TASK018C=fe1de19 is the TASK-018C closure commit; this patch fixes a bug introduced in TASK-018C (20bac38) where worklist counting was limited to top-5 rows.
RELATION_TO_MICRO_AUDIT_HEAD=Micro-audit confirmed canonical count=32 at fe1de19; this patch restores correct counting.
```

## 3. Root Cause

TASK-018C changed `build_morning_brief` and `_today_worklist_response` to only evaluate the top-5 scored rows for the CALL+NONE count. The top-5 contains 0 such cases, but the full portfolio contains 32. The fix restores full-portfolio counting while keeping top-3/5 for display only.

## 4. Code Change

| File | Change |
|---|---|
| `src/msb_agent/copilot.py` | `_today_worklist_response`: iterate `get_portfolio` with `final_route=CALL` across all pages, call NBA for each, count channel=NONE |
| `src/msb_zalo/chat.py` | `build_morning_brief`: iterate all CALL-routed rows in `repository.portfolio()`, call NBA for each, count channel=NONE; keep top-3 for display |
| `tests/test_micro_patch_call_no_call.py` | 9 focused tests |

## 5. Canonical Aggregation

```
TOTAL_PORTFOLIO_CIFS=3000
TOTAL_ROUTE_CALL=1740
CALL_BUT_NO_CALL_NOW=32
SYN002846_MATCHES=YES
```

## 6. Web Result

```
Hôm nay có 3000 hồ sơ có quyết định; 32 hồ sơ thuộc tuyến CALL nhưng chưa cần gọi ngay.
```

## 7. Zalo Result

```
Ưu tiên hôm nay (dữ liệu mô phỏng):
• 3000 hồ sơ có quyết định từ hệ thống
• 32 hồ sơ thuộc tuyến CALL nhưng chưa cần gọi ngay

Top 3 hồ sơ cần xem:
1. SYN001346
2. SYN000746
3. SYN002126
Điểm cơ hội và hành động đề xuất của từng hồ sơ đã có trong bảng tin sáng.
```

## 8. Parity

```
WEB_ZALO_WORKLIST_FACT_PARITY=100%
```

## 9. Regression

```
TASK017=410/410 PASS
TASK018=770/770 PASS
TASK018C=31/31 PASS
MICRO_PATCH=9/9 PASS
DIFF_CHECK=clean
```

## 10. Architecture Integrity

```
DECISION_CORE_CHANGED=NO
SIMULATION_CORE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0
AGENTBASE_PRIMARY_SEMANTIC_PATH=YES
```

## 11. Final Recommendation

**A. READY TO RECORD DEMO**
