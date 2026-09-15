# TASK-013-ZALO-MERGE-MAIN-009 — Independent Very Audit

Date: 2026-09-15  
Repository: `/opt/msb-collection-copilot`  
Branch: `task-013-zalo-merge-main-009`  
Audit mode: read-only; no commit, merge, deploy, landing change, or TASK-014 work.

## Audit baseline

- `cwd=/opt/msb-collection-copilot`
- `branch=task-013-zalo-merge-main-009`
- `PRODUCTION_BASELINE_COMMIT=eae2b43`
- `CURRENT_HEAD=eae2b43`
- Initial `git diff --check`: PASS.
- The requested `tasks/TASK-013-ZALO-MERGE-MAIN-009.md` was not present in the repository; the final report and accepted historical reports were available and inspected.

Initial worktree inventory:

```text
 M .gitignore
 M frontend/src/main.tsx
 M frontend/src/pages.test.tsx
 M frontend/src/pages.tsx
 M frontend/src/styles.css
 M tests/test_task011h_knowledge.py
 M tool_server.py
?? frontend/src/zalo-demo.test.tsx
?? frontend/src/zalo-demo.tsx
?? msb-collection-tool-server.service
?? src/msb_zalo/
?? task-results/TASK-013-ZALO-MERGE-MAIN-009-FINAL.md
?? tests/test_zalo_bridge.py
?? tests/test_zalo_chat.py
?? tests/test_zalo_client.py
?? tests/test_zalo_worker.py
?? zalo-worker.service
?? zalo_worker.py
```

## Scope and diff audit

All actual deltas were inspected. Classification:

- `INTENTIONAL_SOURCE`: `src/msb_zalo/`, `zalo_worker.py`, `tool_server.py`, frontend Zalo route/control/navigation/style source, and the two service units.
- `INTENTIONAL_TEST`: Zalo Python tests, Zalo frontend test, navigation test changes, and the RAG corrective test change.
- `INTENTIONAL_REPORT`: `task-results/TASK-013-ZALO-MERGE-MAIN-009-FINAL.md` and this audit report.
- `SERVICE_CONFIG`: `msb-collection-tool-server.service`, `zalo-worker.service`.
- `GENERATED`: frontend TypeScript build cache was changed by the audit build and restored exactly to the baseline; no generated cache remains as a delta.
- `RUNTIME`: no retained runtime artifact. A 51-byte `:memory:.ses` artifact appeared during test execution and was removed as audit-generated runtime output; it was not part of the initial inventory.
- `SECRET`: none.
- `UNRELATED`: none identified.
- `NEEDS_REVIEW`: none in the implementation delta.

No Decision Core, NBA, recovery-score, or simulation semantic source changed. No OpenClaw runtime, sidecar `18081`, obsolete `/internal/zalo-copilot/`, debug code, or secret values were introduced. Landing source was not changed.

`SCOPE_AUDIT=PASS`  
`DIFF_AUDIT=PASS`

## RAG corrective audit

The only RAG production-adjacent delta is `tests/test_task011h_knowledge.py`. The correction injects `KnowledgeRagConfig` with no GreenNode endpoint/index for deterministic service-behavior tests. It separately adds an in-process configured/live store whose assertions require `GRENNODE_VDB_AVAILABLE=PASS`, live ingest/retrieval `PASS`, Qwen `NOT_RUN`, project-live `NOT_PROVEN`, and the `LIVE_GREENNODE_VDB` inference anchor. This is deterministic testing of two distinct valid contracts, not acceptance of either result from the deployment environment.

Accepted TASK-011H-A.1 and production evidence records a provisioned/live GreenNode vDB with live ingest, retrieval, Qwen RAG, and project-RAG `PASS`. The historical local/unprovisioned state is represented by the deterministic local fixture and `NEEDS_APPROVAL`. Production RAG code, Decision Core, routing, treatment, channel, NBA, score, and simulation semantics are unchanged.

The RAG code remains knowledge-only. Boundary tests keep customer decision, customer fact, simulation, low-confidence, secret, and policy-override paths outside RAG; no low-confidence or security assertion was weakened.

`RAG_CORRECTIVE_AUDIT=PASS`  
`RAG_TEST_IS_ENVIRONMENT_INDEPENDENT=PASS`  
`RAG_PRODUCTION_CODE_UNCHANGED=PASS`  
`RAG_REGRESSION=PASS`  
`RAG_AUTHORITY=KNOWLEDGE_ONLY`  
`RAG_BUSINESS_DECISION_AUTHORITY=NONE`

## Independent test replay

Exact commands and results:

```text
PYTHONPATH=.:src pytest -q tests/test_task011h_knowledge.py
26 passed in 133.81s (0:02:13), 2 non-failing warnings

PYTHONPATH=.:src pytest -q tests/test_zalo_chat.py
76 passed in 161.84s (0:02:41)

PYTHONPATH=.:src pytest -q tests/test_zalo_bridge.py tests/test_zalo_client.py tests/test_zalo_worker.py
56 passed in 71.92s (0:01:11)

PYTHONPATH=.:src pytest -q tests/test_task_copilot_conversation_v2.py
8 passed in 0.25s

frontend: npm test -- --run
6 test files, 70 passed

frontend: npm run build
PASS; TypeScript build and Vite production build completed

systemd-analyze verify msb-collection-tool-server.service zalo-worker.service
exit 0; only unrelated host lshttpd.service KillMode warning
```

The final report documents a 58-test accepted RAG/routing/security batch and a 92-test deterministic/routing/tool batch, but does not specify the exact file lists/command for those aggregate batches. They could not be independently replayed as the same exact batch from the available evidence. The required focused RAG, Zalo, web, frontend, and service checks above were independently replayed.

Selected direct Zalo behavior replay: 9 passed, covering the required score, simulation, after-state follow-up, route-safe call wording, active-CIF score context, explicit CIF switching, unknown CIF safety, and raw-output checks. Full Zalo suite also passed.

## Business canary and conversation audit

Actual deterministic tool path (`invoke_tool("get_next_best_action", ...)`) returned:

```text
SYN002846: final_route=CALL, treatment=WAIT_SELF_CURE, channel=NONE, recovery_opportunity_score=47
SYN000746: recovery_opportunity_score=69
```

The Zalo tests and direct replay verify truthful `47/100` component breakdown, no-inflow transition `WAIT_SELF_CURE -> CONTACT` and `NONE -> CALL`, simulation-after-state follow-up, route/action separation, active-CIF usage, explicit switch isolation, unknown-CIF non-fabrication, and duplicate update suppression. No raw enum/JSON/None leakage was observed.

`SYN002846_ROUTE=CALL`  
`SYN002846_TREATMENT=WAIT_SELF_CURE`  
`SYN002846_CHANNEL=NONE`  
`SYN002846_SCORE=47`  
`SYN000746_SCORE=69`  
`BUSINESS_SEMANTICS_DRIFT=0`  
`DUPLICATE_REPLY_COUNT=0`  
`CONTEXT_CIF_LEAK=0`  
`RAW_ENUM_LEAK=0`  
`RAW_JSON_LEAK=0`  
`RAW_NONE_LEAK=0`

Web conversation regression independently passed 8/8 and covers timeline/history-compatible context, simulation follow-up, knowledge isolation, cross-CIF isolation, truthful progress, security/injection blocking, and business-authority boundaries.

## Product and frontend audit

The source preserves MSB Trợ Lý Thu Hồi Nợ for Collection Officers, with team-leader/manager relevance. Zalo is an interaction channel for the copilot, not an end-customer banking chatbot. Decision Core/tools remain authoritative; AI/RAG has no business-decision authority.

The `/app/zalo` route is auth-gated through `/demo/auth/me`, uses only a display-phone field, has no `target_id` input, and does not render “Nhãn demo”, “Tên hiển thị”, or a technical target identifier. Public landing source files were unchanged by TASK-013.

`PROJECT_ALIGNMENT=PASS`  
`AI_BUSINESS_AUTHORITY=NONE`  
`APP_ZALO_PHONE_ONLY=PASS`  
`LANDING_UNCHANGED=PASS`  
`FRONTEND_TESTS=PASS`  
`FRONTEND_BUILD=PASS`  
`WEB_COPILOT_REGRESSION=PASS`  
`CONVERSATION_CONTEXT_BUSINESS_AUTHORITY=NONE`  
`CONVERSATION_POLICY_OVERRIDE=BLOCKED`

## Service configuration audit

Both units passed static systemd verification. The tool server binds to `127.0.0.1:18080`; the Zalo worker forwards to `http://127.0.0.1:18080/demo/zalo/inbound`. Credentials are referenced through file paths only. No service was installed, started, stopped, or restarted.

`SERVICE_CONFIG_AUDIT=PASS`  
`SIDECAR_RUNTIME_DEPENDENCY=0`  
`OPENCLAW_RUNTIME_DEPENDENCY=0`

## Security audit

`.env` remains untracked. Secret values, authorization headers, cookies, bot tokens, shared secrets, private prompts, and reasoning content were not printed or added to the report. Static scans found only code/documentation references and test placeholders, not committed secret values. Zalo client/worker tests verify safe errors, bounded responses, file-based secrets, and official Bot API request boundaries. Copilot and Zalo security tests cover `.env`, API-key, system-prompt, reasoning-content, and business-override requests.

`SECRET_SCAN=PASS`  
`TOKEN_LEAK_COUNT=0`  
`POLICY_OVERRIDE=BLOCKED`

## Report consistency audit

The existing final report correctly preserves the original `24 passed / 1 failed` history, records the corrected `26 passed` result, explains the historical `NEEDS_APPROVAL` versus configured/live `PASS` state, and records current final gates. However, its `Diff classification` still says:

```text
NEEDS_REVIEW: broader RAG test expectation mismatch described above.
```

After the corrective reconciliation and current 26/26 pass, this wording is stale and materially inconsistent with the report’s own `RAG_TEST_CONTRACT_RECONCILED=PASS` and `READY_FOR_VERY_AUDIT=YES`. It was not changed during this read-only audit.

`REPORT_CONSISTENCY=FAIL`

## Final worktree integrity

After tests/build and generated-artifact restoration, the remaining inventory is the initial task inventory plus this new audit report. `frontend/tsconfig.tsbuildinfo` matches the baseline and `git diff --check` passes. No implementation work was removed or altered.

`FINAL_WORKTREE_INTEGRITY=PASS`

## Final gates

```text
VERY_AUDIT=FAIL
PROJECT_ALIGNMENT=PASS
AI_BUSINESS_AUTHORITY=NONE
SCOPE_AUDIT=PASS
DIFF_AUDIT=PASS
RAG_CORRECTIVE_AUDIT=PASS
RAG_TEST_IS_ENVIRONMENT_INDEPENDENT=PASS
RAG_PRODUCTION_CODE_UNCHANGED=PASS
RAG_REGRESSION=PASS
RAG_AUTHORITY=KNOWLEDGE_ONLY
RAG_BUSINESS_DECISION_AUTHORITY=NONE
ZALO_CHAT_AUDIT=PASS
ZALO_TRANSPORT_AUDIT=PASS
WEB_COPILOT_REGRESSION=PASS
FRONTEND_TESTS=PASS
FRONTEND_BUILD=PASS
APP_ZALO_PHONE_ONLY=PASS
LANDING_UNCHANGED=PASS
SERVICE_CONFIG_AUDIT=PASS
SIDECAR_RUNTIME_DEPENDENCY=0
OPENCLAW_RUNTIME_DEPENDENCY=0
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
POLICY_OVERRIDE=BLOCKED
REPORT_CONSISTENCY=FAIL
FINAL_WORKTREE_INTEGRITY=PASS
READY_TO_COMMIT=NO
READY_TO_MERGE_MAIN=NO
COMMIT=NO
MERGE=NO
DEPLOY=NO
TASK_014_AUTHORIZED=NO
```

The audit stops here as required for a failed material consistency gate.
