# TASK-007B FINAL REPORT

## Final Status

TASK-007B PASS — GREENNODE COLLECTION DECISION AGENT PROVEN

## Implementation Summary

Built the real GreenNode Collection Decision Agent on top of the accepted
deterministic business engines (TASK-001 through TASK-007A).

The agent answers Collection Officer questions using customer context,
collection history, cashflow intelligence, policy/routing, recovery
opportunity, and the deterministic next best action from TASK-007A.

Core product promise delivered:

```
RIGHT CUSTOMER
RIGHT ACTION
RIGHT TIME
EXPLAINABLE REASON
```

The agent is NOT the source of truth for collection decisions.
The deterministic engines are the source of truth.
The LLM may only summarize, explain, and organize evidence.
The LLM may NEVER change treatment, channel, objective, WHEN, routing,
score, rule_id, or override hard policy.

## Agent Modes

### PLAN

Returns the deterministic collection plan for a CIF.

Tool routing: `get_next_best_action` → optionally `get_customer_360`.

Response states WHO, WHY, WHAT, WHEN, HOW, EXPECTED OUTCOME.
All decision values come from `get_next_best_action` (TASK-007A engine).

### INVESTIGATE

Explains important customer facts without changing the decision.

Tool routing: `get_next_best_action`, `get_customer_360`.

Evidence includes: DPD, debt, cashflow, recent inflow, PTP, call history,
routing, recovery opportunity. No fabricated fields.

### EXPLAIN

Explains WHY the deterministic engine selected the current NBA.

Tool routing: `get_next_best_action`.

Grounded in rule_id / reason_code / evidence from the tool.
Clearly distinguishes DETERMINISTIC DECISION from AI EXPLANATION.
Never invents a new reason.

### SIMULATE

Interface/mode contract only. Full What-if engine is TASK-008.

Returns structured `NOT_IMPLEMENTED` / `TASK_008_REQUIRED` result.
Does not mutate source data.
Does not recompute decision using LLM assumptions.
Does not invent hypothetical business rules.

## Tool #7

### get_next_best_action

Input:

```json
{"cif": "SYN002846"}
```

Delegates to the accepted TASK-007A engine (`msb_nba.engine.decide`).
Does NOT duplicate TASK-007A logic.

Output exposes structured deterministic decision data:

- cif
- final_route
- treatment
- channel
- objective
- when
- rule_id
- priority
- reason_code
- decision_trace
- evidence_refs (selected_rule_facts, best_window)
- recovery_opportunity_score
- provenance

Tool errors use existing structured error conventions (`ToolEnvelope`).
Unknown CIF returns `NOT_FOUND`.
No private chain-of-thought exposed.

## Deterministic Decision Safety

The LLM cannot modify any of the following decision fields.
These fields are set from `get_next_best_action` tool output BEFORE
the LLM is called. The LLM output only affects the `summary` string.

| Field | Source | LLM can change? |
|---|---|---|
| treatment | get_next_best_action (TASK-007A) | NO |
| channel | get_next_best_action (TASK-007A) | NO |
| objective | get_next_best_action (TASK-007A) | NO |
| when | get_next_best_action (TASK-007A) | NO |
| final_route | get_next_best_action (TASK-007A) | NO |
| rule_id | get_next_best_action (TASK-007A) | NO |
| reason_code | get_next_best_action (TASK-007A) | NO |
| score | get_recovery_opportunity (TASK-003) | NO |
| routing | get_collection_policy (TASK-002) | NO |

Enforcement is structural: the `decision` dict in `AgentResponse` is
built from `decision_from_nba(nba_data)` before the LLM is invoked.
The LLM return value is only used for the `summary` field.

If the user asks the agent to override the engine, the agent returns
the deterministic recommendation and the decision is unchanged.

## SYN002846 Evidence

### Deterministic tool output (get_next_best_action)

```json
{
  "cif": "SYN002846",
  "final_route": "CALL",
  "hard_suppressed": false,
  "treatment": "WAIT_SELF_CURE",
  "channel": "NONE",
  "objective": "PAYMENT",
  "when": {"type": "NONE", "datetime": null, "date": null, "window": null},
  "rule_id": "NBA-300",
  "priority": "P7",
  "reason_code": "CALL_SELF_CURE",
  "recovery_opportunity_score": 47,
  "evidence_refs": {
    "selected_rule_facts": {
      "max_dpd_cif": 11,
      "net_cashflow_30d": 168000000,
      "inflow_7d": 48000000,
      "inflow_3d": 24000000,
      "ptp_state": "NONE",
      "final_route": "CALL",
      "hard_suppressed": false,
      "cashflow_available": true,
      "latest_business_outcome": null,
      "source_next_action_date": null,
      "promise_date": null
    }
  }
}
```

### Agent PLAN response

```
status: success
mode: PLAN
cif: SYN002846
decision:
  final_route: CALL
  treatment: WAIT_SELF_CURE
  channel: NONE
  objective: PAYMENT
  when: {type: NONE}
  rule_id: NBA-300
  reason_code: CALL_SELF_CURE
summary:
  WHO: SYN002846
  WHY: NBA-300 (CALL_SELF_CURE)
  WHAT: WAIT_SELF_CURE
  WHEN: No immediate action timing required
  HOW: NONE
  EXPECTED OUTCOME: PAYMENT
tools_used: [get_next_best_action, get_customer_360]
```

This case proves the thesis:

```
route is CALL
but next best action is WAIT_SELF_CURE
```

The agent did NOT turn this into CALL NOW / CONTACT / REMIND / PTP FOLLOW UP
or any other action.

## SYN999999 Evidence

### Agent response (all modes)

```
status: error
cif: SYN999999
decision: null
evidence: []
error: {code: NOT_FOUND, message: "CIF 'SYN999999' was not found"}
summary: "CIF SYN999999 was not found; no fabricated customer data."
```

No fabricated customer.
No substituted CIF.
No deterministic recommendation.
No LLM-generated customer narrative.

## GreenNode Evidence

| Component | Status |
|---|---|
| AgentBase | `greennode-agentbase==1.0.3` (GreenNodeAgentBaseApp, PingStatus, RequestContext) |
| GLM-5.2 | `z-ai/glm-5.2-hackathon` via GreenNode MaaS (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL env vars) |
| Canonical model | `glm-5.2` |
| Tool calls | `get_next_best_action`, `get_customer_360` via in-process or HTTP tool caller |
| Runtime | Reuses TASK-007B.0 AgentBase entrypoint, connectivity_check, ping |
| TLS verification | Not disabled |
| Secrets | Not exposed in source, not in response, not in artifacts |

### AgentBase entrypoint

```python
@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
    if payload.get("connectivity_check") == "maas":
        return _maas_probe()
    mode, cif, message = parse_payload(payload)
    runtime = _build_runtime()
    response = runtime.invoke(mode, cif, message)
    return response.to_dict()
```

### Tool caller architecture

- In-process: `invoke_tool(name, args, repository=repo)` — for local testing
- HTTP: `_post_json(_tool_url(name), args, api_key)` — for GreenNode deployment
- LLM: `GreenNodeMaaSClient` via `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`
- LLM is optional: when not configured, deterministic template summaries are used

No secrets stored in this report.

## Tests

### Compilation

```
python -m compileall -q src tests main.py tool_server.py  -> COMPILE_EXIT=0
```

### Accepted Business Tests (regression)

| Test file | Tests | Result |
|---|---|---|
| test_synthetic_data.py | 4 | OK |
| test_policy_engine.py | 25 | OK |
| test_recovery_engine.py | 26 | OK |
| test_evaluation_engine.py | 13 | OK |
| test_context_assembly.py | 14 | OK |
| test_tools.py | 16 | OK |
| test_nba.py | 11 | OK |
| test_task007b_spike.py | 5 | OK |

Accepted subtotal: 114 passed, 0 failed, 0 skipped

### TASK-007B Agent Tests

| Test class | Tests | Result |
|---|---|---|
| TestGetNextBestActionDelegation | 3 | OK |
| TestSyn002846DeterministicFields | 2 | OK |
| TestPlanMode | 3 | OK |
| TestExplainCannotAlterNBA | 3 | OK |
| TestInvestigateOnlyUsesExistingEvidence | 3 | OK |
| TestSimulateReturnsTask008Required | 4 | OK |
| TestSyn999999NoFabrication | 5 | OK |
| TestModelOutputCannotOverrideDecision | 5 | OK |
| TestReasoningContentNeverExposed | 3 | OK |
| TestSecretsNotExposed | 3 | OK |
| TestExistingRegressionsPreserved | 4 | OK |
| TestRouterDeterminism | 5 | OK |
| TestAgentResponseContract | 4 | OK |
| TestToolServerGetNextBestAction | 1 | OK |

TASK-007B subtotal: 48 passed, 0 failed, 0 skipped

### Required Test Coverage (11 areas)

| # | Required test | Covered by |
|---|---|---|
| 1 | get_next_best_action delegates to TASK-007A | TestGetNextBestActionDelegation |
| 2 | SYN002846 deterministic fields preserved | TestSyn002846DeterministicFields |
| 3 | PLAN returns accepted NBA | TestPlanMode |
| 4 | EXPLAIN cannot alter NBA | TestExplainCannotAlterNBA |
| 5 | INVESTIGATE only uses existing evidence | TestInvestigateOnlyUsesExistingEvidence |
| 6 | SIMULATE returns TASK_008_REQUIRED | TestSimulateReturnsTask008Required |
| 7 | SYN999999 no fabrication | TestSyn999999NoFabrication |
| 8 | model output cannot override deterministic decision | TestModelOutputCannotOverrideDecision |
| 9 | reasoning_content never exposed | TestReasoningContentNeverExposed |
| 10 | secrets not exposed | TestSecretsNotExposed |
| 11 | existing regressions remain PASS | TestExistingRegressionsPreserved + all regression suites |

### Total

```
162 tests run, 162 passed, 0 failed, 0 skipped
```

## Business Drift

BUSINESS_SEMANTICS_DRIFT=0

Verified via `git diff HEAD -- src/msb_nba/ src/msb_policy/ src/msb_recovery/ src/msb_synthetic/ src/msb_context/ src/msb_evaluation/` = empty.

Accepted business engines unchanged:

- TASK-001 (src/msb_synthetic/) — unchanged
- TASK-002 (src/msb_policy/) — unchanged
- TASK-003 (src/msb_recovery/) — unchanged
- TASK-004 (src/msb_evaluation/) — unchanged
- TASK-005 (src/msb_context/) — unchanged
- TASK-006 (src/msb_tools/) — semantics unchanged; tool #7 registered, forbidden check updated to exempt decision tool, tool count updated from 6 to 7
- TASK-007A (src/msb_nba/) — unchanged

get_next_best_action delegates to TASK-007A (`msb_nba.engine.decide`).
No business rules duplicated.

## Files Created

| File | Purpose |
|---|---|
| src/msb_agent/__init__.py | Agent module package |
| src/msb_agent/models.py | AgentResponse dataclass, mode constants, decision projection |
| src/msb_agent/router.py | Deterministic mode + CIF routing from payload |
| src/msb_agent/llm.py | LLM client interface and GreenNode MaaS implementation |
| src/msb_agent/runtime.py | AgentRuntime with PLAN, INVESTIGATE, EXPLAIN, SIMULATE modes |
| tests/test_task007b.py | 48 tests covering all 11 required test areas |
| task-results/TASK-007B-FINAL.md | This report |

## Files Modified

| File | Change |
|---|---|
| main.py | Replaced spike handler with 4-mode agent runtime; preserved connectivity_check, _customer_360 URL contract, AgentBase entrypoint |
| tool_server.py | Generalized dispatch to any registered tool (was hardcoded to get_customer_360); supports get_next_best_action |
| src/msb_tools/tools.py | Added get_next_best_action tool function (delegates to msb_nba.engine.decide) |
| src/msb_tools/registry.py | Registered get_next_best_action as tool #7 |
| src/msb_tools/repository.py | Added calls_for_cif() helper for efficient per-CIF call lookup |
| src/msb_tools/schemas.py | Added NextBestActionOutput schema, tool entry, description; updated tool_count to 7 |
| src/msb_tools/validate.py | Updated tool count to 7; forbidden check exempts decision tool (get_next_best_action) |
| tests/test_tools.py | Updated registry, schema count, forbidden check, and schema validation for 7 tools |

## Git Status

```
M main.py
M src/msb_tools/registry.py
M src/msb_tools/repository.py
M src/msb_tools/schemas.py
M src/msb_tools/tools.py
M src/msb_tools/validate.py
M tests/test_tools.py
M tool_server.py
?? src/msb_agent/
?? tests/test_task007b.py
?? task-results/TASK-007B-FINAL.md
```

Tracked modifications: 8
Untracked files: 3 (agent module, test file, report)

## Secret Scan

SECRET_SCAN=PASS

- No secret values in any source file
- LLM_API_KEY, COLLECTION_TOOL_API_KEY read from env vars at runtime
- No Bearer token values in source
- No reasoning_content in any response or artifact

## Reasoning Content Audit

REASONING_CONTENT_EXPOSED=NO

- LLM client extracts only `content` and `model` from MaaS response
- `reasoning_content` field never read, never passed through
- AgentResponse has no reasoning_content field
- Verified by TestReasoningContentNeverExposed (3 tests)

## Commit Status

NOT COMMITTED — WAITING FOR PRODUCT OWNER APPROVAL
