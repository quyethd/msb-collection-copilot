# TASK-002 — DETERMINISTIC POLICY / RULE ENGINE

## ROLE

You are the implementation engineer for MSB Collection Decision Copilot.

TASK-001 — Synthetic Data Foundation has been ACCEPTED.

Your job is to implement exactly:

TASK-002 — Deterministic Policy / Rule Engine

This is a business-critical deterministic layer.

You MUST implement the locked business rules exactly as specified.

You MUST NOT:
- redesign the product;
- invent business rules;
- modify rule thresholds;
- optimize business logic;
- reinterpret ambiguous rules;
- implement scoring;
- let an LLM make policy decisions;
- implement future tasks.

If a required business rule is missing or conflicting:
STOP and report it.

Do not guess.

---

# REQUIRED READING — BEFORE WRITING CODE

Read ALL of these files completely:

1. docs/spec-v1/PRODUCT_SPEC_V1.md
2. docs/spec-v1/RULE_BASE_V1.md
3. docs/spec-v1/SYNTHETIC_DATA_SPEC.md
4. docs/spec-v1/GOLDEN_SCENARIOS_V1.md
5. docs/spec-v1/README.md
6. docs/spec-v1/UBUNTU_BUILD_HANDOFF.md
7. TASK-001.md
8. existing TASK-001 implementation
9. existing TASK-001 tests

Treat docs/spec-v1 as the locked business contract.

Do NOT modify any file under:

docs/spec-v1/

---

# SPEC PRIORITY

When interpreting business rules:

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

If two specifications conflict:

STOP.

Report:
- conflicting files;
- rule IDs;
- exact conflicting requirements.

Do NOT choose one yourself.

---

# TASK OBJECTIVE

Build a deterministic policy/rule engine that consumes the synthetic customer data created by TASK-001 and produces structured policy facts and routing decisions.

TASK-002 covers:

1. CIF-level aggregation
2. base routing
3. challenge-set override
4. PTP state derivation
5. explicit next-action facts
6. hard suppression where explicitly defined by the locked rules
7. deterministic rule trace
8. machine-readable policy result

The engine MUST be independently testable without:
- LLM
- GreenNode
- AgentBase
- frontend
- external API

---

# TASK BOUNDARY

TASK-002 MUST NOT implement:

- Recovery Opportunity Score
- Business Urgency score
- Ability-to-Pay score
- Willingness score
- Contactability score
- Timing score
- Strategic Adjustment score
- customer ranking by Recovery Opportunity
- Next Best Action optimization
- full treatment engine
- channel optimization
- best contact time optimization
- self-cure scoring/model
- machine learning
- GreenNode MaaS
- GreenNode AgentBase
- Agent tools
- What-if Agent
- frontend
- AEV
- real MSB integrations

Those belong to later tasks.

Do not implement them even if convenient.

---

# LOCKED PRECEDENCE

The overall V1 precedence from the specification is:

1. HARD POLICY
2. ROUTING CBS / CALL / OTHER
3. HARD SUPPRESSION
4. PTP / NEXT ACTION
5. RECOVERY OPPORTUNITY SCORE
6. TREATMENT
7. CHANNEL
8. WHEN
9. AGENT EXPLANATION

TASK-002 implements only the deterministic policy portion required before scoring.

The implementation MUST preserve rule precedence.

Do NOT allow later calculations to override earlier hard-policy decisions.

---

# REQUIRED RULE IDENTIFIERS

Use the exact rule IDs from RULE_BASE_V1.md wherever they are defined.

At minimum support the locked rules associated with:

AGG-001
AGG-002

BASE-001
BASE-002

ROUTE-001
ROUTE-002
ROUTE-003
ROUTE-004
ROUTE-005

PTP-001 through PTP-007

OUTCOME-001 through OUTCOME-003

and any explicit hard-suppression / next-action rule IDs that already exist in RULE_BASE_V1.md.

IMPORTANT:

Before implementation, enumerate the exact rule IDs discovered in RULE_BASE_V1.md.

Do not create a new BUSINESS rule ID just because implementation needs one.

Technical validation/test IDs may be created with a clearly technical prefix such as:

TEST-
TECH-

but they MUST NOT masquerade as business rules.

---

# CIF AGGREGATION

## AGG-001

For each CIF:

total_outstanding_cif =
SUM(outstanding_amount across all loan accounts belonging to the CIF)

Do not use:
- average;
- maximum;
- first account;
- one selected loan.

Use SUM.

---

## AGG-002

For each CIF:

max_dpd_cif =
MAX(dpd across all loan accounts belonging to the CIF)

A CIF may contain multiple products/accounts with different DPD.

Do not average DPD.

Do not use outstanding-weighted DPD.

Do not select DPD from the largest loan.

Use MAX.

---

# BASELINE FACTS

The engine must expose enough deterministic data for the future Baseline vs Copilot comparison.

The current baseline dimensions are:

total_outstanding_cif
max_dpd_cif

If BASE-002 specifies prototype deterministic sorting, implement it exactly as defined by RULE_BASE_V1:

total_outstanding_cif DESC
max_dpd_cif DESC
cif ASC

This is a benchmark ordering only.

It is NOT Recovery Opportunity ranking.

Keep these concepts separate.

---

# BASE ROUTING

Routing is hard policy.

Routing and future treatment are separate concepts.

Never mix them.

---

## ROUTE-001 — CALL

When:

heatmap = RED

AND

segment IN:
RED
ORANGE
YELLOW

AND

max_dpd_cif >= 5

then:

base_route = CALL

unless a higher-precedence explicit challenge override applies according to the locked specification.

---

## ROUTE-002 — CBS

When:

heatmap = RED

AND

segment IN:
RED
ORANGE
YELLOW

AND

max_dpd_cif < 5

then:

base_route = CBS

unless a higher-precedence explicit challenge override applies according to the locked specification.

---

## ROUTE-003 — CHALLENGE OVERRIDE

TASK-001 provides:

challenge_override_route

This is explicit synthetic input.

If the specification permits an explicit challenge-set override:

CALL ? CBS

or:

CBS ? CALL

apply it deterministically.

The result must preserve BOTH:

base_route
final_route

Example:

base_route = CALL
challenge_override_route = CBS
final_route = CBS

Do not overwrite or lose the original route.

---

## ROUTE-004

The real MSB challenge-set allocation algorithm is UNKNOWN.

Do NOT invent it.

TASK-002 may consume the explicit synthetic:

challenge_override_route

only.

Do not derive challenge assignment from:
- score;
- DPD;
- debt;
- cashflow;
- PTP;
- random logic.

---

## ROUTE-005

For CIFs outside the explicitly locked routing conditions, use the exact fallback defined by RULE_BASE_V1.

Do not invent an additional portfolio.

If the locked specification defines prototype OTHER/NONE behavior, implement that exact behavior and label it as prototype where appropriate.

---

# CRITICAL ROUTING INVARIANT

Future treatment MUST NOT change routing.

TASK-002 should make this impossible by design.

For example, later:

final_route = CALL

may coexist with:

treatment = WAIT_SELF_CURE

but TASK-002 does NOT implement WAIT_SELF_CURE treatment.

It only preserves final_route = CALL.

---

# PTP STATE DERIVATION

PTP state must be deterministic.

Do not use LLM interpretation.

Use source operation/payment facts.

Supported normalized states:

OPEN
KEPT
PARTIAL
BROKEN

Use exact locked PTP rules from RULE_BASE_V1.md.

---

## KEPT

When the applicable promise has:

actual_paid_amount >= promised_amount

derive:

ptp_status = KEPT

---

## PARTIAL

When:

actual_paid_amount > 0

AND:

actual_paid_amount < promised_amount

derive:

ptp_status = PARTIAL

Do NOT mark this KEPT.

---

## BROKEN

When:

actual_paid_amount = 0

AND:

promise date has passed beyond configured grace period

derive:

ptp_status = BROKEN

Use the configurable prototype grace period defined by the specification.

Current demo default:

1 day

Do not describe the one-day value as confirmed production MSB policy.

It is configuration.

---

## OPEN

A promise that has not yet met the conditions for:

KEPT
PARTIAL
BROKEN

and remains active according to the locked specification should derive:

OPEN

Do not mark a future promise BROKEN.

---

# PTP ABILITY

Preserve:

CERTAIN
HIGH
MEDIUM
LOW
VERY_LOW

as a human-assessed input signal.

TASK-002 MUST NOT convert payment_ptp_ability into:

- score;
- probability;
- truth label;
- routing decision.

That belongs to later reasoning/scoring.

---

# BUSINESS OUTCOME VS TECHNICAL CALL STATUS

This boundary is mandatory.

call_history.status

is technical call status.

Examples:

Success
Error SIP

operation_result.operation_result

is business operation outcome.

Examples:

UTC
PTP
NPTP
RTP
NIN
THIRT
NA

Never derive:

PTP

from:

call_history.status = Success

Never derive willingness from technical call success.

Never copy technical status into business outcome.

---

# OUTCOME FACTS

Implement deterministic extraction/normalization required by the locked OUTCOME rules.

At minimum the engine must be able to expose evidence for business outcomes such as:

UTC
PTP
NPTP
RTP
NIN
THIRT
NA

Do not assign scoring weight.

Do not convert them into Recovery Opportunity Score.

---

# NEXT ACTION FACTS

If operation history contains:

next_action_date
next_operation_channel

preserve these as explicit deterministic facts.

Explicit source data must remain distinguishable from future AI recommendations.

Example:

source_next_action_date
source_next_operation_channel

are source facts.

They are NOT:

recommended_when
recommended_channel

TASK-002 must not confuse them.

---

# HARD SUPPRESSION

Implement ONLY hard-suppression rules that are explicitly defined in RULE_BASE_V1.md.

Do not create new suppressions.

Do not infer:

good cashflow ? suppress CALL

or:

self-cure ? suppress CALL

unless an exact locked hard rule says so.

Cashflow and self-cure belong to later scoring/treatment logic.

If no applicable hard suppression exists for a CIF:

hard_suppressed = false

Do not invent one.

---

# POLICY RESULT CONTRACT

Create a typed/structured result for each CIF.

Use the existing project language/style.

Conceptually the result must expose at least:

cif

total_outstanding_cif
max_dpd_cif

heatmap
segment

base_route
challenge_override_route
final_route

ptp_status
promise_date
promise_amount
actual_paid_amount
payment_ptp_ability

latest_business_outcome

source_next_action_date
source_next_operation_channel

hard_suppressed
hard_suppression_reason

triggered_rule_ids

policy_trace

The exact technical representation may be:
- dataclass;
- typed object;
- equivalent strongly structured model.

Do not add speculative business fields.

---

# POLICY TRACE

Every policy decision must be explainable without an LLM.

The engine must return a deterministic trace.

Example shape:

[
  {
    "rule_id": "AGG-001",
    "result": "MATCH",
    "evidence": {
      "loan_count": 3,
      "total_outstanding_cif": 400000000
    }
  },
  {
    "rule_id": "AGG-002",
    "result": "MATCH",
    "evidence": {
      "max_dpd_cif": 12
    }
  },
  {
    "rule_id": "ROUTE-001",
    "result": "MATCH",
    "evidence": {
      "heatmap": "RED",
      "segment": "ORANGE",
      "max_dpd_cif": 12
    }
  }
]

The exact serialization may vary.

But it MUST contain:

rule_id
result
evidence

Evidence must come from actual structured input.

Do not generate prose explanations with an LLM.

---

# ENGINE DESIGN

Prefer pure deterministic functions.

Business rules should be testable without PostgreSQL where practical.

Database/storage access should be separated from rule evaluation.

Preferred conceptual separation:

data loading
    ?
normalization / aggregation
    ?
policy evaluation
    ?
structured PolicyResult

Avoid hiding business logic inside SQL if doing so makes Golden Scenario testing difficult.

SQL aggregation is acceptable where appropriate, but the rules must remain clearly testable and traceable.

---

# GOLDEN SCENARIOS

TASK-002 MUST evaluate all 20 Golden Scenario CIFs.

Use:

docs/spec-v1/GOLDEN_SCENARIOS_V1.md

and the generated fixtures from TASK-001.

Do not modify Golden inputs to make the engine pass.

---

# CRITICAL GOLDEN ASSERTIONS

At minimum verify the following.

## G06

Must exercise the CBS routing condition defined by the Golden Scenario specification.

Expected routing must match the locked scenario.

---

## G07

Must prove challenge override:

CBS ? CALL

Preserve:

base_route = CBS
final_route = CALL

---

## G08

Must prove challenge override:

CALL ? CBS

Preserve:

base_route = CALL
final_route = CBS

---

## G09

PTP must derive:

KEPT

---

## G10

Given:

promise_amount = 20,000,000

actual_paid_amount = 10,000,000

derive:

PARTIAL

---

## G11

Must derive:

BROKEN

according to reference date + configured grace period.

---

## G12

Must derive:

OPEN

---

## G13

Must preserve:

NIN

as business operation evidence.

Do not interpret technical Success as overriding NIN.

---

## G14

Must preserve:

NA

and explicit:

next_action_date

with source provenance.

---

## G15

Must expose repeated:

UTC

evidence.

Do NOT reduce willingness score because TASK-002 has no score.

---

## G19

Must prove:

call_history.status = Success

does NOT imply:

operation_result = PTP

This distinction must have an automated test.

---

## G20

Must calculate from actual loan rows:

total_outstanding_cif = 400,000,000

max_dpd_cif = 12

Do not read those actual values from expected fixture as the calculation source.

---

# ROUTING GOLDEN TESTS

Automated tests must explicitly verify:

CALL base routing

CBS base routing

OTHER/NONE fallback if defined by locked specification

challenge CBS ? CALL

challenge CALL ? CBS

No score or cashflow field may alter routing.

Include at least one test demonstrating that changing cashflow while keeping routing inputs identical does NOT change final_route.

---

# PTP GOLDEN TESTS

Automated tests must explicitly verify:

KEPT
PARTIAL
BROKEN
OPEN

Boundary cases must include:

actual_paid_amount == promised_amount
actual_paid_amount > promised_amount
0 < actual_paid_amount < promised_amount
actual_paid_amount = 0 before due/grace expiry
actual_paid_amount = 0 after grace expiry

Use configured reference date.

Do not use system current time for deterministic tests.

---

# DETERMINISM

Policy evaluation MUST be deterministic.

Same input
+
same configuration
+
same reference date

must produce identical:

aggregations
routing
PTP state
hard suppression
triggered rules
policy trace

Do not depend on:

system clock
unordered set iteration
random values
LLM
network API

---

# CONFIGURATION

Business/prototype configuration must be explicit.

At minimum expose configurable values required by the locked rules, such as:

PTP grace period

Do not scatter business thresholds as unexplained magic numbers.

However:

do NOT turn locked routing thresholds into arbitrary runtime behavior that silently changes the business contract.

Configuration must have documented defaults.

---

# DATABASE / INPUT

TASK-002 must consume TASK-001 generated data.

Do not create a second incompatible synthetic model.

Do not duplicate the entire generator.

Reuse existing schemas and generated artifacts.

The engine should be able to run against a generated TASK-001 dataset.

---

# CLI / VALIDATION

Provide a simple deterministic command to evaluate policy results.

For example conceptually:

PYTHONPATH=src python -m <module> \
  --input build/synthetic-data \
  --output build/policy-results

Exact module naming is your technical choice.

Provide another validation/test command.

The output should allow inspection of Golden Scenario results.

Prefer machine-readable output such as:

policy_result.csv
or
policy_result.jsonl

and optionally:

golden_policy_validation.json

Do not generate large unnecessary artifacts.

Generated outputs should remain git-ignored when reproducible.

---

# TEST REQUIREMENTS

Add meaningful automated tests.

Do not create tests that simply assert expected fixture fields against themselves.

Tests must execute actual rule-engine functions.

At minimum test:

1. AGG-001 SUM
2. AGG-002 MAX
3. CALL route
4. CBS route
5. fallback route
6. CBS ? CALL challenge override
7. CALL ? CBS challenge override
8. KEPT PTP
9. PARTIAL PTP
10. BROKEN PTP
11. OPEN PTP
12. PTP exact-payment boundary
13. PTP overpayment boundary
14. source next_action preservation
15. NIN preservation
16. UTC evidence
17. technical Success != PTP
18. G20 actual aggregation
19. routing unaffected by cashflow
20. deterministic policy trace

Run the complete TASK-001 test suite too.

TASK-002 must not break TASK-001.

---

# REQUIRED VALIDATION GATES

TASK-002 may report PASS only when:

- TASK-001 tests still PASS
- TASK-002 tests PASS
- all 20 Golden Scenario inputs can be evaluated
- all applicable Golden policy expectations PASS
- G07 preserves CBS ? CALL override
- G08 preserves CALL ? CBS override
- G09 = KEPT
- G10 = PARTIAL
- G11 = BROKEN
- G12 = OPEN
- G19 technical Success is not interpreted as PTP
- G20 = 400M / MAX DPD 12
- zero hard-policy violations
- no docs/spec-v1 files modified
- no Recovery Opportunity scoring implemented
- no GreenNode/LLM dependency introduced

---

# SECURITY / PRIVACY

Continue using synthetic data only.

Do not introduce:
- real MSB data;
- production credentials;
- real phone numbers;
- real recordings;
- API secrets.

Do not commit:
.env
credentials
GreenNode secrets
API keys

---

# EXISTING CODE

Preserve accepted TASK-001 behavior.

Do not refactor TASK-001 broadly unless technically necessary.

If a TASK-001 defect is discovered:

STOP.

Report:

TASK-001 REGRESSION / DEFECT FOUND

with:
- file;
- scenario;
- expected;
- actual;
- proposed fix.

Do NOT silently rewrite accepted TASK-001 behavior.

---

# GIT DISCIPLINE

Do NOT commit automatically unless explicitly instructed.

At the beginning record:

git status
git log --oneline -5

Expected baseline includes:

9695f12 Lock Collection Decision Copilot V1 specs
a206967 TASK-001 pass synthetic data foundation

The working tree should be clean before implementation.

At completion show:

git status --short
git diff --stat
git diff -- docs/spec-v1

The last command should show no specification changes.

---

# STOP CONDITIONS

STOP implementation and report FAIL if:

1. locked specs conflict;
2. required business rule is undefined and implementation requires guessing;
3. TASK-001 data cannot represent a required rule;
4. implementing the requirement would require changing accepted Golden Scenario inputs;
5. TASK-001 regression is discovered;
6. a real MSB rule is required but only an assumption exists.

Do not solve these by inventing logic.

---

# REQUIRED FINAL REPORT

Return exactly this structure:

# TASK-002 RESULT

PASS
or
FAIL

## BASELINE

Git commit before implementation:
Working tree before implementation:

## FILES CREATED / MODIFIED

List every file.

Explicitly state whether any file under docs/spec-v1 was modified.

## RULES IMPLEMENTED

For every implemented business rule:

RULE_ID
status
implementation location
test location

Do not list rules that were not actually implemented.

## POLICY PIPELINE

Show the implemented deterministic precedence.

## GOLDEN RESULTS

Report:

G01: PASS / NOT_APPLICABLE / FAIL
...
G20: PASS / NOT_APPLICABLE / FAIL

For each applicable routing/PTP Golden Scenario include:

base_route
challenge_override_route
final_route
ptp_status
hard_suppressed
triggered_rule_ids

## CRITICAL ASSERTIONS

G07 CBS ? CALL:
G08 CALL ? CBS:
G09 KEPT:
G10 PARTIAL:
G11 BROKEN:
G12 OPEN:
G19 Success != PTP:
G20 400M / MAX DPD 12:

## TEST RESULTS

List every command actually executed.

Include:
TASK-001 regression tests
TASK-002 unit tests
TASK-002 validation

Do not claim tests that were not executed.

## POLICY OUTPUT

State generated artifact path and record count.

## SPEC DEVIATIONS

NONE

or list every deviation.

## ASSUMPTIONS

List technical assumptions only.

Do not hide business assumptions here.

## UNRESOLVED BUSINESS QUESTIONS

NONE

or list them.

## TASK-001 REGRESSIONS

NONE

or list them.

## OUT-OF-SCOPE CONFIRMATION

Explicitly confirm that TASK-002 did NOT implement:

Recovery Opportunity Score
Treatment optimization
Channel optimization
Best-time optimization
ML
GreenNode
AgentBase
Frontend
AEV

## GIT STATUS

Show:

git status --short
git diff --stat
git diff -- docs/spec-v1

## NEXT GATE

Return exactly one:

READY FOR TASK-003 REVIEW

or

NOT READY FOR TASK-003

STOP.

Do not implement TASK-003.