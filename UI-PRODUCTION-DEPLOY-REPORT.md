# UI Production Deploy Report

## 1. Deploy Status

```
DEPLOY_STATUS=PASS
SOURCE_HEAD=f0f430d
DEPLOYED_HEAD=f0f430d
PRODUCTION_NEW_ASSETS=YES
```

## 2. Build Verification

```
TypeScript: PASS (0 errors)
Vite build: PASS
CSS bundle: 87.59 KB (index-BFEZxQG4.css)
JS bundle: 284.37 KB (index-DIg_-M8T.js)
```

New CSS contains: `login-page`, `login-card`, `admin-toggle`, `admin-children`, `admin-child` classes.

## 3. Backup

```
BACKUP_PATH=/opt/backups/msb-prod-20260917110039
```

Previous production assets backed up before deployment.

## 4. Deployment

Method: Copy built files from `frontend/dist/` to `/www/wwwroot/msb-collection-copilot.duckdns.org/` (OpenLiteSpeed docRoot).

Old assets cleaned. Production `index.html` now references:
- CSS: `/assets/index-BFEZxQG4.css`
- JS: `/assets/index-DIg_-M8T.js`

## 5. Production Verification

### Asset serving (hostname-preserving method)
```
curl -sk -H "Host: msb-collection-copilot.duckdns.org" https://127.0.0.1/login
→ <script src="/assets/index-DIg_-M8T.js"></script>
→ <link href="/assets/index-BFEZxQG4.css">
```

### CSS content verification
```
Deployed CSS contains:
  login-page ✅
  admin-toggle ✅
  admin-children ✅
```

### Redirect verification
```
Source (public-pages.tsx):
  Line 83: window.location.replace('/app')  — pre-auth check
  Line 90: window.location.replace('/app')  — login submit

JS bundle:
  location.replace(`/app`)  — login success (no next param)
  location.replace(`/app`)  — pre-auth redirect

LOGIN_REDIRECT_WITH_ZALO_NEXT=/app ✅
```

## 6. Login CSS

```
LOGIN_CSS_APPLIED=YES
```

Login page now has dedicated CSS in `public.css` with:
- Inter font family (matching landing)
- Navy #102b50 / Orange #f15a24 palette (matching landing tokens)
- Styled inputs with focus states
- Styled submit button
- Proper spacing and card layout
- Responsive (mobile-friendly)
- Brand header with MSB logo mark

## 7. Sidebar/Admin

```
ADMIN_DEFAULT_COLLAPSED=YES
ADMIN_EXPAND=PASS
ADMIN_COLLAPSE=PASS
ADMIN_ZALO_ACTIVE=PASS
```

Sidebar structure:
1. Tổng quan
2. Danh sách ưu tiên
3. Khách hàng
4. Quản trị (collapsed by default, chevron indicator)
   - Tác động dự kiến (hidden when collapsed)
   - Điều khiển Demo Zalo (hidden when collapsed)
5. Trợ lý Thu hồi Nợ
6. Đăng xuất

Auto-expand when route is `/app/zalo` or `/app/impact`.

## 8. Business Smoke

```
WORKLIST_TOTAL=3000
WORKLIST_CALL_NO_CALL=32
SYN002846_SCORE=47
SIMULATION_INFLOW_7D_0_TREATMENT=CONTACT
SIMULATION_INFLOW_7D_0_CHANNEL=CALL
```

No business logic affected by UI deployment.

## 9. Architecture Integrity

```
SOURCE_CODE_CHANGED=NO (no code changes during deploy)
DECISION_CORE_CHANGED=NO
SIMULATION_CORE_CHANGED=NO
AGENTBASE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0
```

## 10. Evidence

- `UI-PRODUCTION-DEPLOY-EVIDENCE/prod-login-html.txt` — production /login HTML
- `UI-PRODUCTION-DEPLOY-EVIDENCE/prod-css-deployed.css` — deployed CSS bundle
- `UI-PRODUCTION-DEPLOY-EVIDENCE/prod-js-deployed.js` — deployed JS bundle
- `UI-PRODUCTION-DEPLOY-EVIDENCE/redirect-verification.txt` — redirect logic verification

## 11. Final Recommendation

**A. READY FOR VIDEO RECORDING**

Production is serving the new UI with:
- Styled login page (no more browser-default HTML)
- Login always redirects to /app (no /app/zalo)
- Admin menu collapsed by default with expand/collapse
- Business behavior unchanged (3000/32/47)
