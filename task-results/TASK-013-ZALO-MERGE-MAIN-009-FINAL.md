# TASK-013-ZALO-MERGE-MAIN-009 — Final Verification

Date: 2026-09-15  
Repository: `/opt/msb-collection-copilot`  
Branch: `task-013-zalo-merge-main-009`  

## Final gates

```text
TASK_ID=TASK-013-ZALO-MERGE-MAIN-009
PRODUCTION_BASELINE_COMMIT=eae2b43
IMPLEMENTATION=PASS
PRE_COMMIT_TESTS=PASS
DIFF_CHECK=PASS
RAG_REGRESSION=PASS
RAG_AUTHORITY=KNOWLEDGE_ONLY
RAG_BUSINESS_DECISION_AUTHORITY=NONE
LOW_CONFIDENCE_BOUNDARY=PASS
RAG_SECURITY_BOUNDARY=PASS

ZALO_DIRECT_BOT_MERGED=PASS
CONVERSATION_V3_1_MERGED=PASS
ZALO_CHAT_REGRESSION=PASS
ZALO_TRANSPORT_REGRESSION=PASS
DUPLICATE_REPLY_PROTECTION=PASS
DUPLICATE_REPLY_COUNT=0
CONTEXT_CIF_LEAK=0
RAW_ENUM_LEAK=0
RAW_JSON_LEAK=0
RAW_NONE_LEAK=0

SYN002846_ROUTE=CALL
SYN002846_TREATMENT=WAIT_SELF_CURE
SYN002846_CHANNEL=NONE
SYN002846_SCORE=47
SYN000746_SCORE=69
BUSINESS_SEMANTICS_DRIFT=0

WEB_COPILOT_REGRESSION=PASS
CONVERSATION_CONTEXT_BUSINESS_AUTHORITY=NONE
CONVERSATION_POLICY_OVERRIDE=BLOCKED
FRONTEND_TESTS=PASS
FRONTEND_BUILD=PASS
APP_ZALO_PHONE_ONLY=PASS
LANDING_UNCHANGED=PASS
SECRET_SCAN=PASS
TOKEN_LEAK_COUNT=0
ORIGINAL_PRE_COMMIT_FAILURE_REPRODUCED=YES
RAG_TEST_CONTRACT_RECONCILED=PASS
RAG_EXPECTATION_ROOT_CAUSE=historical NEEDS_APPROVAL assertion hardcoded against a valid configured/live PASS state
CURRENT_RAG_STATE=RESOLVED_REVIEW: no unresolved RAG mismatch remains; the corrective contract is environment-independent, production RAG code is unchanged, RAG remains knowledge-only, and current RAG regression is PASS

READY_FOR_VERY_AUDIT=YES
READY_TO_COMMIT=NO

COMMIT=NO
MERGE_TO_MAIN=NO
DEPLOY=NO
LANDING_CHANGE=NO
```

The original pre-commit failure is preserved below in the corrective reconciliation section. The corrective pass is now green without changing production RAG code.

## Corrective reconciliation

### Original failure and root cause

The original run reproduced the failing test `ServiceBehaviorTest.test_gate_status_flags` with `24 passed, 1 failed` when the configured vDB was reachable. The assertion expected `GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL`, while `KnowledgeRagService.gate_status()` truthfully returned `PASS` for a configured live GreenNode vDB. Under restricted DNS, the same environment-sensitive setup surfaced as seven vDB setup errors instead.

Repository evidence separates the states:

- `NEEDS_APPROVAL` is the historical local/mock foundation state before vDB provisioning.
- `PASS` is valid for a configured/provisioned live vDB; TASK-011H-A.1 records live ingest, retrieval, Qwen RAG, and `PROJECT_KNOWLEDGE_RAG_LIVE=PASS`.
- RAG remains knowledge-only. `DECISION_CORE_UNCHANGED=True`, and customer decisions, routing, NBA, simulation, and score outputs remain outside RAG.

### Exact correction

Only `tests/test_task011h_knowledge.py` was corrected. `ServiceBehaviorTest` now uses an explicit local deterministic fixture, independent of deployment `.env` values, for its foundation behavior checks. A second test uses an in-process store marked as configured/live to verify the live status contract (`PASS`, ingest `PASS`, retrieval `PASS`, Qwen `NOT_RUN` until a live answerer runs, and project-live `NOT_PROVEN` until proven). No production RAG code, Decision Core, or business semantics changed.

Post-correction:

- `PYTHONPATH=.:src pytest -q tests/test_task011h_knowledge.py` — **26 passed**.
- Accepted RAG/routing/security batch with deployment overrides removed from the test process — **58 passed**.
- Deterministic/routing/tool batch — **92 passed, 71 subtests passed**.

```text
ORIGINAL_PRE_COMMIT_FAILURE_REPRODUCED=YES
RAG_EXPECTATION_ROOT_CAUSE=historical NEEDS_APPROVAL assertion hardcoded against a valid configured/live PASS state
RAG_TEST_CONTRACT_RECONCILED=PASS
CORRECTIVE_FILES_CHANGED=tests/test_task011h_knowledge.py; task-results/TASK-013-ZALO-MERGE-MAIN-009-FINAL.md
```

## Accepted source

Spike repository: `/opt/msb-collection-zalo-spike`  
Accepted commits reviewed:

- `220fe73` — `feat(zalo): ship hybrid-NLU conversational copilot V3 for Zalo direct-bot demo`
- `bf03448` — production rollout cleanup preparation
- `be19ae2` — release cleanup report update
- `4609300` — final production rollout cleanup

## Integrated files

- `src/msb_zalo/__init__.py`
- `src/msb_zalo/chat.py`
- `src/msb_zalo/bridge.py`
- `src/msb_zalo/client.py`
- `src/msb_zalo/worker.py`
- `zalo_worker.py`
- `tool_server.py` Zalo bridge/status/preview/inbound/send integration
- `msb-collection-tool-server.service`
- `zalo-worker.service`
- `frontend/src/zalo-demo.tsx`
- `frontend/src/zalo-demo.test.tsx`
- required navigation, routing, styling, and page-test changes
- `tests/test_zalo_chat.py`
- `tests/test_zalo_bridge.py`
- `tests/test_zalo_client.py`
- `tests/test_zalo_worker.py`
- `.gitignore` runtime-artifact rules

Historical task reports, sidecar implementation/tests, OpenClaw runtime files, public proxy, credentials, logs, deployment backups, and spike-specific paths were excluded. The tracked frontend TypeScript cache was restored to the production baseline after build verification.

## Commands and results

- `python3 -m compileall -q ...` — PASS.
- `PYTHONPATH=.:src pytest -q tests/test_zalo_chat.py` — **76 passed**.
- `PYTHONPATH=.:src pytest -q tests/test_zalo_bridge.py tests/test_zalo_client.py tests/test_zalo_worker.py` — **56 passed**.
- `PYTHONPATH=.:src pytest -q tests/test_task_copilot_conversation_v2.py` — **8 passed**.
- `npm test -- --run` — **70 passed**, 6 test files.
- `npm run build` — PASS; Vite production build completed.
- deterministic/routing/tool regression batch — **110 passed**, with 7 live-RAG setup errors under restricted DNS.
- approved network rerun `PYTHONPATH=.:src pytest -q tests/test_task011h_knowledge.py` — **24 passed, 1 failed** for the documented `GRENNODE_VDB_AVAILABLE` expectation mismatch.
- corrected `PYTHONPATH=.:src pytest -q tests/test_task011h_knowledge.py` — **26 passed**.
- corrected accepted batch with `GRENNODE_VDB_*` and `RAG_EMBEDDING_PROVIDER` unset — **58 passed**.
- corrected deterministic/routing/tool batch — **92 passed, 71 subtests passed**.
- `git diff --check` — PASS.
- `systemd-analyze verify msb-collection-tool-server.service zalo-worker.service` — task units accepted; one unrelated host `lshttpd.service` deprecation warning was emitted.

## Behavior evidence

In-process verification confirmed:

- `tính điểm SYN002846` → truthful score `47/100` and component breakdown.
- no-inflow simulation → `WAIT_SELF_CURE` to `CONTACT`, `NONE` to `CALL`.
- `thế giờ làm gì` after simulation uses the simulation after-state.
- TODAY_CALL_LIST wording preserves routing/action separation.
- generic score follow-ups use the active CIF.
- explicit CIF switching changes the active context without old simulation leakage.
- `CALL và CBS khác nhau thế nào?` uses the knowledge path and states routing is not treatment/action.
- unknown/security/policy-override prompts do not expose secrets, JSON, raw enums, or reasoning content.
- duplicate `update_key` produces one reply: `DUPLICATE_REPLY_COUNT=0`.
- `SYN000746` spot-check remains score `69`.

## Diff classification

- `INTENTIONAL_SOURCE`: Zalo package, worker, bridge integration, frontend route/UI, service units.
- `INTENTIONAL_TEST`: Zalo Python and frontend tests.
- `GENERATED`: frontend build cache was touched by build and restored; no generated cache remains as a task delta.
- `RUNTIME`: none tracked; worker lock/heartbeat, logs, and backups are ignored/excluded.
- `SECRET`: none.
- `UNRELATED`: none identified.
- `RESOLVED_REVIEW`: RAG environment-sensitive test assertion reconciled during the corrective pass; no unresolved RAG mismatch remains. The stable corrective contract is environment-independent, production RAG code is unchanged, RAG remains knowledge-only, and current RAG regression is `PASS` (see Corrective reconciliation).

## Known limitations / risks

- No live Zalo delivery was attempted during this merge verification; transport tests use in-process fakes and preserve the official Bot API polling/sendMessage boundary.
- The accepted default-fixture tests must run without deployment environment overrides; the corrected fixture now makes that boundary explicit.
- No commit, merge, deployment, landing change, or TASK-014 work was performed.
