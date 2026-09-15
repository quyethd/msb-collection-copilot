# TASK-014-LANDING-STORY-DEMO-010

## Implementation evidence

Landing được triển khai như một câu chuyện pitch tương tác: hero HTML, bài toán, giải pháp, Web + Zalo, hành trình người dùng, chương demo dạng gallery, SYN002846, minh bạch điểm, mô phỏng, hai luồng Trợ lý, kiến trúc, GreenNode, AI có kiểm soát, tác động, tóm tắt Ban giám khảo, FAQ, lộ trình và CTA cuối.

### Asset mapping

| Section | File | Purpose |
|---|---|---|
| Bài toán / gallery | `slide2.png` | Visual anchor cho bài toán ưu tiên |
| Hành trình người dùng | `user-journey.png` | Infographic 6 bước từ landing đến hành động |
| Demo Zalo thực tế | `zalo-demo-live-context.png` | Hồ sơ, mô phỏng và follow-up cùng ngữ cảnh |
| Hai luồng Trợ lý | `two-assistant-flows.png` | Luồng nghiệp vụ và luồng kiến thức |
| Kiến trúc hệ thống | `system-architecture.png` | Web + Zalo dùng chung Decision Core |
| GreenNode trong sản phẩm | `greennode-in-product.png` | Ranh giới Decision Core / GreenNode / local embedding |
| Demo gallery | `slide1.png`–`slide14.png` | 14 cảnh theo nhóm A–D của hợp đồng |

Tất cả asset landing được kiểm tra ở kích thước 1672×941. Hai asset bắt buộc tồn tại.

## Gates

```text
TASK_ID=TASK-014-LANDING-STORY-DEMO-010

LANDING_STORY=PASS
DEMO_CHAPTER=PASS
WEB_ZALO_SECTION=PASS
USER_JOURNEY_VISUAL=PASS
SYSTEM_ARCHITECTURE_VISUAL=PASS
TWO_ASSISTANT_FLOWS_VISUAL=PASS
ZALO_DEMO_VISUAL=PASS
GREENNODE_SECTION=PASS
AI_CONTROL_SECTION=PASS
JUDGE_SUMMARY=PASS
FAQ=PASS
ROADMAP=PASS

FRONTEND_TESTS=75 PASS
BUILD=PASS
FINAL_BUILD=PASS (pre-commit build; post-commit pending)

PUBLIC_LANGUAGE_POLICY=PASS
PUBLIC_INTERNAL_LABEL_SCAN=PASS (rendered landing)
RECOVERY_SCORE_TRUTH=PASS
GREENNODE_TRUTH=PASS
ZALO_PUBLIC_TRUTH=PASS
RECOVERY_SCORE_PRODUCTION_TRUTH=PENDING
BUSINESS_SEMANTICS_DRIFT=0

LOCAL_DESKTOP_VISUAL_QA=PASS
LOCAL_MOBILE_VISUAL_QA=PASS
VISUAL_STORY_CONTINUITY=PASS
INFOGRAPHIC_STYLE_INTEGRATION=PASS
GALLERY_BEHAVIOR=PASS (open/close, previous/next, keyboard arrows, Escape)

VERY_AUDIT=PENDING
SOURCE_SCOPE=PASS
BACKEND_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
ZALO_RUNTIME_CHANGED=NO
GREENNODE_CONFIG_CHANGED=NO

BOUNDED_BUSINESS_CANARY=PASS (6 tests, 13 subtests)
```

## Verification notes

- Full frontend suite: `75 passed` across 7 test files.
- Production build: passed with Vite/TypeScript.
- Required viewports rendered: 1366×768, 1440×900, 1920×1080, 390×844.
- Browser QA: zero page/console errors, zero horizontal overflow, 18 main story sections rendered.
- Gallery: 14 scenes, six featured scenes, modal caption, close control, previous/next controls, keyboard navigation.
- Bounded business verification: `PYTHONPATH=src pytest -q tests/test_task013a_web_simulation.py` → 6 passed, 13 subtests passed.
- No backend, business-rule, Zalo worker, RAG, GreenNode configuration, or service files were changed.

## Production evidence

```text
PREVIOUS_HEAD=95fd94bbf8fd3773964853f3ca6f50ca82f19ed9
TASK014_COMMIT=PENDING
FINAL_MASTER_HEAD=PENDING
BACKUP_PATH=PENDING
CLOSURE_REPORT_COMMIT=PENDING

FRONTEND_DEPLOY=PENDING
DEPLOYED_BUILD_MATCH=PENDING
BACKEND_RESTARTED=NO
ZALO_WORKER_RESTARTED=NO
PUBLIC_TLS=PENDING
PUBLIC_LANDING_HTTP=PENDING
PRODUCTION_DESKTOP_QA=PENDING
PRODUCTION_MOBILE_QA=PENDING
PRODUCTION_NO_OVERFLOW=PENDING
PRODUCTION_NO_BROKEN_ASSETS=PENDING
PRODUCTION_STORY_CONTINUITY=PENDING
PRODUCTION_DEMO_GALLERY=PENDING
APPLICATION_SMOKE=PENDING
APP_ZALO_SMOKE=PENDING
SESSION_SMOKE=PENDING
TASK_014_CLOSED=NO
PUSH=NO
```
