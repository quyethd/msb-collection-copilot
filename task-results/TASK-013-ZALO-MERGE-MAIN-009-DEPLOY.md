# TASK-013-ZALO-MERGE-MAIN-009 — Deployment Closeout

Date: 2026-09-15
Repository: `/opt/msb-collection-copilot`

## Outcome

TASK-013 was committed and merged to `master`, but production validation found a critical Web Copilot simulation mismatch and the deployment was rolled back. The task is not closed.

```text
TASK_ID=TASK-013-ZALO-MERGE-MAIN-009
TASK013_FEATURE_COMMIT=21c6787e215ab4716ffdd674805e49ecbea686ca
MAIN_HEAD_BEFORE_MERGE=eae2b439afb0df8c123af68e645ac3e7723524d6
MERGE_COMMIT=1aa29ba9d85e308ed9c890275c9db10a36750f3c
MAIN_HEAD_AFTER_MERGE=1aa29ba9d85e308ed9c890275c9db10a36750f3c
PRE_DEPLOY_HEAD=1aa29ba9d85e308ed9c890275c9db10a36750f3c
ROLLBACK_REVERT_COMMIT=69cf9987b7df17238f46e416a786e5d263999526
CLOSEOUT_COMMIT=NONE
```

## Deployment mechanism

```text
ACTUAL_BACKEND_SERVICE=msb-collection-tool-server.service
ACTUAL_ZALO_WORKER_SERVICE=msb-zalo-worker.service
ACTUAL_BACKEND_PORT=18080
ACTUAL_FRONTEND_DOCROOT=/www/wwwroot/msb-collection-copilot.duckdns.org
FRONTEND_DEPLOYMENT=OpenLiteSpeed static docroot; hashed assets first, index.html last
```

The live units were temporarily switched to the merged repository paths. The failed gate triggered rollback to the existing spike checkout and the previous frontend backup. No DNS, firewall, NAT, TLS, OpenLiteSpeed route, OpenClaw service, or 18081 sidecar was changed.

Rollback backup was preserved at:

`/tmp/task013-production-deploy-20260915-062526-backup`

## Post-merge verification

```text
POST_MERGE_ZALO_CHAT=PASS (76 passed)
POST_MERGE_ZALO_TRANSPORT=PASS (56 passed; isolated concurrency test and serial rerun)
POST_MERGE_RAG=PASS (26 passed)
POST_MERGE_WEB_COPILOT=PASS (8 passed)
POST_MERGE_FRONTEND_TESTS=PASS (70 passed, 6 files)
POST_MERGE_FRONTEND_BUILD=PASS
POST_MERGE_SERVICE_CONFIG=PASS
```

The first parallel transport run had one timing failure; the isolated test passed and the required serial rerun passed 56/56.

## Business canaries

```text
SYN002846_ROUTE=CALL
SYN002846_TREATMENT=WAIT_SELF_CURE
SYN002846_CHANNEL=NONE
SYN002846_SCORE=47
SYN000746_SCORE=69
BUSINESS_SEMANTICS_DRIFT=0
```

Conversation and security checks passed in-process:

```text
DUPLICATE_REPLY_COUNT=0
CONTEXT_CIF_LEAK=0
RAW_ENUM_LEAK=0
RAW_JSON_LEAK=0
RAW_NONE_LEAK=0
SECRET_SCAN=PASS
TOKEN_LEAK_COUNT=0
```

## Production validation and failure

Backend health, worker activation, fresh heartbeat after startup, single poller, official provider status, public TLS using the configured matching certificate chain, landing/login, authenticated app, `/app/zalo`, and production business canaries passed.

```text
BACKEND_DEPLOY=PASS
ZALO_WORKER_DEPLOY=PASS
FRONTEND_DEPLOY=PASS
PRODUCTION_BACKEND_HEALTH=PASS
PRODUCTION_ZALO_WORKER=PASS
PRODUCTION_SIDECAR_18081=ABSENT
PUBLIC_LANDING=PASS
PUBLIC_LOGIN=PASS
PUBLIC_TLS=PASS
AUTHENTICATED_APP=PASS
PRODUCTION_APP_ZALO=PASS
PRODUCTION_SYN002846=PASS
PRODUCTION_SCORE=47
PRODUCTION_SYN000746_SCORE=69
PRODUCTION_BUSINESS_SEMANTICS_DRIFT=0
PRODUCTION_ZALO_TRANSPORT=PASS
PRODUCTION_ZALO_CONVERSATION=PASS
PRODUCTION_ZALO_LIVE_ROUNDTRIP=PENDING_OPERATOR
PRODUCTION_SECRET_BOUNDARY=PASS
PRODUCTION_POLICY_OVERRIDE=BLOCKED
```

Critical failure:

```text
PRODUCTION_WEB_COPILOT=FAIL
PRODUCTION_FOLLOWUP_DECISION=PASS
PRODUCTION_FOLLOWUP_SIMULATION=FAIL
PRODUCTION_KNOWLEDGE=PASS
```

For the required exact prompt `Nếu tiền vào 7 ngày bằng 0 thì quyết định có thay đổi không?`, the deployed API classified the request as simulation but returned the unchanged baseline `WAIT_SELF_CURE/NONE` state instead of the required `CONTACT/CALL` after-state. A follow-up with an explicitly supplied prior simulation change reached `CONTACT/CALL`, but that does not satisfy the required first-step production behavior.

## Rollback result

```text
ROLLBACK_REQUIRED=YES
ROLLBACK_RESULT=PASS
TASK_013_CLOSED=NO
TASK_014_AUTHORIZED=NO
MAIN_WORKTREE_CLEAN=PASS (before this report)
PUSH=NO
```

The merge was reverted with normal Git history. Production was restored to the prior spike service paths and the pre-deploy frontend artifacts. No TASK-014 implementation was started.
