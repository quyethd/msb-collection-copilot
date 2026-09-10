# Final Landing Hardening

## Scope

Landing-only hardening for `/`. No business module, business rule, backend contract, authentication architecture, RAG threshold, GreenNode production configuration, commit, or deployment was changed.

Repo truth confirmed: frontend is React + TypeScript + Vite; backend is Python. The landing inventory reflects the repository modules under `src/`.

## Product story and copy

- Vietnamese-first copy was cleaned up and technical terms are introduced with Vietnamese explanations.
- Internal task labels, runtime labels, hashes, branch names, test labels, and `msb-collection-copilot-spike` are absent from rendered public landing text.
- `Cơ Hội Thu Hồi (Recovery Opportunity)` explicitly states that the score is a relative priority score, not a payment probability.
- The score source note points to `src/msb_recovery/engine.py` and `docs/spec-v1/RULE_BASE_V1.md`; no unsupported sub-formula was invented.
- AgentBase wording is bounded to being verified in the demo for business-tool orchestration; the landing does not claim every Copilot request must run through AgentBase.
- Current demo capabilities and future roadmap are visually separated.

## Visuals

Added three responsive visual blocks:

1. User journey: Landing → Đăng nhập → Danh sách ưu tiên → Hồ sơ khách hàng → Hỏi Trợ lý → Hành động / Mô phỏng / Tác động dự kiến.
2. Architecture and technology stack: React + TypeScript + Vite, Python, business modules, GreenNode components, local multilingual embedding, knowledge module, and synthetic data.
3. Assistant flow: separate customer/decision and knowledge paths, with the Decision Core authority message and explicit statement that RAG does not decide nghiệp vụ.

The module inventory contains all nine repository modules requested, grouped into business modules and deployment/architecture components, including `msb_knowledge_rag`.

## Final UX polish

- Secondary technical visuals now sit after the core product and GreenNode story, reducing the first-screen sense of length.
- The user journey is a connected path with a starting persona and a concrete outcome: “Từ danh sách → bằng chứng → hành động”.
- The architecture visual is reduced to five conceptual layers: Frontend, Backend / Trợ lý, Decision Core, GreenNode AI, and Data / Knowledge.
- The nine-module inventory remains available in compact native disclosure groups and does not compete visually with the product story.
- The roadmap is now exactly three future-direction stages: Kết nối dữ liệu, AI hỗ trợ tác nghiệp, and Tối ưu liên tục.

## Roadmap and references

The roadmap now separates “Đã có trong bản demo” from “Hướng phát triển tiếp theo” and includes the requested T24 / Temenos Transact, MSB contact center, DigiLenO, supervised call assistance, outcome feedback, channel/treatment optimization, controlled experimentation, and human-in-the-loop directions. No autonomous production collection claim is made.

External references are displayed separately as inspiration for future direction:

- GreenNode — [AgentBase](https://greennode.ai/product/agentbase)
- Temenos — [Transact Data Hub](https://developer.temenos.com/transact-data-hub)
- Genesys — [Agent Assist](https://www.genesys.com/definitions/what-is-agent-assist)

## QA evidence

Rendered screenshots were captured locally at:

- `/tmp/landing-polish-1366.png`
- `/tmp/landing-polish-1440.png`
- `/tmp/landing-polish-1920.png`
- `/tmp/landing-polish-390.png`

The Playwright render pass found no console errors, no horizontal overflow, no literal `svg...` text, and no internal task/runtime markers in the rendered landing. The app brand is now an anchor to `/`; it does not invoke logout, so the existing session remains available.

Self-review completed from the perspectives of Collection Officer, Collection Manager, Product Manager, Solution Architect, AI Engineer, Security Reviewer, and Hackathon Judge. No remaining meaningful copy, truthfulness, or layout issue was found within this scope.

## Gates

LANDING_POLISH=PASS
VI_FIRST_CONTENT=PASS
SVG_TEXT_BUG=PASS
INTERNAL_TASK_LABELS_REMOVED=PASS
INTERNAL_RUNTIME_LABELS_REMOVED=PASS

RECOVERY_OPPORTUNITY_TRUTHFUL=PASS
RECOVERY_SCORE_SOURCE_VERIFIED=PASS

MODULE_LIST_COMPLETE=PASS
MSB_KNOWLEDGE_RAG_VISIBLE=PASS

USER_JOURNEY_VISUAL=PASS
ARCHITECTURE_VISUAL=PASS
DECISION_FLOW_VISUAL=PASS

GREENNODE_STORY=PASS
AGENTBASE_WORDING_TRUTHFUL=PASS

LOGO_TO_LANDING=PASS
SESSION_PRESERVED=PASS

ROADMAP_UPDATED=PASS
T24_DIRECTION=PASS
DIGILENO_DIRECTION=PASS
CONTACT_CENTER_DIRECTION=PASS
AI_CALL_ASSIST_DIRECTION=PASS
EXTERNAL_REFERENCES=PASS

DESKTOP_QA=PASS
MOBILE_QA=PASS
NO_HORIZONTAL_OVERFLOW=PASS
USER_JOURNEY=PASS
ARCHITECTURE_SIMPLIFIED=PASS
MODULE_SECTION_COMPACT=PASS
ROADMAP_3_STAGE=PASS

TESTS=51/51 PASS
BUILD=PASS
DIFF_CHECK=PASS

BUSINESS_SEMANTICS_DRIFT=0

APPLICATION_CODE_CHANGED=frontend/src/pages.tsx; frontend/src/pages.test.tsx; frontend/src/pages/system-overview/SystemOverviewPage.tsx; frontend/src/pages/system-overview/SystemOverviewPage.test.tsx; frontend/src/pages/system-overview/content.ts; frontend/src/pages/system-overview/system-overview.css
BUSINESS_RULE_CHANGED=NO

COMMIT=NO
DEPLOY=NO
