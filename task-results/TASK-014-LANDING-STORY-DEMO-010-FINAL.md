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
FINAL_BUILD=PASS (from committed HEAD 4f21ede)

PUBLIC_LANGUAGE_POLICY=PASS
PUBLIC_INTERNAL_LABEL_SCAN=PASS (rendered landing)
RECOVERY_SCORE_TRUTH=PASS
GREENNODE_TRUTH=PASS
ZALO_PUBLIC_TRUTH=PASS
RECOVERY_SCORE_PRODUCTION_TRUTH=PASS
BUSINESS_SEMANTICS_DRIFT=0

LOCAL_DESKTOP_VISUAL_QA=PASS
LOCAL_MOBILE_VISUAL_QA=PASS
VISUAL_STORY_CONTINUITY=PASS
INFOGRAPHIC_STYLE_INTEGRATION=PASS
GALLERY_BEHAVIOR=PASS (open/close, previous/next, keyboard arrows, Escape)

VERY_AUDIT=PASS (independent contract review before deployment)
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
TASK014_COMMIT=4f21ede609577802fa2e72e8648f5518aa35faa3
FINAL_MASTER_HEAD=PENDING_CLOSURE_REPORT_COMMIT
BACKUP_PATH=/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260915T150000Z
CLOSURE_REPORT_COMMIT=PENDING

FRONTEND_DEPLOY=PASS (redeployed after pinned TLS QA)
DEPLOYED_BUILD_MATCH=PASS
BACKEND_RESTARTED=NO
ZALO_WORKER_RESTARTED=NO
PUBLIC_TLS=PASS (curl --resolve returned HTTP/2 200)
PUBLIC_LANDING_HTTP=PASS
PRODUCTION_DESKTOP_QA=PASS (1366x768, 1440x900, 1920x1080)
PRODUCTION_MOBILE_QA=PASS (390x844)
PRODUCTION_NO_OVERFLOW=PASS
PRODUCTION_NO_BROKEN_ASSETS=PASS (12 images loaded after scroll)
PRODUCTION_STORY_CONTINUITY=PASS
PRODUCTION_DEMO_GALLERY=PASS
APPLICATION_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS
ROLLBACK_REQUIRED=NO
ROLLBACK_RESULT=PASS
FIRST_DEPLOY_ROLLED_BACK=YES
FIRST_ROLLBACK_RESULT=PASS
ORIGINAL_CHROMIUM_TLS_FAILURE=ENVIRONMENTAL_DNS
DEFAULT_DNS_INTERCEPTED=YES (208.91.112.55 / 2001:cdba::3257:9652)
CHROMIUM_PINNED_TLS=PASS
CERT_HOSTNAME_MATCH=PASS
CERT_CHAIN_VERIFY=PASS
TLS_ROOT_CAUSE=QA_ENVIRONMENT_DNS_INTERCEPTION
LANDING_SOURCE_DEFECT=NO
PRODUCTION_CERT_DEFECT=NO
REDEPLOY_BACKUP_PATH=/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260915T154000Z
TASK_014_CLOSED=YES
PUSH=NO
```

## TLS recovery evidence

The first browser failure was environmental: default DNS resolved the hostname to `208.91.112.55` / `2001:cdba::3257:9652`, not the accepted public address `103.233.48.100`. Chromium with `--host-resolver-rules=MAP msb-collection-copilot.duckdns.org 103.233.48.100` loaded successfully with certificate verification enabled. OpenSSL verified the requested hostname and chain. The first deployment and rollback remain recorded above.
