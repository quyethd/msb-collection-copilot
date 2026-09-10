# TASK-011D PUBLIC FRONTEND FIX FINAL REPORT

## Status

TASK-011D PASS — PUBLIC FE LAYOUT AND SAFE API ROUTING PROVEN

## Root causes

- Browser customer/decision/simulation calls used protected `/tools/*` routes without a browser credential.
- The local frontend proxy had previously targeted a stale backend port; the verified local tool server is `127.0.0.1:18080`.
- Sidebar active styling was based on shared click targets, causing placeholder items to look active alongside the real page.
- Desktop overflow risk was not explicitly constrained for fixed sidebar, grids, and drawer surfaces.

## Safe API routing

Before:

- Browser → `/tools/get_customer_360`
- Browser → `/tools/get_next_best_action`
- Browser → `/tools/simulate_decision`

After:

- Browser → `/demo/customer-360` → existing `get_customer_360` registry function
- Browser → `/demo/next-best-action` → existing `get_next_best_action` registry function
- Browser → `/demo/simulate` → existing `simulate_decision` registry function

The new adapters validate synthetic demo CIFs, require no browser credential, and do not duplicate business rules. Existing `/tools/*` Bearer protection remains intact. The existing `/agent-tools/*` proxy assumptions were not changed.

## Frontend and sidebar

- Central `toolData` boundary normalizes `{ data: ... }` and direct payloads.
- Primary SYN002846 UI remains Vietnamese and maps the accepted decision to `Chờ khách hàng tự thanh toán` and `Chưa cần liên hệ`.
- Only Trang chủ, Khách hàng, or Tác động dự kiến can be active for their corresponding page.
- Inactive nav hover is neutral/light and distinct from active styling.
- MSB branding, attribution, CTA spacing, drawer width, and overflow guards were polished for desktop layouts.

## Local SYN002846 proof

- Browser-safe customer adapter: HTTP 200; outstanding `273000000`; max DPD `11`; inflow 7d `48000000`; net cashflow 30d `168000000`.
- Browser-safe NBA adapter: HTTP 200; route `CALL`; treatment `WAIT_SELF_CURE`; channel `NONE`; recovery score `47`.
- Browser-safe simulation adapter: HTTP 200; before/after result present.
- Frontend proxy integration: root, customer, NBA, simulation, portfolio, timeline, and impact all HTTP 200 on loopback.

## Security QA

- `FRONTEND_SECRET_SCAN=PASS` — no tool key, bearer secret, client secret, or LLM key in the production bundle.
- Protected `/tools/get_customer_360`: missing Bearer `401`; wrong Bearer `401`; current Bearer `200`.
- No public-domain request was made from this server.

## Tests and build

- New backend demo adapter tests: 3/3 PASS.
- Focused TASK-008 simulation/server regressions: PASS.
- Frontend unit tests: 7/7 PASS.
- Production build: PASS.
- BUSINESS_SEMANTICS_DRIFT=0.

## Public docroot deployment

- Source: `/opt/msb-collection-copilot/frontend/dist`
- Destination: `/www/wwwroot/msb-collection-copilot.duckdns.org`
- Backup: `/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260904T234735Z`
- `index.html` source/deployed SHA-256: MATCH.
- Deployed frontend ownership: `www:www`.
- Non-frontend docroot files preserved.

NOT COMMITTED.
