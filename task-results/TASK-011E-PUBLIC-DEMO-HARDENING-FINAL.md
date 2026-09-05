# TASK-011E Public Demo Hardening

TASK-011E PASS — PUBLIC DEMO HARDENING PROVEN

## Current status — September 5, 2026

```text
SERVER_DEFAULT_DNS_PATH=BLOCKED_BY_FORTIGUARD
PUBLIC_NAT_IP=103.233.48.100
PUBLIC_NAT_TLS=PASS
LOCAL_BACKEND=PASS
VIDEOSAAS_HANDLER_FIX=PASS
OLS_GLOBAL_CONFIG_VALIDATION=PASS_WITH_WARNINGS
OLS_PRE_RELOAD_VALIDATION=PASS
MSB_DISK_ROUTING_CONFIG=PASS
OLS_RELOAD=PASS
PUBLIC_DEMO_NBA=PASS
OLS_PUBLIC_ROUTING=PASS
PUBLIC_BROWSER_API_MATRIX=OWNER_VERIFIED_PASS
PUBLIC_BROWSER_TIMELINE=OWNER_VERIFIED_PASS
PUBLIC_API_SPA_LEAK=0 (owner-provided proof for NBA route only)
PUBLIC_DEMO_API_JSON=OWNER_VERIFIED_PASS
FINAL_PRIMARY_NAV=PASS
OVERVIEW_TWO_CHARTS=PASS
PRIORITY_PAGE=PASS
NAV_ACTIVE_HOVER=PASS
RESPONSIVE_LAYOUT=PASS
FRONTEND_TESTS=PASS
FRONTEND_BUILD=PASS
DOCROOT_DEPLOY=PASS
DEPLOYED_BUILD_MATCH=PASS
OWNERSHIP=PASS
POST_DEPLOY_PUBLIC_SMOKE=OWNER_VERIFIED_PASS (product-owner browser evidence)
PUBLIC_PROTECTED_TOOL_AUTH=PASS (owner-verified)
PUBLIC_AGENT_TOOL_AUTH=PASS (owner-verified)
PUBLIC_AGENT_TOOL_DATA=PASS (owner-verified)
BUSINESS_SEMANTICS_DRIFT=0
AGENTBASE_LIVE_CALL=PASS
AGENTBASE_NBA_TOOL_USE=PASS
AGENTBASE_TOOL_CORRELATION=PASS
AGENTBASE_DECISION_FIDELITY=PASS
AGENTBASE_SECOND_DECISION_FIDELITY=PASS
AGENTBASE_UNKNOWN_CIF_NO_FABRICATION=PASS
AGENTBASE_OVERRIDE_GUARDRAIL=PASS
NO_PRIVATE_REASONING_LEAK=PASS
COMMIT AUDIT PENDING
```

Public NAT TLS, public NBA, public protected-tool auth, public AgentBase gateway auth/data, and post-deployment browser smoke are owner-verified. The owner confirms the frontend loads, browser APIs and timeline work, SYN002846 renders, and the previous demo auth issue is resolved. The browser matrix is OWNER_VERIFIED_PASS. The reported HTTP/2 200 NBA response was application/json with NBA-300 / CALL / WAIT_SELF_CURE / NONE / score 47. The existing AgentBase runtime was then updated in place to version 7 and all required live proof gates passed, as recorded in the TASK-011 evidence file.

## Complete Frontend API Surface and Auth Fix

Inspected every request in `frontend/src/main.tsx` and searched the remaining frontend source. The actual browser API surface is:

| Method | Path | Used by browser | Expected auth | Purpose | Live local result |
|---|---|---|---|---|---|
| POST | `/demo/customer-360` | Yes | None; synthetic CIF | Customer context | 200 JSON |
| POST | `/demo/next-best-action` | Yes | None; synthetic CIF | Deterministic decision | 200 JSON |
| POST | `/demo/simulate` | Yes | None; synthetic CIF | Scenario explorer | 200 JSON |
| POST | `/demo/portfolio` | Yes | None; synthetic repository | Overview/priority data | 200 JSON |
| GET | `/demo/timeline/{cif}` | Yes | None; synthetic CIF | Decision timeline | 200 JSON |
| POST | `/demo/events` | Yes | None; synthetic CIF | Accepted in-memory demo events | 200 JSON |
| POST | `/demo/reset/{cif}` | Yes | None; synthetic CIF | Reset demo overlay | 200 JSON |
| POST | `/demo/impact` | Yes | None; synthetic repository | Existing impact formulas | 200 JSON |
| POST | `/demo/copilot` | Yes | None; synthetic CIF | Existing assistant | 200 JSON, application status success |
| POST | `/tools/get_customer_360` | No | Bearer required | Protected tool | Missing/wrong 401; current key 200 JSON |
| POST | `/tools/get_next_best_action` | No | Bearer required | Protected NBA | Missing/wrong 401; current key 200 JSON |
| POST | `/tools/simulate_decision` | No | Bearer required | Protected simulation | Not rerun live |
| GET | `/agent-tools/health` | No | Existing health rewrite unchanged | Gateway health | Not rerun |
| POST | `/agent-tools/get_customer_360`, `/agent-tools/get_next_best_action`, `/agent-tools/simulate_decision` | No | Bearer required | Existing AgentBase gateway rewrites | Not rerun publicly |

The timeline 401 came from its explicit `_require_auth()` call. Other browser POST routes, except the three TASK-011D adapters, fell through the protected default. Vite injected a key server-side into demo requests, masking that production mismatch.

`is_browser_safe_demo_route(method, path)` now centrally allowlists exactly the seven static POST routes and single-segment timeline GET/reset POST paths. All other paths retain auth requirements. Central demo validation rejects non-demo CIFs and repositories containing non-demo CIFs, including aggregate endpoints. Unknown synthetic customers retain safe repository errors. Non-object JSON receives 400 instead of causing `.get()` failures. No business logic or tool registry changed. The demo event engine still owns the accepted in-memory mutations.

The Vite demo proxy now forwards without credentials, and its unused protected-tool proxy was removed. React was not given a key or Authorization header.

Files changed in the earlier auth continuation: `tool_server.py`, `frontend/vite.config.ts`, `tests/test_task011d.py`, and this report. The final UI continuation did not change backend/auth or business modules. Its changed files are `frontend/src/main.tsx`, `frontend/src/pages.tsx`, `frontend/src/navigation.css`, `frontend/src/pages.test.tsx`, `frontend/src/ui-contract.test.ts`, `frontend/layout-qa.mjs`, and this report. TASK-011F was not touched or integrated.

## Root Causes

Default DNS sends this host to a FortiGuard blocking endpoint serving a self-signed blocking-page certificate. This is separate from the public site's TLS. The public NAT address above is not the hidden server address. No hidden server address was discovered or recorded.

The videosaas `/api/` proxy context incorrectly referenced `http://127.0.0.1:8000` as a handler name. The existing external processor is named `backend_api`. Changing only that reference removed the blocking handler error. Existing configuration and a local listener corroborated port 8000; no backend address was invented or changed.

MSB already had correct `/demo/` and `/tools/` proxy contexts. Its final SPA fallback lacked API exclusions. Three exclusions now prevent `/demo`, `/tools`, and `/agent-tools` prefixes, including their slash-prefixed descendants, from matching that fallback. Public browser behavior and protected gateway access are owner-verified.

The pre-edit MSB config mtime was September 4 at 23:25:31 UTC; LiteSpeed processes started at 23:31:10 UTC. These timestamps alone do not support the hypothesis that those processes predated the proxy contexts, nor prove which configuration was loaded.

## Configuration Changes and Backups

- Modified `/www/server/panel/vhost/openlitespeed/proxy/videosaas.duckdns.org/api.conf`: handler changed to `backend_api` only.
- Backup: `/www/server/panel/vhost/openlitespeed/proxy/videosaas.duckdns.org/api.conf.backup-task011e-20260905T005141Z`.
- Modified `/www/server/panel/vhost/openlitespeed/detail/msb-collection-copilot.duckdns.org.conf`: added `REQUEST_URI` exclusions `!^/demo(/|$)`, `!^/tools(/|$)`, and `!^/agent-tools(/|$)` immediately before the final SPA fallback conditions.
- Backup: `/www/server/panel/vhost/openlitespeed/detail/msb-collection-copilot.duckdns.org.conf.backup-task011e-20260905T005521Z`.

The OLS and application auth work above was completed in earlier continuations. The latest continuation changed frontend presentation only; SSL, DNS, backend auth, agent-tool rewrites, and proxy contexts were not changed further.

## Validation and Reload

Both latest validation runs returned 1 with six WARN messages only: UID/GID warnings for Example, default, and phpmyadmin. No ERROR/FATAL or missing-handler message remained. Per the accepted classification this is PASS_WITH_WARNINGS, not a configuration failure. These unrelated warnings were not repaired.

Validation logs: `/tmp/task011e-ols-test.log` and `/tmp/task011e-ols-pre-reload.log`.

`/usr/local/lsws/bin/lswsctrl restart` succeeded, reporting SIGUSR1 sent to the prior master. Subsequent status checks confirmed LiteSpeed running with PID 2436343, with workers listening on 443. No application containers were restarted.

## Final Routing

- `/` → static frontend.
- `/demo/` → existing browser-safe backend proxy, loopback port 18080.
- `/tools/` → existing protected backend proxy, same loopback port.
- Accepted `/agent-tools/` paths → existing health/tool rewrites.
- SPA fallback now excludes all three API prefixes. Unknown API error behavior still requires runtime proof.

## Local Backend Proof

At 00:55:55 UTC, `GET http://127.0.0.1:18080/health` returned HTTP 200, `application/json`, status healthy.

Unauthenticated `POST http://127.0.0.1:18080/demo/next-best-action` with CIF SYN002846 returned HTTP 200, `application/json`, an `ok: true` envelope with `data.rule_id=NBA-300`, `final_route=CALL`, `treatment=WAIT_SELF_CURE`, `channel=NONE`, and `recovery_opportunity_score=47`.

## Public Domain QA

Browser API success, protected-tool auth, AgentBase gateway auth/data, and post-deployment browser smoke are owner-verified as recorded above. No independent public request was executed in this continuation; local results are clearly labeled separately.

## Final Navigation, Overview, and Priority Page

Four real primary page states are implemented: `overview` (Tổng quan), `priority` (Danh sách ưu tiên), `customer` (Khách hàng), and `impact` (Tác động dự kiến). Placeholder sidebar entries and their click mappings are removed. The sidebar has a reserved empty secondary-navigation slot; no dead Giới thiệu hệ thống link or TASK-011F page was added. Assistant CTA has its own namespace and is never an active navigation item.

Overview keeps the API summary KPIs and exactly two CSS bar-chart sections: Phân bổ hành động hôm nay and Phân bổ tuyến xử lý. The API returns 20 ranked portfolio rows without NBA treatment, so the frontend retrieves each row's decision through existing `/demo/next-best-action`. Counts are computed from those actual responses and explicitly labeled as covering the 20 returned rows, not all 3,000 customers. Observed counts: commitment follow-up group 20; CALL route 20. Summary KPIs: portfolio 3,000, returned rows 20, CALL route 1,740, decisions available 3,000. The compact Điểm cần chú ý hôm nay section counts existing suppression/no-contact signals: 0 and 0 in this sample. No fabricated counts or new alert engine.

Priority is independent of Overview, preserving API ranking order with eight requested columns, CIF search, route filter, and action filter. The reason column shows existing DPD and recovery-opportunity facts rather than inventing a reason. Detail buttons open the selected customer. A separate labeled hero shortcut opens SYN002846 even though it is not in the top-20 response.

Customer context, timeline, scenario, PTP/contact information, event panel, assistant, and technical details remain in the customer page. The pre-existing event UI callback incorrectly assigned the whole event response as a decision; it now uses the accepted `after` decision. Impact assumptions and formulas are untouched.

Active navigation uses a persistent light orange tint; inactive hover is lighter and temporary, verified through computed styles. The 260px sidebar aligns branding with a single-line title. Layout uses bounded grids and table-local scrolling instead of hiding whole-page overflow. The assistant drawer is independently bounded; scenario modal remains centered.

Rendered local Playwright QA PASS at 1366×768, 1440×900, and 1920×1080: 12 page/viewport checks across all four pages, zero console/page errors, no horizontal document overflow or sidebar overlap. Verified filtering, selected-CIF detail navigation, hero debt/action rendering, scenario execution and centering, drawer bounds, and loaded impact values. Browser demo requests had no Authorization header. Google font CSS was stubbed locally to keep this QA independent of external font access; screenshots use the fallback font. Screenshots: `/tmp/task011e-overview-{1366,1440,1920}.png`, `/tmp/task011e-scenario-{1366,1440,1920}.png`, and `/tmp/task011e-impact-{1366,1440,1920}.png`. Overview and Impact screenshots at 1366 were visually inspected.

## AgentBase Retry

AgentBase retry passed against the existing runtime, updated from version 6 to version 7 with the current repository image. The credential already matched and was not rotated. `get_next_best_action` was invoked for SYN002846 and GOLDEN_G02; direct deterministic outputs matched AgentBase decisions field-for-field. Unknown-CIF no-fabrication, override guardrail, and no-private-reasoning checks passed. TASK-011 evidence and final status were updated to PASS.

## Security and Regression

No secrets printed or inserted into frontend. Protected tool authentication unchanged. FRONTEND_SECRET_SCAN=PASS: current dist scanned for prohibited credential names, actual configured credential values, and Bearer strings without printing them.

- Adapter suite: 6 tests PASS, including all browser methods, protected negative/positive auth, non-demo/unknown CIFs, malformed JSON, and aggregate demo-only validation. Copilot is stubbed only in this contract suite, not claimed as live AgentBase.
- Focused TASK-008 regression: 7 tests PASS (all hero scenarios, immutable snapshots, adversarial-LLM simulation invariance).
- Frontend: 14 tests PASS across 2 files: source contracts plus rendered navigation/chart and interactive priority tests. Separately, the local Playwright suite passed all three viewports as documented above.
- Production build: `tsc -b && vite build` PASS. Vite reports its existing future-loader compatibility warning.
- Live local matrix: all nine browser routes returned 200 application/json with no Authorization header. Copilot application status was success. Both protected customer/NBA tools rejected missing/wrong credentials and accepted the current `.env` credential. Health returned healthy. SYN002846 retained NBA-300 / CALL / WAIT_SELF_CURE / NONE / score 47. A synthetic cash-in test event was followed by reset of its demo overlay.

Initial sandbox-bound test server creation was denied; tests passed after explicit permission for local sockets. The first nohup backend launch did not persist; the backend was restored in persistent terminal session 1267 using the real `.env`, loopback host and port 18080, and the current repository entrypoint. Live matrix tests passed against that running process.

## Deployment

Deployed September 5, 2026 at 01:43:47 UTC.

- Source: `/opt/msb-collection-copilot/frontend/dist`.
- Destination: `/www/wwwroot/msb-collection-copilot.duckdns.org`.
- Full docroot backup: `/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260905T014347Z`.
- Replaced only static `index.html` and `assets/`; `.htaccess`, `.user.ini`, and `.well-known` preserved. Removed superseded assets are recoverable from the backup.
- Current artifacts: `index--OBahY07.js`, `index-D5LXIV6M.css`, referenced by the deployed index.
- Source/deployed index SHA-256: `caf59a0093aab222bf3acb32fd8fcb7265628e58c5077e79e20973291101c3f8`.
- Index byte comparison and recursive asset comparison PASS; static ownership `www:www`; deployed timestamps correspond to this deployment.
- Post-deployment local smoke: portfolio, customer-360, next-best-action, timeline, and impact all HTTP 200 application/json without browser auth. Post-deployment public browser smoke is owner-verified above.

## Business Drift

BUSINESS_SEMANTICS_DRIFT=0 — latest continuation changed frontend presentation, navigation, and tests only. Policy, recovery score, NBA, simulation, event semantics, and impact formulas were untouched. Earlier focused backend regression results are retained as historical evidence, not claimed rerun in this UI-only continuation.

## External Browser QA

Product-owner browser QA is complete and recorded above as `OWNER_VERIFIED_PASS`: the public site loads, browser API calls and timeline work, SYN002846 renders correctly, and the post-deployment smoke passed. The final AgentBase live proof is also complete and recorded in `task-results/TASK-011-agentbase-evidence.json` and `task-results/TASK-011-FINAL.md`.

## Commit

The production TypeScript build also refreshed tracked `frontend/tsconfig.tsbuildinfo`. Existing unrelated worktree changes were preserved.

The accepted TASK-011/TASK-011E files are committed; unrelated pre-existing worktree files remain intentionally uncommitted.
