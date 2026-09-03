# TASK-007B.0 FINAL REPORT

## Final Status

TASK-007B.0 PASS -- GREENNODE END-TO-END PROVEN

## Platform Gates

| Gate | Status |
|---|---|
| PUBLIC_DNS | PASS |
| PUBLIC_TLS | PASS |
| PUBLIC_PROXY | PASS |
| PUBLIC_AUTH | PASS |
| PUBLIC_SYN002846 | PASS |
| RUNTIME_TOOL_CALL | PASS |
| REMOTE_UNKNOWN_CIF_NO_FABRICATION | PASS |
| RUNTIME_TO_GLM_5_2 | PASS |
| AGENTBASE_MONITORING | PASS |

## Runtime

| Field | Value |
|---|---|
| Runtime name | msb-collection-copilot-spike |
| Runtime ID | runtime-bded4bb3-3d91-459d-b80b-d5c784662586 |
| Runtime status | ACTIVE |
| Endpoint ID | endpoint-3c977781-5522-43a8-940e-01e9f55de485 |
| Endpoint URL | https://endpoint-3c977781-5522-43a8-940e-01e9f55de485.agentbase-runtime.aiplatform.vngcloud.vn |
| Version | 5 (live) |
| Image | vcr.vngcloud.vn/111480-abp114572/msb-collection-copilot-spike:task007b0-v3 |
| Flavor | runtime-s2-general-2x4 |
| Network | PUBLIC |
| Inbound auth | NONE |

No credentials stored in this report.

## End-to-End Proof

```
GreenNode Agent Runtime (v5, ACTIVE)
  -> POST /invocations {"message": "...SYN002846..."}
  -> handler extracts CIF SYN002846
  -> get_customer_360 selected
  -> HTTPS POST https://msb-collection-copilot.duckdns.org/agent-tools/get_customer_360
  -> Bearer authentication succeeded
  -> Ubuntu OpenLiteSpeed -> TASK-006 tool layer
  -> SYN002846 customer context returned (HTTP 200)
  -> GLM-5.2 invoked for summary (canonical_model: glm-5.2)
  -> model_summary: "The customer record for SYN002846 has been successfully retrieved."
  -> response returned to caller (HTTP 200, 33.5s)
```

Observable evidence from the decisive test:

- HTTP 200 from runtime endpoint
- status: success
- cif: SYN002846
- tool: get_customer_360
- tool_result.ok: True
- tool_result.data.cif: SYN002846
- tool_result.data.as_of_date: 2026-08-28
- tool_result.data contains: policy, cashflow, contact, payment
- canonical_model: glm-5.2
- synthetic_data: True
- model_summary contains no recommendation
- reasoning_content: not present in response

## Negative Test

```
GreenNode Agent Runtime (v5, ACTIVE)
  -> POST /invocations {"message": "...SYN999999..."}
  -> handler extracts CIF SYN999999
  -> get_customer_360 selected
  -> HTTPS tool request sent
  -> tool returned NOT_FOUND
  -> no LLM invocation (canonical_model: None)
  -> response returned (HTTP 200, 19.6s)
```

Observable evidence:

- HTTP 200 from runtime endpoint
- status: error
- cif: SYN999999
- tool_result.ok: False
- tool_result.error: {"code": "NOT_FOUND", "message": "CIF 'SYN999999' was not found"}
- tool_result.data: None
- model_summary: "Tool lookup failed; no model interpretation was requested."
- canonical_model: None
- No fabricated customer data
- No replacement CIF
- No recommendation

## Security

| Control | Status |
|---|---|
| HTTPS | Runtime endpoint uses valid TLS (agentbase-runtime.aiplatform.vngcloud.vn) |
| Bearer authentication | Tool endpoint requires Bearer token; runtime env var configured securely |
| Secret handling | COLLECTION_TOOL_API_KEY set as runtime env var, not baked into image, not in .env.example, not tracked by Git |
| reasoning_content | Not exposed in runtime response, not persisted in any artifact |
| Backend exposure | Runtime network mode: PUBLIC; inbound auth: NONE (runtime endpoint is publicly callable) |
| Image secret status | Image auth configured on runtime; registry credentials not stored in application source |
| .env | Git-ignored, not tracked, not uploaded in Docker image (.dockerignore excludes .env) |

Host-local TLS note: curl from the Ubuntu host to the public duckdns hostname
reports a self-signed certificate. This is a local host routing/certificate-path
issue only. The GreenNode Agent Runtime calls the externally validated HTTPS
endpoint successfully. No TLS verification was disabled. No production workaround
was applied.

## Repository Audit

### Baseline

| Field | Value |
|---|---|
| Baseline HEAD | ed845c4 |
| Baseline commit | TASK-007A pass deterministic next best action engine |
| Current HEAD | ed845c4 (no new commits) |

### Business Semantics Drift

BUSINESS_SEMANTICS_DRIFT=0

No changes to accepted business implementations:

- src/ -- unchanged (git diff ed845c4 -- src/ = empty)
- sql/ -- unchanged
- TASK-001.md through TASK-007A.md -- unchanged
- TASK-007A_DECISION_CONTRACT_V1.md -- unchanged
- pyproject.toml -- unchanged
- README.md -- unchanged

TASK-007B.0 files verified as infrastructure only:

- main.py: no business logic keywords (routing, scoring, treatment, channel, objective, WHEN, reason_code, decision_trace). LLM prompt explicitly forbids business actions.
- tool_server.py: no business logic keywords. Delegates to TASK-006 (msb_tools.registry.invoke_tool). Does not duplicate or reinterpret business rules.

### Docs/Spec Drift

DOCS_SPEC_V1_DRIFT=0

- docs/ -- unchanged (git diff ed845c4 -- docs/ = empty)

## Files Created

| File | Purpose |
|---|---|
| main.py | TASK-007B.0 AgentBase connectivity-spike agent entrypoint |
| tool_server.py | Authenticated local HTTP adapter for TASK-006 tool layer |
| Dockerfile | Container image definition for runtime deployment |
| requirements.txt | Python dependency: greennode-agentbase==1.0.3 |
| .dockerignore | Docker build exclusions (prevents .env, secrets, venv in image) |
| .env.example | Safe example configuration (all secrets empty, only public URLs/model names) |
| tests/test_task007b_spike.py | Local tests for spike agent URL contract, tool auth, SYN002846, SYN999999 |
| opencode.json | OpenCode CLI configuration (local tooling) |
| task-results/TASK-007B.0-FINAL.md | This audit report |

## Files Modified

| File | Change |
|---|---|
| .gitignore | Added: .agentbase/, .agentbase-state.json, .greennode.json, venv/, *.credentials.json |

## File Classification

### SHOULD_COMMIT

- .gitignore (modified -- infrastructure exclusions)
- main.py (TASK-007B.0 agent)
- tool_server.py (TASK-007B.0 tool adapter)
- Dockerfile (TASK-007B.0 container)
- requirements.txt (TASK-007B.0 dependency)
- .dockerignore (TASK-007B.0 docker exclusions)
- .env.example (safe example, no secrets)
- tests/test_task007b_spike.py (TASK-007B.0 local tests)
- task-results/TASK-007B.0-FINAL.md (audit evidence)

### LOCAL_ONLY

- opencode.json (OpenCode CLI configuration -- local tooling, not application source)
- .env (contains secrets -- git-ignored, not tracked)
- .agentbase/ (runtime state -- git-ignored)
- venv/ (virtual environment -- git-ignored)

### PRE_EXISTING

- None. All untracked files are new for TASK-007B.0.

### UNRELATED / INVESTIGATE

- None.

## Tests

### Compilation

```
python -m compileall -q src tests       -> COMPILE_EXIT=0
python -m compileall -q main.py tool_server.py -> COMPILE_EXIT=0
```

### Accepted Business Tests (regression)

| Test file | Tests | Result | Time |
|---|---|---|---|
| test_synthetic_data.py | 4 | OK | 9.7s |
| test_policy_engine.py | 25 | OK | 5.7s |
| test_recovery_engine.py | 26 | OK | 22.6s |
| test_evaluation_engine.py | 13 | OK | 33.3s |
| test_context_assembly.py | 14 | OK | 234.5s |
| test_tools.py | 16 | OK | 153.3s |
| test_nba.py | 11 | OK | 31.7s |

Accepted subtotal: 109 passed, 0 failed, 0 skipped

### TASK-007B.0 Spike Tests

| Test | Result |
|---|---|
| test_public_url_uses_only_approved_route | ok |
| test_deployment_defaults_are_loopback_only | ok |
| test_syn002846 | ok |
| test_unknown_cif | ok |
| test_authentication | ok |

Spike subtotal: 5 passed, 0 failed, 0 skipped

### Total

114 tests run, 114 passed, 0 failed, 0 skipped

## Git Status

Sanitized git status (no secret values):

```
 M .gitignore
?? .dockerignore
?? .env.example
?? Dockerfile
?? main.py
?? opencode.json
?? requirements.txt
?? task-results/TASK-007B.0-FINAL.md
?? tests/test_task007b_spike.py
?? tool_server.py
```

Tracked modifications: 1 (.gitignore)
Untracked files: 9 (8 application + 1 report)
Secret files (.env, .agentbase/, venv/): git-ignored, not tracked

## Secret Scan

SECRET_SCAN=PASS

- No secret values found in any untracked or modified file
- .env is git-ignored and not tracked
- .env.example contains only non-sensitive defaults (public URLs, model name, localhost)
- No Bearer token values in source files
- No GREENNODE_CLIENT_SECRET, LLM_API_KEY, or COLLECTION_TOOL_API_KEY values in source files

## Reasoning Content Audit

REASONING_CONTENT_EXPOSED=NO

- No reasoning_content field in runtime response (SYN002846 test)
- No reasoning_content field in runtime response (SYN999999 test)
- No reasoning_content in application source (main.py, tool_server.py)
- No reasoning_content in test artifacts
- No chain-of-thought persisted in any file

## Commit Status

NOT COMMITTED -- WAITING FOR PRODUCT OWNER APPROVAL

## Proposed Commit File List

```
.gitignore
.dockerignore
.env.example
Dockerfile
main.py
requirements.txt
task-results/TASK-007B.0-FINAL.md
tests/test_task007b_spike.py
tool_server.py
```

Excluded from commit (LOCAL_ONLY):

```
opencode.json
.env
.agentbase/
venv/
```

## Proposed Commit Message

```
TASK-007B.0 pass GreenNode end-to-end connectivity spike
```
