# TASK-001 — SYNTHETIC DATA FOUNDATION

## ROLE

You are the implementation engineer for MSB Collection Decision Copilot.

Your job is to implement exactly this task from the locked specifications.

Do NOT redesign the product.
Do NOT invent collection business rules.
Do NOT change the architecture.
Do NOT implement future tasks.

---

## REQUIRED READING — BEFORE WRITING CODE

Read ALL of these files completely:

1. docs/spec-v1/PRODUCT_SPEC_V1.md
2. docs/spec-v1/RULE_BASE_V1.md
3. docs/spec-v1/SYNTHETIC_DATA_SPEC.md
4. docs/spec-v1/GOLDEN_SCENARIOS_V1.md
5. docs/spec-v1/SPEC_README.md
6. docs/spec-v1/UBUNTU_BUILD_HANDOFF.md

Treat them as the source of truth.

Priority when interpreting requirements:

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

If specifications conflict:
STOP.
Report the conflict.
Do NOT choose a rule yourself.

If a required business rule is missing:
mark it UNKNOWN and report it.
Do NOT invent it.

---

# TASK OBJECTIVE

Implement only:

TASK-001 — Synthetic Data Generator

Build the deterministic synthetic data foundation required by the locked V1 specifications.

This task DOES NOT implement:

- Recovery Opportunity scoring
- treatment decision engine
- Agent
- GreenNode integration
- AgentBase
- MaaS
- frontend
- AEV
- ML
- real MSB integrations

Do not implement those.

---

# REQUIRED DATA SCALE

Generate approximately:

- 3,000 synthetic CIF
- 4,500–5,500 loan accounts
- 50,000–80,000 cashflow transactions
- 10,000–15,000 payment events
- 5,000–8,000 call history events
- 2,000–3,000 operation/PTP events

The exact normal-population counts may vary deterministically by seed.

There MUST be exactly:

20 Golden Scenario CIFs

corresponding to:

G01 ? G20

from:

docs/spec-v1/GOLDEN_SCENARIOS_V1.md

G01–G05 must also be marked HERO.

---

# DETERMINISM

Default generator seed:

20260828

Running the generator twice with the same seed MUST produce logically identical datasets.

Do not use uncontrolled current timestamps or random values that make regression tests unstable.

A configurable reference/evaluation date may be used.

---

# REQUIRED ENTITIES

Implement the synthetic equivalents defined by SYNTHETIC_DATA_SPEC:

customer

loan_account

collection_assignment

cashflow_transaction

payment_event

operation_result

call_history

golden_scenario_expected

generation_manifest

Use appropriate normalized relationships and foreign keys.

Do not add business entities unless technically required.

If technical metadata is required, keep it minimal and document it.

---

# CRITICAL BUSINESS CONTRACTS

These MUST be represented correctly.

## CIF debt aggregation

A CIF may contain multiple loan accounts.

total_outstanding_cif =
SUM(outstanding_amount of the CIF)

max_dpd_cif =
MAX(dpd of the CIF)

Do NOT calculate or implement Recovery Opportunity Score in TASK-001.

---

## Routing source data

Synthetic records must contain enough data for the later rule engine to evaluate:

Heatmap

Segment

DPD

challenge_override_route

Do NOT invent the actual MSB challenge-set algorithm.

challenge_override_route is an explicit synthetic input only.

---

## PTP

Support source data necessary to derive:

OPEN
KEPT
PARTIAL
BROKEN

Important:

actual_paid_amount >= promised_amount
can support KEPT

0 < actual_paid_amount < promised_amount
must support PARTIAL

actual_paid_amount = 0 after promise date + configured grace period
must support BROKEN

Do not silently hard-code a real MSB grace policy.

The demo default may be configuration value 1 day as defined by RULE_BASE_V1.

---

## PTP ABILITY

payment_ptp_ability:

CERTAIN
HIGH
MEDIUM
LOW
VERY_LOW

This is an employee assessment signal.

Do not treat it as objective truth.

---

## CALL HISTORY VS OPERATION RESULT

This distinction is mandatory.

call_history.status
=
technical call status

Examples:
Success
Error SIP

operation_result.operation_result
=
business operation outcome

Examples:

UTC
PTP
NPTP
RTP
NIN
THIRT
NA

Never merge these concepts.

---

# SYNTHETIC CASHFLOW

Generate transaction-level cashflow.

Required fields include:

cif
transaction_date
direction
amount
source_type

source_type prototype values:

SALARY
BUSINESS_INCOME
TRANSFER
DEPOSIT
OTHER

Data must support later derivation of:

inflow_3d
inflow_7d
inflow_30d
outflow_30d
net_cashflow_30d
recent_large_inflow
salary_like_income
income_stability_90d
liquidity_to_due_ratio

Do NOT calculate Recovery Opportunity Score.

---

# CORRELATED DATA

Do NOT generate every column independently at random.

Implement reproducible archetypes/correlations.

Examples:

stable salary profile
? periodic salary-like inflows

strong cashflow
? supports high ability-to-pay evidence
? does NOT automatically imply willingness

BROKEN PTP
? promise passes without sufficient payment

PARTIAL PTP
? payment > 0 but below promise

KEPT PTP
? payment >= promise

high contactability
? more successful calls in consistent time windows

NIN
? do not create subsequent successful calls on the same invalid number unless a new phone is introduced

self-cure archetype
? historical low-DPD episodes followed by payment

These are synthetic scenario relationships, not claims about MSB population distribution.

---

# GOLDEN SCENARIOS

Implement all 20 scenarios from:

docs/spec-v1/GOLDEN_SCENARIOS_V1.md

Each scenario must have stable:

scenario_id

cif

hero flag

input fixture

expected metadata

must_trigger_rule_ids

must_not_trigger_rule_ids

rationale

TASK-001 is responsible for generating the INPUT DATA and EXPECTED FIXTURE.

Do NOT implement the future decision engine just to force expected outputs.

---

# HERO SCENARIOS

Pay special attention to:

G01
High debt/high DPD but weak recovery opportunity signals

G02
Moderate debt + recent inflow + PTP due

G03
CALL-route input conditions + self-cure evidence

G04
Broken PTP + recent inflow

G05
What-if base customer fixture

These must be easy to identify and inspect manually.

---

# PRIVACY

All data MUST be synthetic.

Do NOT use:

real MSB customer data
real CIF
real phone numbers
real addresses
real call recordings
production dumps
external customer datasets

Synthetic identifiers should be obvious, for example:

SYN000001

Golden scenarios may use:

GOLDEN_G01
...
GOLDEN_G20

Do not create real-looking recording URLs.

---

# REQUIRED OUTPUTS

Create a clear project structure.

Choose the simplest maintainable structure appropriate for the existing repository.

At minimum provide:

1. synthetic data generator
2. database schema/migrations
3. deterministic seed configuration
4. golden scenario fixtures
5. generation_manifest.json
6. validation command
7. automated tests
8. README explaining generation and validation

Do NOT introduce:

Kafka
Kubernetes
microservices
distributed processing
unnecessary infrastructure

---

# DATABASE

Use PostgreSQL-compatible schema.

The design must remain easy to run locally through Docker Compose if the repository does not already provide PostgreSQL.

Do not introduce another database unless the existing repository already requires it.

---

# VALIDATION REQUIREMENTS

The validation suite MUST verify at least:

1. exactly 3,000 CIF unless configuration explicitly changes population size

2. exactly 20 Golden Scenario CIFs

3. G01–G05 are HERO

4. every loan_account references an existing CIF

5. every cashflow transaction references an existing CIF

6. every payment references an existing CIF

7. every call_history references an existing CIF

8. every operation_result references an existing CIF

9. multi-loan aggregation fixture G20 produces:

total_outstanding = 400,000,000 VND
max_dpd = 12

10. G09 supports PTP KEPT

11. G10 supports:

promise = 20,000,000
actual paid = 10,000,000

and therefore expected fixture = PARTIAL

12. G11 supports BROKEN PTP input

13. G12 supports OPEN PTP input

14. G13 contains NIN evidence

15. G14 contains NA + next_action_date

16. G15 contains repeated UTC evidence

17. G19 contains:

call_history.status = Success

but MUST NOT contain a PTP business outcome merely because technical status is Success

18. monetary values are valid

19. foreign-key integrity passes

20. same seed produces deterministic Golden fixtures

---

# MANIFEST

generation_manifest.json must include at least:

seed
reference_date
generator_version
generated_at
is_synthetic
counts
golden_scenario_count
hero_scenario_count

generated_at may vary and MUST NOT be used for deterministic dataset comparison.

is_synthetic MUST be true.

---

# TESTING

Run all tests yourself.

Do not report PASS without executing them.

If PostgreSQL is required for integration tests, start it using the project's supported local/Docker workflow.

Do not modify the specification files to make tests pass.

---

# TASK BOUNDARY

STOP after TASK-001.

Do NOT start:

TASK-002 Policy Engine

even if TASK-001 passes.

---

# REQUIRED FINAL REPORT

When implementation is complete, return:

## TASK-001 RESULT

PASS
or
FAIL

## FILES CREATED / MODIFIED

List all files.

## DATA COUNTS

customers
loans
cashflow
payments
calls
operations
golden scenarios

## TEST RESULTS

Show commands executed and results.

## GOLDEN VALIDATION

Report G01–G20 fixture validation.

## SPEC DEVIATIONS

NONE

or list every deviation.

## ASSUMPTIONS

List any technical assumptions.

Do not hide assumptions.

## UNRESOLVED QUESTIONS

List anything requiring business clarification.

## NEXT GATE

Explicitly state:

READY FOR TASK-002

or

NOT READY FOR TASK-002

Do not implement TASK-002.