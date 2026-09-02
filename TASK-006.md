# TASK-006 — GREENNODE COLLECTION TOOL LAYER

## STATUS

AUTHORIZED AFTER TASK-005 ACCEPTANCE

Accepted checkpoints:

TASK-001 = ACCEPTED
TASK-002 = ACCEPTED
TASK-003 = ACCEPTED
TASK-004 = ACCEPTED
TASK-005 = ACCEPTED

Expected baseline:

f1b8791 TASK-005 pass decision context assembly

TASK-006 must remain uncommitted until independent audit ACCEPT.

---

# 1. PURPOSE

Build the deterministic tool boundary between the accepted Collection
Decision foundation and the future GreenNode Collection Decision Agent.

TASK-006 exposes accepted data and deterministic business results
through small, typed, auditable tools.

Architecture:

TASK-001 Synthetic Data
        ?
TASK-002 Policy Engine
        ?
TASK-003 Recovery Opportunity
        ?
TASK-004 Evaluation
        ?
TASK-005 Decision Context
        ?
TASK-006 Tool Layer
        ?
TASK-007 GreenNode Collection Decision Agent

TASK-006 DOES NOT implement the Agent.

TASK-006 DOES NOT allow an LLM to create, modify or override business
rules.

---

# 2. CORE PRINCIPLE

The deterministic engines remain the source of truth.

The future LLM/Agent may:

- request information;
- inspect portfolio context;
- inspect customer context;
- inspect evidence;
- inspect policy;
- inspect recovery scoring;
- compare accepted ranking information.

The future LLM/Agent may NOT:

- calculate a replacement score;
- override routing;
- invent customer facts;
- invent PTP;
- invent cashflow;
- invent recovery probability;
- invent treatment rules;
- silently modify deterministic results.

Rule:

TOOL-BOUNDARY-001

---

# 3. REQUIRED READING

Before coding read completely:

1. TASK-006.md
2. TASK-005.md
3. TASK-004.md
4. TASK-003.md
5. TASK-003_SCORING_CONTRACT.md
6. TASK-002.md
7. TASK-001.md

and:

8. docs/spec-v1/PRODUCT_SPEC_V1.md
9. docs/spec-v1/RULE_BASE_V1.md
10. docs/spec-v1/SYNTHETIC_DATA_SPEC.md
11. docs/spec-v1/GOLDEN_SCENARIOS_V1.md
12. docs/spec-v1/README.md
13. docs/spec-v1/UBUNTU_BUILD_HANDOFF.md

Inspect accepted implementations:

src/msb_synthetic/
src/msb_policy/
src/msb_recovery/
src/msb_evaluation/
src/msb_context/

and all accepted tests.

Do not rely on conversation summaries.

Repository specifications are authoritative.

---

# 4. SPEC PRECEDENCE

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
TASK-003_SCORING_CONTRACT.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

TASK-005 defines authoritative Decision Context semantics.

TASK-006 defines tool interface semantics only.

TASK-006 MUST NOT redefine business rules.

---

# 5. REQUIRED TOOL SET

Implement exactly these six logical collection tools:

1. Portfolio Tool
2. Customer 360 Tool
3. Collection History Tool
4. Cashflow Intelligence Tool
5. Collection Policy Tool
6. Recovery Opportunity Tool

Do not add additional business tools without explicit authorization.

Rule:

TOOL-SET-001

---

# 6. TOOL 1 — PORTFOLIO TOOL

Logical name:

get_portfolio

Purpose:

Expose accepted portfolio prioritization information to a future Agent.

Source:

TASK-005 portfolio_context_index.

Inputs:

limit
offset

Optional filters ONLY if already represented by accepted facts:

final_route
movement
hard_suppressed

No semantic filters may be invented.

Default:

limit = 20
offset = 0

Maximum:

limit = 100

This maximum is technical payload protection, not business policy.

Required output per CIF:

cif
final_route
hard_suppressed
total_outstanding_cif
max_dpd_cif
baseline_rank
recovery_rank
rank_delta
movement
recovery_opportunity_score
business_urgency_score
ability_to_pay_score
willingness_to_pay_score
contactability_score
timing_opportunity_score
strategic_adjustment_score
availability

Required metadata:

total_matching
limit
offset
synthetic_data
synthetic_label
reference_date

Default order:

recovery_rank ASC

The tool MUST NOT calculate a new ranking.

Rule:

TOOL-PORTFOLIO-001

---

# 7. PORTFOLIO PAGINATION

Validation:

limit >= 1
limit <= 100
offset >= 0

Invalid values must return typed validation failure.

Do not silently coerce invalid input.

Rule:

TOOL-PAGINATION-001

---

# 8. PORTFOLIO FILTERS

Allowed:

final_route
movement
hard_suppressed

Filters must use exact accepted values.

Unknown filter value:

typed validation failure.

No fuzzy interpretation.

No LLM involvement.

Rule:

TOOL-FILTER-001

---

# 9. TOOL 2 — CUSTOMER 360 TOOL

Logical name:

get_customer_360

Input:

cif

Source:

TASK-005 authoritative Decision Context.

Output:

the complete accepted TASK-005 context for the CIF,
subject only to deterministic serialization.

The tool MUST NOT summarize or reinterpret it.

Unknown CIF:

typed NOT_FOUND.

Do not return an empty object.

Rule:

TOOL-CUSTOMER-001

---

# 10. CUSTOMER 360 IMMUTABILITY

For every CIF:

tool output
=
accepted TASK-005 Decision Context

except for a possible outer tool envelope.

No inner customer facts may change.

Rule:

TOOL-CUSTOMER-IMMUTABILITY-001

---

# 11. TOOL 3 — COLLECTION HISTORY TOOL

Logical name:

get_collection_history

Input:

cif

Optional:

event_types
limit

Allowed event types:

CALL
OPERATION
PAYMENT
PTP

If TASK-005/source semantics make PTP part of OPERATION rather than a
separate event family, preserve the source distinction and document
the mapping.

Do NOT duplicate one source event as two factual events merely to
satisfy a tool label.

Default limit:

20

Maximum:

100

Output should expose accepted/source historical events.

Each event must identify:

event_type
source_id
event_date/time
source-specific factual payload

Technical call status remains technical.

Business operation result remains business outcome.

Rule:

TOOL-HISTORY-001

---

# 12. HISTORY ORDERING

Default:

event timestamp DESC

Tie-break:

stable source identifier ASC

Same accepted deterministic ordering principle as TASK-005.

Rule:

TOOL-HISTORY-ORDER-001

---

# 13. HISTORY BOUNDARY

Never convert:

call technical Success

into:

PTP
payment
recovery success.

Never convert UTC/PTP/NPTP/RTP/etc into technical PBX status.

Rule:

TOOL-HISTORY-BOUNDARY-001

---

# 14. TOOL 4 — CASHFLOW INTELLIGENCE TOOL

Logical name:

get_cashflow_intelligence

Input:

cif

Source:

TASK-005 cashflow context
+
accepted TASK-003 evidence.

Required output where available:

cashflow_available

inflow_3d
inflow_7d
inflow_30d
outflow_30d
net_cashflow_30d

net_cashflow_windows_30d
positive_cashflow_windows

income-source evidence where exposed

liquidity_to_due_ratio

recent_transactions

accepted relevant scoring evidence/rule IDs

Missing semantics MUST remain exactly consistent with TASK-005.

If:

cashflow_available = false

unavailable analytical fields must remain null.

Do NOT transform null to zero.

Rule:

TOOL-CASHFLOW-001

---

# 15. CASHFLOW NON-PREDICTION

The tool MUST NOT return:

payment_probability
recovery_probability
cure_probability
expected_payment
expected_recovery
future_income
forecast_cashflow

Rule:

TOOL-CASHFLOW-NO-PREDICT-001

---

# 16. TOOL 5 — COLLECTION POLICY TOOL

Logical name:

get_collection_policy

Input:

cif

Source:

accepted TASK-002 / TASK-005 policy facts.

Required:

base_route
challenge_override_route
final_route
hard_suppressed
source_next_action_date
source_next_operation_channel

where those source fields exist.

Also expose deterministic policy trace / applicable accepted rule IDs
where available.

The tool MUST distinguish:

SOURCE NEXT ACTION

from:

AI RECOMMENDATION.

No recommended treatment/channel/time exists in TASK-006.

Rule:

TOOL-POLICY-001

---

# 17. POLICY AUTHORITY

Policy tool is READ ONLY.

It MUST NOT accept:

new_route
override_route
suppress
unsuppress
treatment
channel
when

or any write/update command.

Rule:

TOOL-POLICY-READONLY-001

---

# 18. TOOL 6 — RECOVERY OPPORTUNITY TOOL

Logical name:

get_recovery_opportunity

Input:

cif

Source:

accepted TASK-003
+
TASK-004 comparison evidence
+
TASK-005 context.

Required:

recovery_opportunity_score

business_urgency_score
ability_to_pay_score
willingness_to_pay_score
contactability_score
timing_opportunity_score
strategic_adjustment_score

baseline_rank
recovery_rank
rank_delta
absolute_rank_delta
normalized_rank_delta
movement

primary_movement_factors

structured score evidence
accepted rule IDs

No recalculation using different formulas.

Rule:

TOOL-RECOVERY-001

---

# 19. RECOVERY SCORE IS NOT PROBABILITY

The tool schema/documentation must explicitly state:

Recovery Opportunity Score is an explainable prototype prioritization
score.

It is NOT:

probability of payment
probability of cure
expected recovery
expected monetary value

Rule:

TOOL-RECOVERY-NONCLAIM-001

---

# 20. COMMON TOOL ENVELOPE

Every tool call should return a consistent typed envelope.

Suggested success:

{
  "ok": true,
  "tool": "...",
  "data": ...,
  "meta": {
    "synthetic_data": true,
    "synthetic_label": "SYNTHETIC PROTOTYPE DATA",
    "reference_date": "2026-08-28"
  },
  "error": null
}

Suggested failure:

{
  "ok": false,
  "tool": "...",
  "data": null,
  "meta": {...},
  "error": {
    "code": "...",
    "message": "..."
  }
}

Rule:

TOOL-ENVELOPE-001

Do not expose stack traces as user-facing tool output.

---

# 21. ERROR CODES

Required minimum:

INVALID_ARGUMENT
NOT_FOUND
DATA_INTEGRITY_ERROR

Optional technical:

INTERNAL_ERROR

Do not use a business outcome as an error code.

Rule:

TOOL-ERROR-001

---

# 22. INPUT VALIDATION

All tool inputs must be validated before execution.

Examples:

missing CIF
blank CIF
unknown CIF
negative offset
limit 0
limit >100
unknown route filter
unknown movement
unknown event type

must not produce ambiguous success.

Rule:

TOOL-INPUT-001

---

# 23. SYNTHETIC PROVENANCE

Every tool response MUST clearly retain:

synthetic_data = true

synthetic_label =
SYNTHETIC PROTOTYPE DATA

reference_date =
accepted reference date

Rule:

TOOL-PROVENANCE-001

This applies to errors too where metadata can be safely constructed.

---

# 24. READ-ONLY CONTRACT

All six tools are read-only.

No tool may mutate:

source data
PolicyResult
RecoveryResult
EvaluationResult
Decision Context
artifact files

Rule:

TOOL-READONLY-001

---

# 25. NO SYSTEM CLOCK

Do not use system time for business semantics.

No:

datetime.now()
date.today()
time.time()

for reference-date decisions.

Use accepted deterministic reference date.

Rule:

TOOL-DATE-001

Runtime timing metrics are unnecessary in TASK-006.

---

# 26. NO NETWORK DEPENDENCY FOR BUSINESS TESTS

Core tool behavior must run locally without:

GreenNode API
internet
external database
external service
LLM

Rule:

TOOL-OFFLINE-001

This is required so business/tool contracts can be independently tested.

---

# 27. GREENNODE INTEGRATION BOUNDARY

TASK-006 should prepare tool definitions/adapters suitable for later
GreenNode AgentBase integration.

However:

TASK-006 must NOT deploy an Agent.

TASK-006 must NOT implement autonomous reasoning.

TASK-006 must NOT send prompts to MaaS.

TASK-006 must NOT require GreenNode credentials for deterministic tests.

Allowed:

- tool schema definitions;
- AgentBase-compatible adapter structure if directly supported by the
  installed GreenNode skills/docs;
- local deterministic invocation;
- documentation describing future AgentBase registration.

Rule:

TOOL-GREENNODE-BOUNDARY-001

---

# 28. GREENNODE SKILL DISCOVERY

Before implementing any AgentBase-specific adapter, inspect the
installed GreenNode AgentBase skills and repository documentation.

Relevant skills include:

/agentbase-wizard
/agentbase
/agentbase-llm
/agentbase-deploy
/agentbase-monitor
/agentbase-identity
/agentbase-memory
/agentbase-gateway
/agentbase-policy

TASK-006 primarily concerns tool contracts.

Do NOT use /agentbase-llm to create business logic.

Do NOT deploy in TASK-006.

If the installed GreenNode skills do not define a stable tool adapter
contract:

implement framework-neutral typed tools first.

Do NOT invent a fake AgentBase SDK/API.

Rule:

TOOL-GREENNODE-DISCOVERY-001

---

# 29. GREENNODE PLATFORM POLICY DISTINCTION

GreenNode /agentbase-policy concerns platform/runtime policy.

Collection Policy Tool concerns MSB collection business policy.

They MUST remain separate concepts.

Rule:

TOOL-POLICY-DISTINCTION-001

---

# 30. TOOL SCHEMAS

Every tool must expose a machine-readable input/output schema.

Preferred:

Python typed dataclass / TypedDict / Pydantic only if already available
and justified.

Avoid adding a heavy dependency merely for schema validation.

JSON-schema-compatible representation is recommended.

Required schemas:

PortfolioInput
PortfolioOutput

Customer360Input
Customer360Output

CollectionHistoryInput
CollectionHistoryOutput

CashflowIntelligenceInput
CashflowIntelligenceOutput

CollectionPolicyInput
CollectionPolicyOutput

RecoveryOpportunityInput
RecoveryOpportunityOutput

Common ToolEnvelope
ToolError

Rule:

TOOL-SCHEMA-001

---

# 31. SCHEMA EXPORT

Generate a deterministic machine-readable artifact:

tool_schemas.json

It must describe all six tools.

No timestamps that break determinism.

Rule:

TOOL-SCHEMA-EXPORT-001

---

# 32. TOOL REGISTRY

Provide a deterministic local registry.

Conceptually:

registry = {
  "get_portfolio": ...,
  "get_customer_360": ...,
  "get_collection_history": ...,
  "get_cashflow_intelligence": ...,
  "get_collection_policy": ...,
  "get_recovery_opportunity": ...
}

Exactly six business tools.

Rule:

TOOL-REGISTRY-001

---

# 33. TOOL INVOCATION

Provide one framework-neutral deterministic invocation entry point.

Conceptually:

invoke_tool(tool_name, arguments)

Unknown tool:

INVALID_ARGUMENT
or a dedicated typed UNKNOWN_TOOL error if explicitly documented.

Do not dynamically eval code.

Rule:

TOOL-INVOKE-001

---

# 34. TOOL SECURITY

Tool invocation must not allow:

arbitrary file path reads
shell commands
Python eval/exec
SQL supplied by caller
network URL supplied by caller
arbitrary module import

Rule:

TOOL-SECURITY-001

---

# 35. PAYLOAD SIZE

Portfolio and history tools must use pagination/limits.

Customer 360 is one CIF only.

Do not expose all 3,000 complete Customer 360 objects through one call.

Rule:

TOOL-PAYLOAD-001

---

# 36. DATA SOURCE

Preferred TASK-006 source:

accepted TASK-005 deterministic artifacts/context access layer.

Do not independently reconstruct different business facts if TASK-005
already provides them.

Use earlier stages only where required to expose full source history
that TASK-005 intentionally previews.

Rule:

TOOL-SOURCE-001

---

# 37. HISTORY SOURCE EXCEPTION

Collection History may require full source events beyond TASK-005
preview limit.

It may read accepted TASK-001 synthetic source event files.

It must not reinterpret them.

TASK-005 remains authoritative for derived context.

Rule:

TOOL-HISTORY-SOURCE-001

---

# 38. G01 TOOL CONTRACT

For G01 verify:

Portfolio:
baseline rank 1
Recovery rank 917
movement DEMOTED

Customer360:
cashflow_available false
missing cashflow-derived facts remain null

Policy:
CALL final route

Recovery:
score 28
accepted components preserved

No tool invents a treatment.

Rule:

TOOL-G01-001

---

# 39. G02 TOOL CONTRACT

For G02 verify:

Portfolio:
baseline 1209
Recovery 84
movement PROMOTED

Customer360:
accepted complete context

Cashflow:
40,000,000 recent inflow evidence

Policy:
CALL

Recovery:
score 58
accepted components

History:
technical successful contact and applicable business/PTP evidence remain
distinct.

Rule:

TOOL-G02-001

---

# 40. G04 TOOL CONTRACT

Verify:

BROKEN PTP
recent inflow
successful technical contact
accepted score/ranking

No treatment:

PTP_RECOVERY

may be generated by TASK-006.

That belongs to later decision logic.

Rule:

TOOL-G04-001

---

# 41. G07 / G08

G07:

base CBS
override CALL
final CALL

G08:

base CALL
override CBS
final CBS

Policy tool and Customer360 must agree exactly.

Rule:

TOOL-ROUTE-GOLDEN-001

---

# 42. G19

Verify:

technical call Success exists

business PTP absent

willingness score remains accepted value 0

No tool labels technical Success as recovery/payment success.

Rule:

TOOL-G19-001

---

# 43. G20

Customer360 must expose exactly:

3 loans

100M DPD4
250M DPD12
50M DPD7

total outstanding 400M
MAX DPD 12

Portfolio/Policy/Recovery tools must agree on accepted aggregate facts
where those fields are exposed.

Rule:

TOOL-G20-001

---

# 44. CROSS-TOOL CONSISTENCY

For the same CIF, shared facts must agree across tools.

Examples:

Customer360.final_route
=
CollectionPolicy.final_route
=
Portfolio.final_route

Customer360.recovery score
=
RecoveryOpportunity.recovery score
=
Portfolio.recovery score

Customer360 ranks
=
Portfolio ranks
=
RecoveryOpportunity ranks

Rule:

TOOL-CONSISTENCY-001

Required mismatch count:

0.

---

# 45. NO FUTURE DECISION FIELDS

TASK-006 must not output:

treatment
recommended_treatment
next_best_action
recommended_channel
recommended_when
best_contact_time
action_priority
expected_recovery
expected_payment
recovery_probability
payment_probability
cure_probability
confidence_score
AI reasoning
Agent decision

Source-specific fields such as:

source_next_operation_channel

remain allowed.

Rule:

TOOL-NO-FUTURE-DECISION-001

---

# 46. NO NATURAL LANGUAGE AGENT REASONING

Tool outputs are structured facts.

No:

agent_reasoning
chain_of_thought
ai_explanation
model_explanation

Rule:

TOOL-NO-REASONING-001

Future Agent may create a concise explanation grounded in these facts.

---

# 47. NUMERIC SAFETY

Preserve accepted numeric semantics.

Money:

integer VND.

Exact ratios:

Decimal or deterministic string representation.

Do not introduce binary float drift.

Rule:

TOOL-NUMERIC-001

---

# 48. DETERMINISM

Same input + same arguments:

byte-equivalent serialized response.

Schema export must also be deterministic.

No random IDs.

Rule:

TOOL-DETERMINISM-001

---

# 49. REQUIRED PACKAGE

Preferred:

src/msb_tools/

Suggested:

__init__.py
models.py
errors.py
repository.py
portfolio.py
customer.py
history.py
cashflow.py
policy.py
recovery.py
registry.py
schemas.py
cli.py
validate.py

Keep simple.

Do not over-engineer.

---

# 50. LOCAL CLI

Provide a local invocation CLI.

Example:

PYTHONPATH=src python -m msb_tools.cli \
  --input build/synthetic-data \
  --tool get_customer_360 \
  --args '{"cif":"GOLDEN_G02"}'

Examples should also work for:

get_portfolio
get_collection_history
get_cashflow_intelligence
get_collection_policy
get_recovery_opportunity

No server required.

Rule:

TOOL-CLI-001

---

# 51. REQUIRED ARTIFACTS

Preferred:

build/tools/

Required:

tool_schemas.json
tool_registry_manifest.json
golden_tool_validation.json

Optional:

sample_tool_responses.json

if deterministic and clearly synthetic.

Rule:

TOOL-ARTIFACT-001

---

# 52. REGISTRY MANIFEST

tool_registry_manifest.json must contain:

tool count = 6

tool names

schema version

synthetic provenance

reference date

No nondeterministic timestamp.

Rule:

TOOL-MANIFEST-001

---

# 53. VALIDATOR

Implement independent TASK-006 validation.

Preferred:

PYTHONPATH=src python -m msb_tools.validate \
  --input /tmp/.../synthetic \
  --output /tmp/.../tools/golden_tool_validation.json

At minimum validate:

- exactly six registered tools;
- schema export contains exactly six tool definitions;
- valid/invalid inputs;
- 3,000-CIF portfolio source integrity;
- pagination;
- filters;
- Customer360 equality;
- history boundary;
- cashflow missing semantics;
- policy immutability;
- Recovery immutability;
- cross-tool consistency;
- G01;
- G02;
- G04;
- G07;
- G08;
- G19;
- G20;
- synthetic provenance;
- forbidden fields absent;
- no source mutation.

Do not unconditionally mark Golden scenarios PASS.

Rule:

TOOL-VALIDATOR-001

---

# 54. REQUIRED TESTS

At minimum test:

1. exactly six registered tools
2. unknown tool fails
3. schema export deterministic
4. registry manifest deterministic

Portfolio:
5. default limit 20
6. limit 1
7. limit 100
8. limit 0 fails
9. limit 101 fails
10. negative offset fails
11. offset beyond result set returns deterministic empty page
12. route filter
13. movement filter
14. hard_suppressed filter
15. invalid filter fails
16. recovery_rank ordering preserved

Customer360:
17. G02 exact context equality
18. unknown CIF NOT_FOUND
19. blank CIF fails

History:
20. history deterministic ordering
21. limit
22. invalid event type
23. G19 technical/business boundary

Cashflow:
24. G01 missing cashflow remains null
25. available legitimate zero remains zero
26. G02 cashflow evidence preserved

Policy:
27. G07
28. G08
29. no mutation/write interface

Recovery:
30. G01
31. G02
32. score/components/ranks exact

Cross-tool:
33. shared facts equal
34. G20 aggregation consistency

Safety:
35. forbidden future decision fields absent
36. synthetic provenance every tool
37. no arbitrary path input
38. no eval/exec/shell/network caller functionality

Determinism:
39. repeated invocation identical
40. artifact A/B hashes identical

Regression:
41. accepted TASK-001 tests
42. accepted TASK-002 tests
43. accepted TASK-003 tests
44. accepted TASK-004 tests
45. accepted TASK-005 tests

Tests must not depend on GreenNode credentials.

---

# 55. TOOL SCHEMA QUALITY

Each tool description should be concise and explicit enough for a future
LLM to select correctly.

Descriptions must state what the tool RETURNS.

Descriptions must not tell the LLM to make unsupported predictions.

Bad:

"Predict whether the customer will pay."

Good:

"Return accepted Recovery Opportunity score, component scores, ranks,
movement and supporting deterministic evidence for one synthetic CIF."

Rule:

TOOL-DESCRIPTION-001

---

# 56. FUTURE AGENT COMPATIBILITY

TASK-006 should make TASK-007 possible without changing business
engines.

TASK-007 should be able to consume:

tool registry
tool schemas
tool responses

and perform reasoning on top.

If TASK-007 would need direct database/source access because TASK-006
omitted a required accepted fact:

report it during TASK-006.

Do not invent future decision semantics to solve it.

---

# 57. PRECHECK

Before coding return:

# TASK-006 PRECHECK

## GIT

HEAD:
working_tree:
spec_drift:

Expected accepted baseline:
f1b8791 TASK-005 pass decision context assembly

## ACCEPTED STAGES

TASK-001:
TASK-002:
TASK-003:
TASK-004:
TASK-005:

## TOOL CONTRACT

Portfolio:
Customer360:
History:
Cashflow:
Policy:
Recovery:

## DATA SOURCES

TASK-005:
TASK-001 history exception:

## GREENNODE DISCOVERY

Installed skills found:
Tool adapter contract found:
Framework-neutral fallback required:

## FORBIDDEN SCOPE

Agent:
MaaS invocation:
AgentBase deployment:
LLM reasoning:
treatment:
channel recommendation:
best time:
probability:
expected recovery:
ML:
frontend:
AEV/ROI:

All must be absent.

## BLOCKERS

NONE

or exact blocker.

If GreenNode-specific tool adapter semantics are unavailable:

DO NOT BLOCK TASK-006.

Use framework-neutral tool contracts.

If an accepted business/data semantic required by a tool is genuinely
undefined:

STOP.

Return:

TASK-006 BLOCKED — REQUIRED TOOL SEMANTIC UNDEFINED

---

# 58. IMPLEMENTATION GATES

T6-01 Repository
- accepted TASK-005 HEAD
- clean before implementation
- no spec drift

T6-02 Registry
- exactly 6 tools

T6-03 Schema
- six deterministic schemas

T6-04 Portfolio
- pagination/filter/order correct

T6-05 Customer360
- exact TASK-005 equality

T6-06 History
- source facts only
- technical/business boundary preserved

T6-07 Cashflow
- TASK-005 missing semantics preserved

T6-08 Policy
- immutable TASK-002 facts

T6-09 Recovery
- immutable TASK-003/004 facts

T6-10 Cross-tool
- 0 shared-field mismatches

T6-11 Golden
- G01/G02/G04/G07/G08/G19/G20 PASS

T6-12 Provenance
- synthetic labels preserved

T6-13 Safety
- no mutation
- no arbitrary execution/path/network input

T6-14 No future decisions
- forbidden fields = 0

T6-15 Determinism
- artifact hashes identical

T6-16 Regression
- TASK-001?005 pass

T6-17 Scope
- no Agent/MaaS/deploy/ML/frontend/AEV

---

# 59. FRESH PIPELINE

Use fresh /tmp.

Run:

python -m compileall -q src tests

TASK-001 generator + validator + tests
TASK-002 validator + tests
TASK-003 CLI + validator + tests
TASK-004 CLI + validator + tests
TASK-005 CLI + validator + tests

TASK-006 tests

full unittest discovery

TASK-006 validator

Generate tool artifacts twice:

/tmp/msb-task006-tools-a
/tmp/msb-task006-tools-b

Compare SHA-256.

Hash source artifacts before and after.

---

# 60. GIT RULE

Do NOT commit TASK-006 implementation.

At completion:

git status --short
git diff --stat
git diff --check
git diff -- docs/spec-v1

Implementation remains uncommitted until independent audit ACCEPT.

---

# 61. REQUIRED FINAL REPORT

Return:

# TASK-006 RESULT

PASS
or
FAIL

## BASELINE

HEAD:
Working tree before:
Spec drift:

## PRECHECK

GreenNode skills:
Adapter decision:
Blockers:

## FILES

Created:
Modified:
Generated:
docs/spec-v1 modified:
Commit created:

## TOOL REGISTRY

Count:
Names:

## PORTFOLIO TOOL

Pagination:
Filters:
Ordering:
Provenance:

## CUSTOMER 360 TOOL

Equality mismatches:
Unknown CIF:

## HISTORY TOOL

Ordering:
Technical/business boundary:
Event types:

## CASHFLOW TOOL

Missing semantics:
G01:
G02:

## POLICY TOOL

Mutation mismatches:
G07:
G08:

## RECOVERY TOOL

Score mismatches:
Rank mismatches:
G01:
G02:

## CROSS-TOOL CONSISTENCY

Mismatch count:

## G04

Facts:
Forbidden treatment generated:

## G19

Technical Success:
PTP:
Willingness:
Boundary:

## G20

Loan count:
Outstanding:
MAX DPD:

## INPUT VALIDATION

Invalid cases tested:
Failures:

## SECURITY

Arbitrary path:
Shell:
eval/exec:
caller URL/network:
mutation:

## FORBIDDEN DECISION AUDIT

Treatment:
Recommended channel:
Recommended when:
Probability:
Expected recovery:
AI reasoning:
AEV/ROI:

## GREENNODE BOUNDARY

MaaS called:
Agent created:
AgentBase deployed:
Credentials required for tests:

All must be NO.

## ARTIFACTS

tool_schemas:
registry_manifest:
golden_validation:

## DETERMINISM

List A/B SHA-256.

## SOURCE MUTATION

Before:
After:
Result:

## TESTS

TASK-001:
TASK-002:
TASK-003:
TASK-004:
TASK-005:
TASK-006:
Full suite:

## SPEC DEVIATIONS

NONE
or details.

## ASSUMPTIONS

NONE
or authorized technical assumptions.

## UNRESOLVED BUSINESS QUESTIONS

NONE
or exact blocker.

## REGRESSIONS

NONE
or details.

## GIT STATUS

git status --short:
git diff --check:
git diff -- docs/spec-v1:

## NEXT GATE

READY FOR TASK-006 INDEPENDENT AUDIT

or

NOT READY

Do not implement TASK-007.

STOP.

---

# 62. DEFINITION OF DONE

TASK-006 is DONE only when:

1. Exactly six collection tools exist.
2. Tool schemas are machine-readable and deterministic.
3. Portfolio Tool preserves accepted ranking.
4. Customer360 equals TASK-005.
5. History preserves technical/business distinction.
6. Cashflow preserves missing-vs-zero semantics.
7. Policy preserves TASK-002 exactly.
8. Recovery preserves TASK-003/004 exactly.
9. Cross-tool shared-field mismatch = 0.
10. G01/G02/G04/G07/G08/G19/G20 pass.
11. Every response is clearly synthetic.
12. No future decision is invented.
13. No source mutation occurs.
14. No GreenNode credentials are needed for deterministic tests.
15. No Agent/MaaS/deployment is implemented.
16. Full TASK-001?005 regression passes.
17. Independent TASK-006 audit ACCEPTS.
18. Commit occurs only after audit acceptance.

END OF TASK-006