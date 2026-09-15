# TASK-013 — Final Navigation/Auth Corrective

Date: 2026-09-15
Branch: `master`
Pre-corrective HEAD: `c1512b3`

## Scope and root cause

The three Web UI defects were reproduced by tracing the existing route lifecycle:

1. On `/app/zalo`, the app rendered a separate `AuthenticatedShell`. Its
   sidebar received `setPage={()=>{}}`, so sidebar navigation could not update
   the route or content. The brand anchor itself correctly targeted `/`, and
   session state is cookie-backed, so the brand defect was the shell’s broken
   return/navigation lifecycle rather than logout logic.
2. From normal pages, the sidebar’s Zalo branch called `history.pushState` and
   dispatched `popstate`, but the normal app route map omitted `zalo`. This made
   Zalo navigation dependent on the special shell path and left the rendered
   page out of sync until a document reload.
3. From `/app/zalo`, the separate shell’s no-op page callback prevented normal
   navigation back to overview, priority, customer, or impact.

```text
BRAND_LINK_DEFECT_REPRODUCED=YES
NAV_TO_ZALO_REFRESH_BUG_REPRODUCED=YES
NAV_FROM_ZALO_BUG_REPRODUCED=YES
ZALO_ROUTE_ROOT_CAUSE_IDENTIFIED=YES
```

## Corrective change

`/app/zalo` is now a first-class route in the existing authenticated
`AuthenticatedApp` shell. The shared route helper covers `/app`,
`/app/priority`, `/app/customer`, `/app/impact`, and `/app/zalo`. The existing
sidebar callback handles every destination, and the existing `popstate`
listener keeps back/forward navigation synchronized. `ZaloDemo` content and
session handling were reused unchanged.

The brand remains one anchor to `/`; it does not logout. Returning to `/app`
therefore uses the existing session cookie without a second login.

## Auth contract reconciliation

Source and history confirm the later browser-safe contract:

- `_BROWSER_POST_ROUTES` explicitly allowlists the browser demo POST surface.
- `/demo/timeline/{synthetic-cif}` and `/demo/reset/{synthetic-cif}` are
  explicitly allowlisted browser-safe routes.
- Demo validation remains synthetic-CIF-only and rejects unknown/non-demo
  mutations.
- `/tools/*` and `/agent-tools/*` still require Bearer authentication.
- The frontend uses `/demo/*` adapters and contains no
  `COLLECTION_TOOL_API_KEY`.

The three stale TASK-008B 401 assertions were renamed and changed into public
browser-safe synthetic-route assertions. They were not deleted. Existing
protected-route tests remain and were executed.

```text
CURRENT_BROWSER_SAFE_DEMO_CONTRACT=CONFIRMED
LEGACY_AUTH_TESTS_RECONCILED=PASS
BROWSER_SAFE_DEMO_ROUTE_TESTS=PASS
PROTECTED_TOOL_AUTH_TESTS=PASS
INVALID_AUTH_REJECTED=PASS
FRONTEND_API_KEY_PRESENT=NO
BROWSER_SAFE_ALLOWLIST_BOUNDED=PASS
```

## Regression evidence

```text
FRONTEND_TESTS=PASS (7 files, 73 tests)
FRONTEND_BUILD=PASS
SOCKET_RELEVANT_TESTS=PASS (76 tests, 10 subtests; authorized run)
TASK013A_EXACT_PHRASE=PASS
TASK013A_SHORT_PHRASE=PASS
TASK013A_SIMULATION_RESULT=CONTACT/CALL
TASK013A_FOLLOWUP_AFTER_STATE=PASS
ZALO_CHAT_REGRESSION=PASS (99 tests)
ZALO_TRANSPORT_REGRESSION=PASS (included in authorized Zalo worker/client/bridge battery)
RAG_REGRESSION=PASS
BUSINESS_REGRESSION=PASS
```

The RAG and deterministic business run passed 103 tests and 71 subtests.
The authorized TASK-008B/TASK-011D/TASK-011I socket run passed 76 tests and
10 subtests. The initial sandbox socket failures were environmental and were
not treated as application failures.

```text
ORIGINAL_SANDBOX_SOCKET_FAILURE=ENVIRONMENTAL
FULL_SUITE_SINGLE_PROCESS=NOT_CLAIMED
```

## Navigation contract

```text
NAV_APP_TO_ZALO=PASS
NAV_PRIORITY_TO_ZALO=PASS
NAV_CUSTOMER_TO_ZALO=PASS
NAV_IMPACT_TO_ZALO=PASS
NAV_ZALO_TO_OVERVIEW=PASS
NAV_ZALO_TO_PRIORITY=PASS
NAV_ZALO_TO_CUSTOMER=PASS
NAV_ZALO_TO_IMPACT=PASS
DIRECT_LOAD_APP_ZALO=PASS
NAVIGATION_REQUIRES_REFRESH=NO
BRAND_LINK_FROM_ZALO=PASS
BRAND_TO_LANDING=PASS
SESSION_PRESERVED_AFTER_BRAND_NAV=PASS
```

These are covered by the shared route-helper tests, Sidebar callback tests,
existing active-navigation/brand tests, and the production build/typecheck.

## Business and security gates

```text
SYN002846_ROUTE=CALL
SYN002846_TREATMENT=WAIT_SELF_CURE
SYN002846_CHANNEL=NONE
SYN002846_SCORE=47
SYN000746_SCORE=69
BUSINESS_SEMANTICS_DRIFT=0
DUPLICATE_REPLY_COUNT=0
CONTEXT_CIF_LEAK=0
RAW_ENUM_LEAK=0
RAW_JSON_LEAK=0
RAW_NONE_LEAK=0
SECRET_SCAN=PASS
TOKEN_LEAK_COUNT=0
FRONTEND_API_KEY_PRESENT=NO
PROTECTED_TOOL_AUTH=PASS
SIDECAR_18081=ABSENT
OPENCLAW_RUNTIME=ABSENT
SOURCE_SCOPE=PASS
BUSINESS_RULE_CHANGED=NO
GREENNODE_CONFIG_CHANGED=NO
RAG_AUTHORITY_CHANGED=NO
```

## Independent Very Audit (pre-deploy)

```text
VERY_AUDIT=PASS
```

The audit confirmed first-class Zalo routing, no refresh-based fix, brand
landing navigation without logout, session preservation, reconciled auth
tests, protected internal tools, no frontend API key, unchanged TASK-013A
simulation, unchanged Zalo backend/conversation source, and unchanged business
canaries.

## Delivery state

```text
TASK013_SOURCE_PRESENT=PASS
TASK013A_SOURCE_PRESENT=PASS
TASK013A_COMMIT=be62958
READY_TO_COMMIT=YES
TASK013_FINAL_CORRECTIVE_COMMIT=RECORDED_AFTER_COMMIT
COMMIT=RECORDED_AFTER_COMMIT
MERGE=NO
PUSH=NO
DEPLOY=PENDING
TASK_014_AUTHORIZED=NO
```

Production gates and the final closeout status are appended after deployment
validation. No production claim is made by this pre-deploy section.
