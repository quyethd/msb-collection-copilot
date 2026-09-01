# TASK-005 — DECISION CONTEXT / CUSTOMER 360 ASSEMBLY

## STATUS

AUTHORIZED AFTER TASK-004 ACCEPTANCE

TASK-001 = ACCEPTED
TASK-002 = ACCEPTED
TASK-003 = ACCEPTED
TASK-004 = ACCEPTED

TASK-005 must not begin unless:

- TASK-004 independent audit = ACCEPT;
- TASK-004 implementation is committed;
- working tree is clean;
- docs/spec-v1 has no drift.

---

# 1. PURPOSE

Build the deterministic Decision Context layer for the Collection Decision Copilot.

TASK-005 combines accepted outputs from:

TASK-001 Synthetic Data
TASK-002 Policy Engine
TASK-003 Recovery Opportunity Engine
TASK-004 Baseline vs Recovery Evaluation

into one stable, typed, machine-readable Customer 360 / Decision Context per CIF.

The output will become the authoritative read contract for:

- future GreenNode tools;
- future Collection Decision Agent;
- future Customer 360 UI;
- future Priority Queue UI;
- future What-if simulator input.

TASK-005 itself must NOT make a new collection decision.

---

# 2. PRODUCT ROLE

Today information about a CIF is distributed across:

- customer;
- loan accounts;
- collection routing;
- DPD;
- outstanding balance;
- cashflow;
- payments;
- PTP;
- operation history;
- call history;
- Recovery Opportunity score;
- baseline rank;
- Recovery rank;
- ranking movement.

TASK-005 creates one deterministic object answering:

WHO is this customer?

WHAT is their current debt state?

WHAT is the current policy/routing state?

WHAT payment/cashflow/PTP/contact evidence exists?

HOW does Baseline prioritize them?

HOW does Recovery Opportunity prioritize them?

WHAT structured evidence supports the Recovery score?

TASK-005 does NOT answer:

WHAT treatment should be performed?
WHICH channel should be used?
WHEN should the collector contact?
WHAT will the customer do?
WHAT is the expected recovery?

Those belong to later tasks.

---

# 3. REQUIRED READING

Before writing ANY implementation code, read completely:

1. docs/spec-v1/PRODUCT_SPEC_V1.md
2. docs/spec-v1/RULE_BASE_V1.md
3. docs/spec-v1/SYNTHETIC_DATA_SPEC.md
4. docs/spec-v1/GOLDEN_SCENARIOS_V1.md
5. docs/spec-v1/README.md
6. docs/spec-v1/UBUNTU_BUILD_HANDOFF.md
7. TASK-001.md
8. TASK-002.md
9. TASK-003.md
10. TASK-003_SCORING_CONTRACT.md
11. TASK-004.md
12. accepted TASK-001 implementation and tests
13. accepted TASK-002 implementation and tests
14. accepted TASK-003 implementation and tests
15. accepted TASK-004 implementation and tests

Do not rely on previous conversation summaries.

Repository specifications are authoritative.

---

# 4. SPEC PRECEDENCE

Business/spec precedence:

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
TASK-003_SCORING_CONTRACT.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

TASK-004.md defines evaluation semantics.

TASK-005.md defines assembly/output semantics only.

TASK-005 MUST NOT redefine any accepted business rule.

---

# 5. HARD ANTI-INVENTION RULE

TASK-005 must not invent or infer:

- customer propensity;
- recovery probability;
- cure probability;
- willingness probability;
- ability probability;
- expected payment;
- expected recovery amount;
- treatment;
- channel;
- contact timing;
- collector action;
- collection strategy;
- risk classification;
- customer segment beyond source values;
- business reason not supported by accepted evidence;
- AI explanation;
- confidence score;
- model prediction;
- AEV;
- ROI.

If a required output cannot be sourced from accepted data or accepted derived results:

represent it as:

null
[]
MISSING

according to field type.

Do NOT fill gaps using assumptions.

---

# 6. SCOPE

TASK-005 implements only:

Accepted source data
        +
Accepted PolicyResult
        +
Accepted RecoveryResult
        +
Accepted EvaluationResult
        ?
Decision Context Assembly
        ?
Customer 360 artifacts
        ?
Portfolio index artifact

Allowed:

- deterministic joins;
- deterministic aggregation already accepted;
- source-event ordering;
- accepted feature/result preservation;
- structured evidence references;
- data availability flags;
- customer/loan summaries;
- cashflow summaries already accepted by TASK-003;
- PTP context;
- call/contact context;
- baseline/recovery comparison;
- typed schemas;
- serialization;
- CLI;
- validator;
- tests.

Not allowed:

- new scoring;
- new ranking;
- routing changes;
- treatment;
- channel recommendation;
- best contact time recommendation;
- queue optimization;
- GreenNode;
- AgentBase;
- LLM;
- ML;
- frontend;
- REST API/server;
- What-if mutation;
- AEV;
- ROI.

---

# 7. AUTHORITATIVE DATA BOUNDARY

TASK-005 MUST distinguish three data categories:

## SOURCE FACT

Raw synthetic source data.

Examples:

customer fields
loan rows
cashflow transactions
payment events
call events
operation_result events

## ACCEPTED DERIVED FACT

Calculated by accepted deterministic engines.

Examples:

total_outstanding_cif
max_dpd_cif
PTP state
cashflow features
Recovery Opportunity components
baseline_rank
recovery_rank
rank_delta

## FUTURE DECISION

Not available in TASK-005.

Examples:

treatment
recommended_channel
recommended_when
objective
agent explanation
next-best-action

Future decision fields MUST NOT appear with invented values.

Rule:

CTX-BOUNDARY-001

---

# 8. REQUIRED CUSTOMER CONTEXT OBJECT

Create one Decision Context per CIF.

Suggested top-level structure:

{
  "context_version": "...",
  "cif": "...",
  "as_of_date": "...",

  "customer": {...},

  "debt": {...},

  "policy": {...},

  "cashflow": {...},

  "payment": {...},

  "ptp": {...},

  "contact": {...},

  "recovery_opportunity": {...},

  "ranking": {...},

  "evidence": {...},

  "availability": {...},

  "provenance": {...}
}

Exact serialization may vary slightly if implementation language requires it.

Meaning must remain equivalent.

Rule:

CTX-OBJECT-001

---

# 9. CONTEXT VERSION

Every context object must contain:

context_version

Default:

"1.0"

This is a technical schema version.

It is NOT a business version.

Rule:

CTX-VERSION-001

---

# 10. AS-OF DATE

Every context must contain:

as_of_date

Use the accepted deterministic reference date from the synthetic manifest.

Default current V1 dataset:

2026-08-28

Do NOT use:

date.today()
datetime.now()
system clock

Rule:

CTX-DATE-001

---

# 11. CUSTOMER SECTION

The customer section may contain only fields present in the accepted synthetic customer source.

At minimum:

cif

plus existing customer attributes if defined by TASK-001 source schema.

Do not infer demographics.

Do not generate missing data.

Rule:

CTX-CUSTOMER-001

---

# 12. DEBT SECTION

Required fields:

total_outstanding_cif
max_dpd_cif
loan_count
loans

Each loan entry must preserve accepted source facts such as:

loan/account identifier
outstanding_amount
dpd

plus any other actual TASK-001 loan fields.

Required consistency:

total_outstanding_cif
=
SUM(current loan outstanding)

max_dpd_cif
=
MAX(current loan DPD)

The accepted TASK-002 values remain authoritative.

TASK-005 may independently verify them.

Rule:

CTX-DEBT-001

---

# 13. POLICY SECTION

Required:

base_route
challenge_override_route
final_route
hard_suppressed

Also include accepted source-next-action facts if already available from TASK-002.

Example:

source_next_action_date
source_next_operation_channel

Do not rename a source next action as an AI recommendation.

Required distinction:

source_next_action_date
!=
recommended_when

The latter does not exist in TASK-005.

Rule:

CTX-POLICY-001

---

# 14. CASHFLOW SECTION

TASK-005 must expose accepted TASK-003 cashflow-derived facts.

At minimum where available:

inflow_3d
inflow_7d
inflow_30d
outflow_30d
net_cashflow_30d
income-source evidence
cashflow stability evidence
liquidity_to_due_ratio

Use exactly the semantics accepted by TASK-003.

TASK-005 must NOT reimplement different cashflow formulas.

If exposing recent transactions, they must come from source rows.

Recommended:

recent_transactions

limited deterministically to the latest 10 transactions by:

transaction_date DESC
then stable source identifier ASC/DESC as appropriate for deterministic ordering.

If a stable source identifier exists, use it.

If no safe deterministic tie-break exists:

STOP and report the missing technical ordering contract rather than inventing business meaning.

Transaction preview is descriptive only.

Rule:

CTX-CASHFLOW-001

---

# 15. PAYMENT SECTION

Required where available:

payment_available
recent_payment_count

Optional deterministic preview:

recent_payments

using source payment records.

Do not create:

payment_probability
future_payment_amount
expected_payment

Rule:

CTX-PAYMENT-001

---

# 16. PTP SECTION

Expose the accepted selected/applicable PTP context from TASK-002/TASK-003.

Where available:

promise_date
promise_amount
actual_paid_amount
status
employee_assessed_ability
fulfillment_ratio_raw if TASK-003 exposes it
next_action_date
next_operation_channel

Important:

employee_assessed_ability is a HUMAN assessment.

It must not be renamed:

probability
confidence
model_score

Rule:

CTX-PTP-001

Technical distinction:

TASK-002 capped fulfillment representation, if present,
must not silently replace TASK-003 raw scoring evidence.

If both are exposed, name them distinctly.

Example:

policy_fulfillment_ratio
scoring_fulfillment_ratio_raw

Rule:

CTX-PTP-002

---

# 17. CONTACT SECTION

Expose accepted source/derived contact facts.

At minimum where available:

call_history_available
operation_history_available
outbound_attempts_30d
successful_outbound_calls_30d
technical_success_rate_30d
utc_count_30d
latest_successful_outbound_date

Optional:

recent_calls
recent_operation_results

For call records:

technical status must remain technical.

Example:

call_history.status = Success

must NOT become:

payment_success
PTP
recovery_success

Rule:

CTX-CONTACT-001

---

# 18. RECENT EVENT PREVIEW LIMIT

To keep future UI/tool payloads bounded:

Default V1 preview limit:

10

for each source-event family:

recent_cashflow_transactions
recent_payments
recent_calls
recent_operation_results

This is:

[TECHNICAL-CONFIG]

not business policy.

Full source datasets remain elsewhere.

The limit must be configurable.

Rule:

CTX-PREVIEW-001

---

# 19. EVENT ORDERING

Recent-event previews must be deterministic.

Primary:

event timestamp/date DESC

Secondary:

stable source ID ASC unless source ordering contract already defines otherwise.

Document the actual deterministic ordering in code/tests.

Do not use random ordering.

Rule:

CTX-ORDER-001

---

# 20. RECOVERY OPPORTUNITY SECTION

Required:

recovery_opportunity_score

and six accepted components:

business_urgency_score
ability_to_pay_score
willingness_to_pay_score
contactability_score
timing_opportunity_score
strategic_adjustment_score

Also preserve:

score_trace
or equivalent structured evidence generated by TASK-003.

TASK-005 must not alter:

scores
rules
trace
thresholds

Rule:

CTX-RECOVERY-001

---

# 21. RANKING SECTION

Required:

baseline_rank
recovery_rank
rank_delta
absolute_rank_delta
normalized_rank_delta
movement

Also include accepted structured movement evidence:

primary_movement_factors

where available from TASK-004.

Rule:

CTX-RANKING-001

TASK-005 must not recompute different ranks.

---

# 22. BASELINE EVIDENCE

Preserve explicit baseline evidence:

total_outstanding_cif
max_dpd_cif

Do not invent another baseline reason.

Rule:

CTX-BASELINE-001

---

# 23. AVAILABILITY SECTION

Required:

cashflow_available
payment_available
ptp_available
call_history_available
operation_history_available

Use accepted TASK-003/source availability semantics.

Missing evidence must remain missing.

No imputation.

No negative interpretation.

Rule:

CTX-AVAILABILITY-001

---

# 24. EVIDENCE SECTION

Create structured evidence references.

This section should make future Agent explanation grounded and auditable.

Suggested shape:

evidence:
  baseline:
    - ...
  recovery:
    - ...
  ptp:
    - ...
  contact:
    - ...
  cashflow:
    - ...

Evidence must refer only to:

source facts
accepted rule IDs
accepted derived facts

No free-form AI narrative.

Rule:

CTX-EVIDENCE-001

---

# 25. PROVENANCE

Every context must include provenance.

Required minimum:

synthetic_data = true

reference_date

source_stage:

TASK-001

policy_stage:

TASK-002

recovery_stage:

TASK-003

evaluation_stage:

TASK-004

context_stage:

TASK-005

Required label:

SYNTHETIC PROTOTYPE DATA

Rule:

CTX-PROVENANCE-001

This must prevent future UI/Agent from accidentally presenting the data as real MSB customer data.

---

# 26. NO PII CLAIM

All TASK-005 data are synthetic prototype data.

Do not add:

real MSB identifiers
real phone numbers
real names
real customer data
real recordings

Rule:

CTX-PRIVACY-001

---

# 27. PORTFOLIO INDEX

Generate a lightweight portfolio context index.

One row per CIF.

Required fields:

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

availability summary

This will support future Portfolio Tool/UI without loading full Customer 360 objects.

Rule:

CTX-INDEX-001

---

# 28. SORT ORDER OF PORTFOLIO INDEX

Default serialization order:

recovery_rank ASC

because TASK-005 is exposing the accepted Recovery ranking.

This is presentation/storage ordering only.

It must not create or change ranking.

Rule:

CTX-INDEX-ORDER-001

---

# 29. CUSTOMER CONTEXT LOOKUP

Provide deterministic library/API-function-level lookup by CIF.

Example conceptual API:

get_customer_context(cif)

No HTTP server required.

If CIF does not exist:

return explicit NOT_FOUND result
or raise a typed domain lookup error.

Do not silently return empty context.

Rule:

CTX-LOOKUP-001

---

# 30. NO ACTIONABLE DECISION

TASK-005 output must NOT contain fields such as:

treatment
recommended_treatment
next_best_action
recommended_channel
recommended_when
best_contact_time
objective
agent_decision
action_priority
expected_recovery

unless the field is clearly a SOURCE FACT with an unambiguous source-specific name.

For example:

source_next_operation_channel

is allowed.

recommended_channel

is forbidden.

Rule:

CTX-NO-ACTION-001

Hard acceptance gate.

---

# 31. NO NATURAL-LANGUAGE AI EXPLANATION

TASK-005 does not generate AI narratives.

Do not generate fields like:

ai_explanation
why_ai_selected
reasoning_text
agent_reasoning

Structured accepted evidence is sufficient.

Rule:

CTX-NO-AI-TEXT-001

---

# 32. NO SCORE OR RANK CHANGE

TASK-005 must preserve all accepted TASK-003 values exactly:

recovery_opportunity_score
six component scores
baseline_rank
recovery_rank

and TASK-004 values:

rank_delta
absolute_rank_delta
normalized_rank_delta
movement

Mismatch count must be:

0

Rule:

CTX-IMMUTABILITY-001

---

# 33. POLICY IMMUTABILITY

TASK-005 must preserve exactly:

base_route
challenge_override_route
final_route
hard_suppressed
total_outstanding_cif
max_dpd_cif

Mismatch count:

0

Rule:

CTX-POLICY-IMMUTABILITY-001

---

# 34. G01 CUSTOMER CONTEXT

G01 must demonstrate:

baseline_rank = accepted TASK-004 value
recovery_rank = accepted TASK-004 value
movement = DEMOTED
final_route preserved
Recovery score/components preserved
source evidence preserved

TASK-005 must not hardcode its values.

Rule:

CTX-G01-001

---

# 35. G02 CUSTOMER CONTEXT

G02 must demonstrate:

baseline_rank = accepted value
recovery_rank = accepted value
movement = PROMOTED
recent cashflow evidence preserved
PTP evidence preserved
contactability evidence preserved
Recovery score/components preserved
route preserved

No hardcoded G02 scoring behavior.

Rule:

CTX-G02-001

---

# 36. G04 CUSTOMER CONTEXT

G04 should explicitly validate that TASK-005 can assemble:

BROKEN PTP
recent inflow
successful contact evidence
Recovery Opportunity result

without turning those facts into a treatment recommendation.

Rule:

CTX-G04-001

---

# 37. G07 / G08

G07:

CBS ? CALL challenge override must remain preserved.

G08:

CALL ? CBS challenge override must remain preserved.

Rule:

CTX-ROUTE-GOLDEN-001

---

# 38. G19

G19 must prove:

technical Success remains technical contact evidence.

No PTP exists.

Willingness remains accepted TASK-003 value.

TASK-005 must not reinterpret Success as business success.

Rule:

CTX-G19-001

---

# 39. G20

G20 context must preserve:

loan_count = 3

loans:

100,000,000 DPD 4
250,000,000 DPD 12
50,000,000 DPD 7

total_outstanding_cif =
400,000,000

max_dpd_cif =
12

Rule:

CTX-G20-001

---

# 40. GOLDEN VALIDATION

Evaluate G01–G20 where TASK-005 has an explicit applicable assertion.

Allowed statuses:

PASS
FAIL
NOT_APPLICABLE

Never report unconditional PASS.

At minimum explicit TASK-005 assertions:

G01
G02
G04
G07
G08
G19
G20

Other Golden scenarios:

PASS only if an explicit TASK-005 assertion exists.

Otherwise:

NOT_APPLICABLE

Rule:

CTX-GOLDEN-001

---

# 41. DATA JOIN INTEGRITY

Every accepted portfolio CIF must result in exactly one Decision Context.

Required:

input CIF count = 3,000
output context count = 3,000
duplicate context CIF = 0
missing context CIF = 0
unexpected context CIF = 0

Rule:

CTX-JOIN-001

If an authoritative stage is missing a CIF:

FAIL.

Do not silently drop the CIF.

---

# 42. NULL / MISSING SEMANTICS

Use:

null

for unavailable scalar data.

Use:

[]

for available list-shaped output with no applicable rows or for a missing source family where schema requires an array, paired with the availability flag.

Use explicit availability flags.

Do not convert missing evidence to:

0
false
"NONE"

unless the accepted upstream semantic explicitly defines that value.

Rule:

CTX-MISSING-001

Important:

an accepted numeric feature of 0 is not automatically equivalent to missing evidence.

---

# 43. SERIALIZATION SAFETY

Money must remain integer VND or deterministic Decimal/string representation according to accepted upstream serialization.

Ratios must retain deterministic precision.

Do not introduce binary floating point into persisted financial values.

Rule:

CTX-NUMERIC-001

---

# 44. DETERMINISM

Same accepted inputs and config must produce byte-identical TASK-005 artifacts.

No:

randomness
network
LLM
system clock

Rule:

CTX-DETERMINISM-001

---

# 45. REQUIRED IMPLEMENTATION PACKAGE

Preferred:

src/msb_context/

Suggested modules:

__init__.py
models.py
assembler.py
io.py
cli.py
validate.py

Exact names may differ if repository style strongly favors another structure.

Keep implementation simple.

No framework.

No web server.

---

# 46. REQUIRED OUTPUT ARTIFACTS

Preferred:

build/decision-context/

Required:

customer_context.jsonl

Exactly:

3,000 records

portfolio_context_index.json

or:

portfolio_context_index.jsonl

Use whichever matches repository conventions, but document it.

golden_context_validation.json

context_manifest.json

---

# 47. CONTEXT MANIFEST

Required:

context_version
reference_date
synthetic_data
synthetic_label
customer_count
preview_limit
input stage identifiers
generated artifact names

Do not include nondeterministic current timestamp if artifact determinism would be broken.

If metadata needs generation timestamp:

it must be excluded from deterministic artifact comparison or omitted.

Prefer omission in TASK-005.

Rule:

CTX-MANIFEST-001

---

# 48. CLI

Preferred:

PYTHONPATH=src python -m msb_context.cli \
  --input build/synthetic-data \
  --output build/decision-context

CLI must build accepted upstream deterministic stages as required or consume their accepted outputs consistently.

No external services.

---

# 49. CUSTOMER LOOKUP CLI

Optional but recommended:

PYTHONPATH=src python -m msb_context.cli \
  --input build/synthetic-data \
  --output build/decision-context \
  --cif GOLDEN_G02

If implemented, it may print or write a single context.

It must use exactly the same assembler as batch generation.

No duplicated logic.

---

# 50. VALIDATOR

Preferred:

PYTHONPATH=src python -m msb_context.validate \
  --input build/synthetic-data \
  --output build/decision-context/golden_context_validation.json

Validator must independently verify important assembly invariants.

It must not merely trust context fields.

At minimum:

- 3,000 contexts;
- no duplicate/missing/unexpected CIF;
- authoritative TASK-002 fields;
- authoritative TASK-003 fields;
- authoritative TASK-004 fields;
- debt aggregation;
- event previews respect limit;
- deterministic event ordering;
- G01;
- G02;
- G04;
- G07;
- G08;
- G19;
- G20;
- synthetic provenance;
- forbidden action fields absent;
- forbidden probability/expected-recovery fields absent;
- no unconditional Golden PASS.

---

# 51. REQUIRED TESTS

TASK-005 tests must include at least:

1. one context per CIF
2. exactly 3,000 contexts
3. no duplicate CIF
4. missing authoritative-stage CIF fails
5. unexpected authoritative-stage CIF fails
6. context_version
7. deterministic as_of_date
8. debt SUM consistency
9. debt MAX DPD consistency
10. G20 loan-level aggregation
11. policy field immutability
12. TASK-003 score immutability
13. TASK-004 rank/movement immutability
14. cashflow availability vs actual zero distinction
15. PTP missing vs actual state distinction
16. employee PTP ability remains human assessment
17. technical Success does not become business success
18. event preview max 10
19. event ordering deterministic
20. portfolio index sorted by recovery_rank
21. portfolio index contains every CIF
22. lookup existing CIF
23. lookup unknown CIF returns typed not-found behavior
24. G01 context
25. G02 context
26. G04 context
27. G07 route
28. G08 route
29. G19 boundary
30. G20 aggregation
31. provenance synthetic label
32. no treatment field
33. no recommended channel
34. no recommended when
35. no probability field
36. no expected recovery field
37. no AI explanation
38. byte-deterministic artifact rerun
39. input source artifacts unchanged
40. Golden statuses truthful

Tests must inspect serialized output where applicable.

Do not rely only on in-memory objects.

---

# 52. ARTIFACT SCHEMA TEST

Tests must load generated:

customer_context.jsonl
portfolio_context_index
context_manifest.json
golden_context_validation.json

and validate required structure.

Do not consider successful serialization sufficient.

Rule:

CTX-SCHEMA-001

---

# 53. SOURCE MUTATION GATE

Hash source data before and after TASK-005.

Required:

identical hashes.

TASK-005 is read-only relative to accepted source data.

Rule:

CTX-READONLY-001

---

# 54. STATIC FORBIDDEN FIELD CHECK

Search executable TASK-005 output schema/code for unauthorized decision fields.

Forbidden executable output names include:

treatment
recommended_treatment
next_best_action
recommended_channel
recommended_when
best_contact_time
action_priority
recovery_probability
payment_probability
cure_probability
expected_recovery
expected_payment
confidence_score
ai_explanation
agent_reasoning
AEV
ROI

Context matters:

source_next_operation_channel

is allowed.

Tests checking that forbidden names do not exist are allowed.

---

# 55. STATIC SCOPE CHECK

TASK-005 must not implement executable integration with:

GreenNode
AgentBase
OpenAI
Anthropic
Gemini
DeepSeek
LLM
LightGBM
XGBoost
ML frameworks
FastAPI
Flask
Django
React
Next.js
frontend

No network calls.

No external API.

---

# 56. GOLDEN-SPECIFIC LOGIC CHECK

Golden/CIF identity may be used only in:

tests
validator
fixture/report selection

Production assembler must not say:

if cif == GOLDEN_G01
if cif == GOLDEN_G02

to alter assembled facts.

No Golden-specific assembly behavior.

Rule:

CTX-NO-GOLDEN-HACK-001

---

# 57. PRECHECK

Before coding, produce:

# TASK-005 PRECHECK

## GIT BASELINE

commit:
working_tree:
docs_spec_drift:

## ACCEPTED CHECKPOINTS

TASK-001:
TASK-002:
TASK-003:
TASK-004:

## AUTHORITATIVE SOURCES

customer:
loan:
cashflow:
payment:
PTP:
call:
operation:
policy:
Recovery Opportunity:
evaluation:

## OUTPUT CONTRACT

context_version:
as_of_date:
context_count:
portfolio_index:
preview_limit:
provenance:

## IMMUTABILITY CONTRACT

TASK-002 fields:
TASK-003 fields:
TASK-004 fields:

## FORBIDDEN DECISIONS

Confirm absent:

treatment
channel recommendation
best contact time
probability
expected recovery
AI explanation
GreenNode/Agent
ML
frontend
AEV/ROI

## BLOCKERS

NONE

or exact blocker.

If a required source field or deterministic ordering contract is genuinely undefined and cannot be resolved from accepted source schema:

STOP BEFORE CODING.

Return:

TASK-005 BLOCKED — CONTEXT CONTRACT REQUIRES UNSPECIFIED SOURCE SEMANTICS

Do not invent business meaning.

---

# 58. IMPLEMENTATION GATES

GATE T5-01 — Repository

PASS:
accepted TASK-004 commit exists;
working tree clean before implementation;
no spec drift.

GATE T5-02 — Join Integrity

PASS:
3,000 input CIF;
3,000 contexts;
0 duplicate;
0 missing;
0 unexpected.

GATE T5-03 — Policy Immutability

PASS:
all TASK-002 authoritative mismatch counts = 0.

GATE T5-04 — Recovery Immutability

PASS:
all TASK-003 authoritative mismatch counts = 0.

GATE T5-05 — Evaluation Immutability

PASS:
all TASK-004 authoritative mismatch counts = 0.

GATE T5-06 — Debt Integrity

PASS:
SUM/MAX aggregation independently verified.

GATE T5-07 — Evidence Boundary

PASS:
technical call status remains technical;
human PTP assessment remains human;
missing remains missing.

GATE T5-08 — Golden Contexts

PASS:
G01/G02/G04/G07/G08/G19/G20 assertions pass.

GATE T5-09 — No Future Decision

PASS:
no treatment/channel/when/probability/expected recovery fields.

GATE T5-10 — Provenance

PASS:
all context output clearly marked synthetic.

GATE T5-11 — Determinism

PASS:
two fresh runs produce identical artifacts.

GATE T5-12 — Regression

PASS:
TASK-001/002/003/004 tests and validators all pass.

GATE T5-13 — Scope

PASS:
no GreenNode/Agent/ML/frontend/AEV implementation.

---

# 59. REQUIRED FRESH PIPELINE

Use fresh /tmp directories.

Run:

python -m compileall -q src tests

PYTHONPATH=src python -m msb_synthetic.generator \
  --output /tmp/msb-task005-synthetic

PYTHONPATH=src python -m msb_synthetic.validate \
  /tmp/msb-task005-synthetic

Run TASK-001 tests.

Run TASK-002 tests.

Run TASK-003 tests.

Run TASK-004 tests.

Run TASK-005 tests.

Run full unittest discovery.

Run policy validator.

Run Recovery CLI/validator.

Run Evaluation CLI/validator.

Run Context CLI/validator.

Run Context a second time in another directory.

Compare TASK-005 artifacts byte-for-byte / SHA-256.

---

# 60. GIT RULE

Do NOT automatically commit TASK-005 implementation.

At end:

git status --short
git diff --stat
git diff --check
git diff -- docs/spec-v1

TASK-005 implementation must remain uncommitted until independent audit ACCEPT.

---

# 61. REQUIRED FINAL REPORT

Return exactly:

# TASK-005 RESULT

PASS
or
FAIL

## BASELINE

Git commit before implementation:
Working tree before implementation:
Accepted checkpoints:

## PRECHECK RESULT

Context contract:
Source semantics:
Blockers:

## FILES CREATED / MODIFIED

Modified:
Created:
Generated:
docs/spec-v1 modified:
Git commit created:

## CONTEXT CONTRACT IMPLEMENTED

List rule IDs:

CTX-BOUNDARY-001
CTX-OBJECT-001
CTX-VERSION-001
CTX-DATE-001
CTX-CUSTOMER-001
CTX-DEBT-001
CTX-POLICY-001
CTX-CASHFLOW-001
CTX-PAYMENT-001
CTX-PTP-001
CTX-PTP-002
CTX-CONTACT-001
CTX-PREVIEW-001
CTX-ORDER-001
CTX-RECOVERY-001
CTX-RANKING-001
CTX-BASELINE-001
CTX-AVAILABILITY-001
CTX-EVIDENCE-001
CTX-PROVENANCE-001
CTX-PRIVACY-001
CTX-INDEX-001
CTX-INDEX-ORDER-001
CTX-LOOKUP-001
CTX-NO-ACTION-001
CTX-NO-AI-TEXT-001
CTX-IMMUTABILITY-001
CTX-POLICY-IMMUTABILITY-001
CTX-G01-001
CTX-G02-001
CTX-G04-001
CTX-ROUTE-GOLDEN-001
CTX-G19-001
CTX-G20-001
CTX-GOLDEN-001
CTX-JOIN-001
CTX-MISSING-001
CTX-NUMERIC-001
CTX-DETERMINISM-001
CTX-MANIFEST-001
CTX-SCHEMA-001
CTX-READONLY-001
CTX-NO-GOLDEN-HACK-001

## PORTFOLIO

Input CIF:
Output contexts:
Duplicate:
Missing:
Unexpected:

Portfolio index count:

## G01

Summarize assembled context.

## G02

Summarize assembled context.

## G04

Summarize assembled context.

## G07 / G08

Routes:

## G19

technical Success:
PTP:
Willingness:
interpretation:

## G20

loan count:
SUM:
MAX DPD:

## IMMUTABILITY

TASK-002 mismatch counts:
TASK-003 mismatch counts:
TASK-004 mismatch counts:

## AVAILABILITY / MISSING DATA

Summarize checks.

## PROVENANCE

synthetic:
label:
reference date:

## FORBIDDEN OUTPUT AUDIT

treatment:
recommended channel:
recommended when:
probability:
expected recovery:
AI explanation:
AEV:
ROI:

## GOLDEN RESULTS

G01:
G02:
...
G20:

Use:

PASS
FAIL
NOT_APPLICABLE

## OUTPUT ARTIFACTS

customer_context:
record count:

portfolio_context_index:
record count:

golden_context_validation:

context_manifest:

## DETERMINISM

Artifact:
Run A hash:
Run B hash:

for every TASK-005 artifact.

## SOURCE MUTATION

Before hash:
After hash:
Result:

## TEST RESULTS

Exact commands and results.

TASK-001:
TASK-002:
TASK-003:
TASK-004:
TASK-005:
Full suite:

## SPEC DEVIATIONS

NONE
or details.

## ASSUMPTIONS

NONE
or authorized technical assumptions only.

## UNRESOLVED BUSINESS QUESTIONS

NONE
or exact blocker.

## ACCEPTED TASK REGRESSIONS

NONE
or details.

## OUT-OF-SCOPE CONFIRMATION

TASK-005 did NOT implement:

- score changes
- ranking changes
- routing changes
- treatment
- channel recommendation
- best-time recommendation
- GreenNode
- AgentBase
- LLM
- ML
- frontend
- REST server
- What-if
- AEV
- ROI
- prediction

## GIT STATUS

git status --short:

git diff --stat:

git diff --check:

git diff -- docs/spec-v1:

## NEXT GATE

READY FOR TASK-006 REVIEW

or

NOT READY FOR TASK-006

Do not implement TASK-006.

STOP.

---

# 62. DEFINITION OF DONE

TASK-005 is DONE only when:

1. Exactly 3,000 Decision Context objects exist.
2. Every accepted CIF appears exactly once.
3. No accepted TASK-002/003/004 fact changes.
4. Customer 360 contains debt, policy, cashflow, payment, PTP, contact, Recovery, ranking and provenance sections.
5. Missing evidence remains distinguishable from zero evidence.
6. Technical call Success remains technical.
7. Employee PTP ability remains human assessment.
8. No future treatment/channel/time/probability is invented.
9. G01/G02/G04/G07/G08/G19/G20 pass.
10. All output is explicitly synthetic prototype data.
11. Artifacts are deterministic.
12. Full regression passes.
13. Independent audit ACCEPTS TASK-005.
14. TASK-005 is committed only AFTER audit acceptance.

END OF TASK-005