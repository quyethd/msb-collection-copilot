# TASK-011C LOCAL FRONTEND FINAL REPORT

## Status

TASK-011C PASS — LOCAL FRONTEND DATA AND SIDEBAR PROVEN

## Root cause

The local tool server returns an accepted envelope shaped as `{ ok, tool, data, error, meta }`. The frontend correctly needs the nested `data` payload, but its Vite proxy was reading the stale `.env` base URL `http://127.0.0.1:8000` instead of the verified tool server at `http://127.0.0.1:18080`. The frontend also had no boundary normalization for an equivalent direct-payload response.

## Local response and mapping

- `get_customer_360`: `data.debt.total_outstanding_cif`, `data.debt.max_dpd_cif`, `data.cashflow.inflow_7d`, `data.cashflow.net_cashflow_30d`, `data.ptp.status`, and `data.recovery_opportunity.recovery_opportunity_score`.
- `get_next_best_action`: `data.final_route=CALL`, `data.treatment=WAIT_SELF_CURE`, `data.channel=NONE`, `data.rule_id=NBA-300`.
- Added `toolData(response) => response.data ?? response` at the frontend boundary.
- Primary UI remains Vietnamese: `Chờ khách hàng tự thanh toán` and `Chưa cần liên hệ`; raw internal codes remain only in technical detail views.

## Sidebar changes

- Only the actual current page item is active.
- Inactive customer-related items remain neutral.
- MSB product name and GreenNode attribution keep readable single-line spacing at desktop width.
- Assistant CTA is distinct, wider, and consistently aligned.

## Files changed

- `frontend/src/main.tsx`
- `frontend/src/styles.css`
- `frontend/src/ui-contract.test.ts`
- `frontend/vite.config.ts`
- `task-results/TASK-011C-LOCAL-FE-FINAL.md`

## QA

- Local backend: PASS (`127.0.0.1:18080` only)
- Frontend proxy integration: PASS (HTTP 200, SYN002846 decision/data present)
- Frontend unit tests: 6/6 PASS
- Production build: PASS (`tsc -b && vite build`)
- Frontend secret scan: PASS
- BUSINESS_SEMANTICS_DRIFT=0
- NOT COMMITTED

## Public Docroot Deployment

- Source dist path: `/opt/msb-collection-copilot/frontend/dist`
- Destination docroot: `/www/wwwroot/msb-collection-copilot.duckdns.org`
- Backup path: `/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260904T121503Z`
- Build result: `FRONTEND_BUILD=PASS`
- Deployment result: `DOCROOT_DEPLOY=PASS`
- `index.html` checksum match: `DEPLOYED_BUILD_MATCH=PASS`
- Asset filename references: `PASS`
- Ownership: `OWNERSHIP=PASS` (`www:www`)
- Deployed timestamp: `2026-09-04T12:15:03Z`
- Non-frontend docroot files preserved: `PASS`
- Public-domain requests from this server: none
- NOT COMMITTED
