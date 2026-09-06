# TASK-011I — Public Landing + Demo Login + Application Shell

## Route Architecture

- `/` renders the full-width public MSB product landing page.
- `/gioi-thieu` renders the same landing and replaces its history entry with `/`.
- `/login` renders the demo login card.
- `/app`, `/app/priority`, `/app/customer`, and `/app/impact` are the authenticated operational application routes.
- Unauthenticated application access redirects to `/login?next=...`; authenticated `/login` redirects to `/app`.
- This `/app/*` strategy preserves a clean public root while keeping operational state and customer navigation explicit.

## Public Landing

The existing System Overview implementation is reused as the landing content; it is not duplicated. The public wrapper supplies the light MSB header, login CTA, and full-width presentation without the operational sidebar. It includes the accepted SYN002846 demo truth: CALL, chờ khách hàng tự thanh toán, chưa cần liên hệ, điểm 47.

## Login and Auth Implementation

Added backend session endpoints:

- `POST /demo/auth/login`
- `GET /demo/auth/me`
- `POST /demo/auth/logout`

Credentials are read only from backend environment variables `DEMO_ADMIN_USERNAME` and `DEMO_ADMIN_PASSWORD`. Sessions are in-memory server-side tokens with HttpOnly, SameSite=Lax cookies; Secure is applied when the request is forwarded as HTTPS. No database or frontend credential is used.

## Application Route Guard and Logout

The application checks `/demo/auth/me` before loading operational data. Logout invalidates the server-side session and redirects to `/`. Existing browser-safe `/demo/*`, protected `/tools/*`, and protected `/agent-tools/*` contracts were not changed.

## Sidebar Change

Removed `Giới thiệu hệ thống` from the operational sidebar. Operational navigation remains Tổng quan, Danh sách ưu tiên, Khách hàng, and Tác động dự kiến, followed by the assistant CTA and Đăng xuất.

## Language Audit

- `VI_FIRST_CONTENT=PASS`
- `LINE_INITIAL_CAPITALIZATION=PASS`
- `UNEXPLAINED_TECH_JARGON=0`
- `ENGLISH_TERM_HAS_VIETNAMESE_EXPLANATION=PASS`

Technical terms shown on the public page are introduced with Vietnamese explanations, including Bộ máy quyết định (Decision Core), Cơ hội thu hồi (Recovery Opportunity), Hành động đề xuất tiếp theo (Next Best Action), Mô phỏng tình huống, and Dịch vụ mô hình AI GreenNode (MaaS). Qwen, VDB, and RAG are not claimed as live production capabilities.

## GreenNode Presentation

- `GREENNODE_VISIBLE_IN_HERO=PASS`
- `GREENNODE_DEDICATED_SECTION=PASS`
- `AGENTBASE_ROLE_CLEAR=PASS`
- `GLM_ROLE_CLEAR=PASS`
- `DECISION_CORE_AUTHORITY_CLEAR=PASS`
- `GREENNODE_NOT_DECISION_AUTHORITY=PASS`
- `QWEN_VDB_NOT_FALSELY_CLAIMED_LIVE=PASS`

The landing states that GreenNode AI supports analysis and explanation while the deterministic Decision Core owns the business result. The dedicated section describes the proven AgentBase, MaaS/GLM 5.2, and decision-engine roles without overclaiming.

## Rendered QA

Local rendered QA passed at 1366x768, 1440x900, 1920x1080, and 390x844:

- landing has no operational sidebar and no horizontal overflow;
- `/gioi-thieu` resolves to `/` without duplicate content;
- `/app/priority` redirects unauthenticated users to login;
- invalid login is rejected with a user-facing error;
- valid login opens the application shell;
- logout returns to the public landing and invalidates the session.

Evidence screenshots:

- `/tmp/task011i-landing-final-1366.png`
- `/tmp/task011i-landing-final-1440.png`
- `/tmp/task011i-landing-final-1920.png`
- `/tmp/task011i-landing-final-390.png`
- `/tmp/task011i-app-priority-1366.png`

## Security

- `CREDENTIAL_NOT_IN_FRONTEND_SOURCE=PASS`
- `CREDENTIAL_NOT_IN_FRONTEND_BUNDLE=PASS`
- `NO_SECRET_LEAK=PASS`
- `PRIVATE_REASONING_AUDIT=PASS`
- `LOGIN_INVALID=PASS`
- `LOGIN_VALID=PASS`
- `AUTH_ME=PASS`
- `LOGOUT_INVALIDATES_SESSION=PASS`
- `UNAUTHENTICATED_APP_REDIRECT=PASS`
- `AUTHENTICATED_APP_ACCESS=PASS`

The frontend contains no configured demo credential, collection-tool key, model key, bearer credential, runtime secret, or private prompt.

## Regression

- Frontend: 44/44 tests passed across 4 files.
- Backend adapter/auth focus: 9/9 tests passed.
- Deterministic NBA/recovery/impact regression: 42 passed, 71 subtests passed.
- Production build: PASS.
- `BUSINESS_SEMANTICS_DRIFT=0`.

Accepted SYN002846 behavior remains unchanged: CALL, WAIT_SELF_CURE, NONE, score 47.

## Scope

`TASK011H_INTEGRATION=NO`

Changed files:

- `.env.example`
- `tool_server.py`
- `frontend/src/main.tsx`
- `frontend/src/pages.tsx`
- `frontend/src/public-pages.tsx`
- `frontend/src/public.css`
- `frontend/src/pages/system-overview/SystemOverviewPage.tsx`
- `frontend/src/pages/system-overview/content.ts`
- `frontend/src/pages/system-overview/system-overview.css`
- associated frontend tests
- `tests/test_task011i.py`


## Final Approval, Deployment, And Production QA

- `AUTH_SCOPE=DEMO_APPLICATION_ACCESS_CONTROL`
- `SESSION_STORE=IN_MEMORY`
- `TASK011H_INTEGRATION=NO`
- `PRODUCTION_COOKIE_HTTPONLY=PASS`
- `PRODUCTION_COOKIE_SAMESITE_LAX=PASS`
- `PRODUCTION_COOKIE_SECURE=PASS`
- `BACKEND_DEPLOY=PASS`
- `BACKEND_HEALTH=PASS`
- `FRONTEND_DEPLOY=PASS`
- `DOCROOT_DEPLOY=PASS`
- `DEPLOYED_BUILD_MATCH=PASS`
- `PRODUCTION_LANDING_QA=PASS`
- `PRODUCTION_LOGIN_VALID=PASS`
- `PRODUCTION_LOGIN_INVALID=PASS`
- `PRODUCTION_AUTH_GUARD=PASS`
- `PRODUCTION_LOGOUT=PASS`
- `PRODUCTION_APPLICATION_REGRESSION=PASS`
- `SECRET_AUDIT=PASS`
- `BUSINESS_SEMANTICS_DRIFT=0`

Deployment backup: `/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260906T015434Z`.
The deployed `index.html` SHA-256 matches `frontend/dist/index.html`; static files are owned by `www:www`.
Public NAT-pinned smoke passed for `/`, `/gioi-thieu`, `/login`, browser-safe demo APIs, protected tools, and protected Agent tools. Public login cookie attributes were verified without recording the token.

The demo session survives normal browser navigation and logout invalidates it. Because the session store is in memory, a backend restart may invalidate active sessions; this is not persistent production authentication.

`TASK011I_COMMIT=698a4be`
