# TASK-003 — RECOVERY OPPORTUNITY ENGINE

## ROLE

You are the implementation engineer for:

MSB Collection Decision Copilot

TASK-001 — Synthetic Data Foundation
STATUS: ACCEPTED

TASK-002 — Deterministic Policy / Rule Engine
STATUS: ACCEPTED

Your job is to implement exactly:

TASK-003 — Recovery Opportunity Engine

This task introduces the deterministic scoring and ranking layer used to estimate:

"Which collection case represents the strongest recovery opportunity right now?"

The engine must combine structured evidence from:

- business urgency;
- ability to pay;
- willingness to pay;
- contactability;
- timing opportunity;
- strategic adjustment.

This is NOT a machine-learning task.

This is NOT an LLM task.

This is NOT a treatment recommendation task.

This is NOT a routing task.

The scoring engine must remain deterministic, explainable, reproducible, and subordinate to the hard policy/routing result produced by TASK-002.

---

# PRODUCT THESIS

The current baseline primarily prioritizes:

total outstanding at CIF level
+
MAX DPD at CIF level

The product thesis is:

The customer with the largest debt or highest DPD is not necessarily the best recovery opportunity right now.

Recovery Opportunity must consider:

- urgency;
- current ability to pay;
- willingness/payment behavior;
- ability to establish contact;
- timing;
- strategic adjustment.

The engine must provide evidence supporting every score component.

---

# REQUIRED READING — BEFORE WRITING CODE

Read ALL of these files completely before implementation:

1. docs/spec-v1/PRODUCT_SPEC_V1.md
2. docs/spec-v1/RULE_BASE_V1.md
3. docs/spec-v1/SYNTHETIC_DATA_SPEC.md
4. docs/spec-v1/GOLDEN_SCENARIOS_V1.md
5. docs/spec-v1/README.md
6. docs/spec-v1/UBUNTU_BUILD_HANDOFF.md
7. TASK-001.md
8. TASK-002.md
9. existing TASK-001 implementation
10. existing TASK-001 tests
11. existing TASK-002 implementation
12. existing TASK-002 tests

The files under:

docs/spec-v1/

are LOCKED.

Do NOT modify them.

---

# SPEC PRIORITY

When interpreting business behavior:

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

If specifications conflict:

STOP.

Report:

SPEC CONFLICT

including:
- file;
- section;
- rule ID;
- conflicting requirement.

Do not choose an interpretation yourself.

---

# CRITICAL ANTI-INVENTION RULE

Before writing scoring code, inspect RULE_BASE_V1.md and enumerate every scoring rule and every scoring threshold explicitly defined there.

You MUST NOT invent:

- sub-feature weights;
- score thresholds;
- normalization thresholds;
- percentile bands;
- cashflow thresholds;
- contactability thresholds;
- PTP penalties;
- PTP bonuses;
- DPD bands;
- debt bands;
- timing windows;
- strategic adjustment values;
- missing-data penalties;
- confidence formulas.

If the locked specification defines the component maximum weights but does NOT define enough deterministic sub-feature formulas to produce the component scores:

STOP.

Return:

TASK-003 BLOCKED — SCORING FORMULA NOT FULLY SPECIFIED

Then list exactly which scoring formulas/thresholds are missing.

Do NOT fill gaps using "reasonable defaults".

Do NOT infer business logic from examples unless the specification explicitly marks the example as a locked prototype rule.

This requirement has higher priority than completing TASK-003.

---

# TASK OBJECTIVE

Implement a deterministic:

Recovery Opportunity Engine

that consumes:

TASK-001 synthetic evidence
+
TASK-002 PolicyResult

and produces:

RecoveryOpportunityResult

for each CIF.

The engine must calculate:

Business Urgency        max 20
Ability to Pay          max 25
Willingness to Pay      max 20
Contactability          max 15
Timing Opportunity      max 15
Strategic Adjustment    max 5
                       -------
TOTAL                   max 100

The total score must satisfy:

0 <= recovery_opportunity_score <= 100

The component weights are LOCKED.

Do not change them.

---

# TASK BOUNDARY

TASK-003 MAY implement only:

1. scoring feature derivation explicitly required by the locked specification;
2. deterministic component scoring;
3. total Recovery Opportunity Score;
4. score evidence;
5. component breakdown;
6. score trace;
7. data-quality/confidence facts if fully specified;
8. deterministic Recovery Opportunity ranking;
9. Baseline vs Recovery Opportunity comparison artifacts;
10. Golden scoring/ranking validations.

TASK-003 MUST NOT implement:

- routing changes;
- challenge allocation logic;
- treatment recommendation;
- WAIT_SELF_CURE decision;
- PTP_RECOVERY treatment;
- CONTACT treatment;
- CALLBACK treatment;
- VERIFY_CONTACT treatment;
- ESCALATE treatment;
- channel recommendation;
- best contact time recommendation;
- SMS/ZALO/CALL optimization;
- Agent reasoning;
- GreenNode MaaS;
- AgentBase;
- What-if Agent;
- frontend;
- AEV;
- ML;
- LightGBM;
- XGBoost;
- synthetic-trained predictive model;
- production probability-of-payment claims.

Those belong to later tasks.

---

# ARCHITECTURAL INVARIANT

TASK-002 owns:

Hard Policy
Routing
Challenge Override
PTP deterministic state
Source next-action facts

TASK-003 MUST NOT change these outputs.

The following fields from PolicyResult must be treated as immutable inputs:

cif
total_outstanding_cif
max_dpd_cif
base_route
challenge_override_route
final_route
ptp_status
source_next_action_date
source_next_operation_channel
hard_suppressed

Recovery scoring may consume these facts where explicitly permitted by RULE_BASE_V1.

It must never rewrite them.

Example:

final_route = CALL
recovery_opportunity_score = 12

must remain:

final_route = CALL

Example:

final_route = CALL
recovery_opportunity_score = 100

must still remain:

final_route = CALL

Score never changes routing.

---

# LOCKED SCORE STRUCTURE

The score structure is:

## 1. BUSINESS URGENCY

Maximum:

20 points

Potential evidence categories identified by the specification may include:

- max DPD;
- delinquency/bucket;
- total outstanding;
- PTP overdue urgency.

Use ONLY formulas explicitly defined by RULE_BASE_V1.

Do not allow raw outstanding to dominate the total score.

If percentile/log normalization is explicitly required by the locked rule, implement it exactly.

Do not invent percentile bands.

Maximum:

20

Minimum:

0

---

## 2. ABILITY TO PAY

Maximum:

25 points

Potential evidence categories identified by the specification may include:

- inflow_3d;
- inflow_7d;
- inflow_30d;
- net_cashflow_30d;
- salary-like income;
- business income;
- recent large inflow;
- liquidity_to_due_ratio;
- cashflow stability.

Use detailed TASK-001 cashflow transactions as source evidence.

Derived features must be deterministic.

Do not use an LLM to classify cashflow.

If source_type is already synthetic structured data such as:

SALARY
BUSINESS_INCOME
TRANSFER
DEPOSIT
OTHER

use it directly according to the locked specification.

Do not invent cashflow categories.

Maximum:

25

Minimum:

0

---

# CASHFLOW FEATURE DERIVATION

Where explicitly required by the specification, derive features from actual cashflow_transaction rows.

Examples of deterministic feature shapes include:

inflow_3d
inflow_7d
inflow_30d
outflow_7d
net_cashflow_30d
salary_like_signal
recent_large_inflow
liquidity_to_due_ratio

Do NOT read precomputed expected Golden score fields as the source of actual feature calculation.

For example:

inflow_7d

must be calculated from transaction rows inside the configured reference window.

Do not simply copy:

expected_inflow_7d

from a Golden fixture.

---

## 3. WILLINGNESS TO PAY

Maximum:

20 points

Potential evidence categories identified by the specification may include:

- PTP KEPT;
- PTP PARTIAL;
- PTP BROKEN;
- PTP fulfillment ratio;
- payment history;
- NPTP;
- RTP;
- previous payment after contact;
- payment_ptp_ability.

Important:

payment_ptp_ability is a HUMAN ASSESSMENT SIGNAL.

Values:

CERTAIN
HIGH
MEDIUM
LOW
VERY_LOW

It must NOT be treated as:

- ground truth;
- repayment probability;
- model label.

If RULE_BASE_V1 defines points such as:

CERTAIN
HIGH
MEDIUM
LOW
VERY_LOW

implement the exact locked mapping.

Do not invent a mapping if it is not explicitly locked.

Technical call Success must never increase willingness merely because the call connected.

Maximum:

20

Minimum:

0

---

## 4. CONTACTABILITY

Maximum:

15 points

Potential deterministic evidence may include:

- outbound attempts;
- successful calls;
- success rate;
- repeated UTC;
- NIN;
- THIRT;
- consecutive failed calls;
- days since successful contact;
- talk duration.

Critical boundary:

call_history.status

is technical call status.

operation_result.operation_result

is business outcome.

Do not mix them.

A technical:

Success

does NOT mean:

PTP

and does NOT automatically mean:

high willingness.

Contactability may use technical connection evidence only according to locked scoring rules.

Maximum:

15

Minimum:

0

---

## 5. TIMING OPPORTUNITY

Maximum:

15 points

Potential evidence may include:

- recent cashflow window;
- promise due timing;
- broken PTP timing;
- explicit next_action_date;
- historical successful contact windows.

TASK-003 calculates timing opportunity score only.

It MUST NOT output:

recommended_when

or:

best_contact_time recommendation

unless the locked specification explicitly defines that as part of TASK-003.

The future recommendation layer owns WHEN.

TASK-003 may expose deterministic timing features that future tasks consume.

Maximum:

15

Minimum:

0

---

## 6. STRATEGIC ADJUSTMENT

Maximum:

5 points

Potential evidence may include:

- explicit MSB priority;
- explicit portfolio adjustment;
- explicit manual/synthetic strategic flag.

Only implement strategic adjustment logic that is explicitly defined in RULE_BASE_V1.

Do NOT use challenge_override_route as an automatic score bonus.

Challenge override is routing policy, not Recovery Opportunity evidence.

Do not invent strategic flags.

Maximum:

5

Minimum:

0

---

# TOTAL SCORE

Calculate:

recovery_opportunity_score =
    business_urgency_score
  + ability_to_pay_score
  + willingness_to_pay_score
  + contactability_score
  + timing_opportunity_score
  + strategic_adjustment_score

Maximum:

100

Minimum:

0

Do not add hidden multipliers.

Do not add LLM adjustments.

Do not add route bonuses.

Do not add CALL/CBS bonuses.

Do not add debt multipliers outside component rules.

Do not add post-processing corrections unless explicitly defined by RULE_BASE_V1.

---

# SCORE COMPONENT CONTRACT

Each component must expose:

name
score
max_score
evidence
triggered_rule_ids

Conceptual example:

{
  "name": "ABILITY_TO_PAY",
  "score": 18,
  "max_score": 25,
  "evidence": {
    "inflow_7d": 40000000,
    "promise_amount": 15000000,
    "liquidity_to_due_ratio": 2.6667
  },
  "triggered_rule_ids": [...]
}

Evidence must be structured.

No LLM prose.

---

# RECOVERY OPPORTUNITY RESULT CONTRACT

Create a strongly structured result.

Conceptually:

RecoveryOpportunityResult

must expose at least:

cif

base_route
challenge_override_route
final_route

total_outstanding_cif
max_dpd_cif

business_urgency_score
ability_to_pay_score
willingness_to_pay_score
contactability_score
timing_opportunity_score
strategic_adjustment_score

recovery_opportunity_score

component_breakdown

derived_features

triggered_rule_ids

score_trace

baseline_rank
recovery_rank

data_quality
confidence

IMPORTANT:

Only implement data_quality/confidence numeric formulas if explicitly defined.

If the specification requires evidence completeness but not a numeric confidence formula, represent deterministic completeness facts rather than inventing a probability.

Never output:

probability_of_payment

unless explicitly specified.

---

# SCORE TRACE

Every score contribution must be traceable.

Conceptual example:

[
  {
    "rule_id": "<locked score rule>",
    "component": "ABILITY_TO_PAY",
    "result": "MATCH",
    "points": 4,
    "evidence": {
      "inflow_7d": 40000000
    }
  }
]

Trace must expose at least:

rule_id
component
result
points
evidence

A judge should be able to understand why:

score = X

without an LLM.

---

# NO DOUBLE COUNTING

Do not count the same business signal multiple times unless RULE_BASE_V1 explicitly says to.

Examples requiring care:

PTP BROKEN

must not silently create:

+ urgency
- willingness
+ timing

unless each contribution is explicitly defined in locked scoring rules.

Likewise:

recent inflow

must not automatically create points in multiple components unless specified.

If the same evidence legitimately contributes to multiple components according to explicit rules:

preserve separate rule IDs and traces.

---

# FEATURE WINDOWS

All time-window features must use an explicit:

reference_date

or:

reference_datetime

from configuration/input.

Never use:

datetime.now()
date.today()
system current time

inside deterministic scoring logic.

Examples:

inflow_3d
inflow_7d
inflow_30d
calls_30d

must be calculated relative to the configured reference time.

TASK-001 currently uses the synthetic reference period around:

2026-08-28

Use the locked/configured reference date from existing project behavior.

Do not hardcode a new unrelated current date.

---

# DECIMAL / MONEY

Money is VND.

Use deterministic numeric handling.

Do not use floating-point arithmetic where it could introduce unstable money calculations.

Prefer:

Decimal

or equivalent deterministic numeric handling.

Ratios may be quantized consistently where required.

Do not round intermediate values differently across runs.

---

# BASELINE RANK

Reuse TASK-002 baseline semantics.

Baseline benchmark order:

total_outstanding_cif DESC
max_dpd_cif DESC
cif ASC

Do not redefine baseline.

Do not modify TASK-002 baseline logic unnecessarily.

The result should preserve:

baseline_rank

for comparison.

---

# RECOVERY RANK

Create deterministic Recovery Opportunity ranking.

Primary:

recovery_opportunity_score DESC

Tie-breakers MUST come from the locked specification.

If tie-breakers are not specified:

STOP and report the missing deterministic tie-break contract.

Do not invent a business tie-breaker.

If the specification explicitly allows a purely technical deterministic tie-break such as CIF ASC, label it technical rather than business logic.

Do not silently use debt as tie-break unless specified.

---

# ROUTE-AWARE PRESENTATION VS ROUTE-AWARE SCORING

Do not add route points.

Do not score CALL higher than CBS merely because it is CALL.

Do not score CBS lower merely because it is CBS.

Recovery Opportunity Score and routing are separate concepts.

If future UI wants separate queues per route, that is presentation/filtering.

TASK-003 scoring must not mutate route.

---

# HARD SUPPRESSION

Respect TASK-002:

hard_suppressed

If a case is hard-suppressed:

do not override suppression.

Whether suppressed cases receive a calculated analytical score must follow RULE_BASE_V1.

If the locked specification does not say whether to calculate score for hard-suppressed cases and this situation exists in TASK-001 data:

STOP and report ambiguity.

Do not assume:

score = 0

unless explicitly specified.

---

# GOLDEN SCENARIOS

TASK-003 must evaluate all 20 Golden Scenario CIFs where scoring inputs exist.

Do not modify Golden Scenario source data.

Do not modify expected fixtures to make scoring pass.

---

# HERO SCENARIOS

G01–G05 are HERO scenarios.

They are particularly important for TASK-003.

---

## G01 — BASELINE WEAKNESS

G01 represents:

high debt
high DPD
but weaker recovery opportunity evidence.

The engine must preserve the fact that G01 can rank highly in baseline because of debt/DPD.

Recovery Opportunity must NOT automatically rank G01 first solely because of:

high outstanding
high DPD.

---

## G02 — RECOVERY OPPORTUNITY HERO

G02 represents:

moderate debt
recent cashflow
PTP due
stronger timing/contact opportunity.

Under the locked demo scoring configuration:

G02 Recovery Opportunity rank must be better than G01.

This is a critical product assertion.

Expected relationship:

baseline_rank(G01) < baseline_rank(G02)

where lower rank number means better baseline position,

AND:

recovery_rank(G02) < recovery_rank(G01)

This proves:

baseline priority != recovery opportunity.

The test must use actual source transactions and policy facts.

Do not simply assert expected rank fixture values.

---

## G03 — SELF-CURE EVIDENCE

G03 contains evidence intended for later self-cure treatment logic.

TASK-003 may score relevant evidence according to locked rules.

TASK-003 MUST NOT output:

WAIT_SELF_CURE

That belongs to treatment logic in a later task.

The route from TASK-002 must remain unchanged.

---

## G04 — BROKEN PTP + RECENT INFLOW

G04 should demonstrate that:

broken PTP
+
recent cashflow

can create a meaningful Recovery Opportunity profile.

However:

TASK-003 must NOT output:

PTP_RECOVERY
CALL NOW

Those belong to later treatment/action tasks.

Only score and expose evidence.

---

## G05 — WHAT-IF FOUNDATION

G05 is a future What-if HERO scenario.

TASK-003 should make the scoring engine a pure deterministic function so a later task can:

clone state
? modify cashflow
? rerun score
? compare before/after

TASK-003 does NOT implement the interactive What-if Agent.

If the Golden specification contains a deterministic G05 score-change assertion that can be tested without implementing the What-if feature, test the underlying pure scoring behavior.

Do not implement future UI/Agent functionality.

---

# CRITICAL NON-HERO SCENARIOS

G09:
PTP KEPT evidence must be consumed correctly if willingness scoring rules specify it.

G10:
PTP PARTIAL evidence must be consumed correctly.

G11:
PTP BROKEN evidence must be consumed correctly.

G12:
PTP OPEN evidence must be consumed correctly.

G13:
NIN must affect only components explicitly defined by the scoring contract.

G14:
NA / next_action_date must remain source evidence.

G15:
Repeated UTC may affect contactability according to explicit scoring rules.

It must NOT automatically reduce willingness unless explicitly specified.

G16:
Must demonstrate:

ability != willingness

Strong ability evidence must not automatically produce strong willingness.

G17:
High DPD + strong cashflow must not automatically become self-cure.

TASK-003 does not implement treatment.

G18:
Historical self-cure evidence may contribute only where explicitly defined.

Do not output WAIT_SELF_CURE.

G19:
Technical Success must not create PTP or willingness.

G20:
Must continue to preserve:

total_outstanding_cif = 400,000,000
max_dpd_cif = 12

from actual loan aggregation.

---

# PRODUCT-LEVEL ASSERTION

Add an automated test demonstrating:

baseline priority != Recovery Opportunity priority

using actual Golden source data.

At minimum:

G01 vs G02.

The test must run the actual:

TASK-001 data
? TASK-002 policy engine
? TASK-003 scoring engine
? ranking

No hardcoded final scores.

No copying expected ranks into actual results.

---

# ROUTING IMMUTABILITY TESTS

Add explicit tests proving:

score calculation cannot change:

base_route
challenge_override_route
final_route

At minimum test:

1. CALL route with low score;
2. CALL route with high score;
3. CBS route with low score;
4. CBS route with high score;
5. challenge CBS ? CALL remains CALL after scoring;
6. challenge CALL ? CBS remains CBS after scoring.

The score engine should preferably not have authority to calculate routing at all.

It should consume PolicyResult.

---

# SCORE BOUNDS

Every component must satisfy:

0 <= component_score <= component_max

Total:

0 <= recovery_opportunity_score <= 100

Add tests over all 3,000 synthetic CIFs.

No case may exceed a component maximum.

No case may have negative score unless the locked scoring model explicitly represents component internals with negative contributions but clamps the final component.

If clamping behavior is not specified:

do not invent it.

---

# DETERMINISM

Same:

TASK-001 dataset
TASK-002 configuration
TASK-003 configuration
reference date

must produce identical:

derived features
component scores
total score
score trace
recovery ranking

No randomness.

No LLM.

No network.

No current system time.

Add a determinism test.

---

# DATA QUALITY

The scoring result should expose missing evidence clearly.

Examples:

cashflow evidence available / unavailable
call evidence available / unavailable
PTP evidence available / unavailable
payment evidence available / unavailable

Do not silently treat:

missing data

as:

bad customer behavior.

Missing evidence and negative evidence are different.

If numeric confidence is not fully specified, do NOT invent:

0.82 confidence

Instead use structured completeness facts, for example:

{
  "cashflow_available": true,
  "call_history_available": false,
  "ptp_history_available": true
}

Use exact project naming/style where possible.

---

# ENGINE DESIGN

Prefer a separate module such as conceptually:

src/msb_recovery/

Possible responsibilities:

features.py
scoring.py
ranking.py
io.py
validate.py
cli.py

This naming is only a technical suggestion.

You may choose an equivalent clean structure.

Do not move TASK-002 policy ownership into TASK-003.

Preferred flow:

TASK-001 data
       ?
TASK-002 PolicyResult
       ?
Feature derivation
       ?
Component scoring
       ?
Recovery Opportunity Score
       ?
Recovery ranking
       ?
Structured evidence/trace

---

# PURE FUNCTIONS

Business scoring should be implemented as deterministic pure functions where practical.

Feature derivation should be independently testable.

Component scoring should be independently testable.

Ranking should be independently testable.

Do not require PostgreSQL for unit tests if current project architecture does not require it.

---

# PERFORMANCE

The engine only needs to support the hackathon synthetic scale efficiently.

Target:

~3,000 CIF

Do not over-engineer.

Do not introduce:

Spark
Kafka
Redis
Celery
microservices
Kubernetes

TASK-003 should run locally on the Ubuntu server using the existing project runtime.

---

# OUTPUT ARTIFACT

Provide a deterministic machine-readable output.

Preferred:

build/recovery-opportunity/recovery_opportunity_result.csv

or equivalent JSONL.

It should include at minimum:

cif
baseline_rank
recovery_rank
base_route
challenge_override_route
final_route
total_outstanding_cif
max_dpd_cif
business_urgency_score
ability_to_pay_score
willingness_to_pay_score
contactability_score
timing_opportunity_score
strategic_adjustment_score
recovery_opportunity_score

Detailed evidence/trace may be:

JSON fields

or a separate deterministic artifact.

Also generate a compact Golden validation artifact such as:

build/recovery-opportunity/golden_recovery_validation.json

Exact technical filename may vary.

Generated reproducible artifacts should remain git-ignored.

---

# CLI

Provide a simple deterministic CLI.

Conceptually:

PYTHONPATH=src python -m msb_recovery.cli \
  --input build/synthetic-data \
  --output build/recovery-opportunity

The exact module name is a technical choice.

The CLI must:

1. load TASK-001 data;
2. run/reuse TASK-002 policy engine;
3. derive scoring features;
4. calculate component scores;
5. calculate total;
6. rank cases;
7. write deterministic output.

No network calls.

No LLM calls.

---

# VALIDATOR

Provide a validator.

Conceptually:

PYTHONPATH=src python -m msb_recovery.validate \
  build/recovery-opportunity

or equivalent.

Validator must independently check important invariants.

Do not merely trust:

"status": "PASS"

from generated output.

At minimum validate:

- record count;
- unique CIF;
- component bounds;
- total bounds;
- total = sum(component scores);
- routing preserved;
- G01/G02 relationship;
- G19 boundary;
- G20 aggregation preservation;
- deterministic Golden expectations explicitly supported by spec.

---

# TEST REQUIREMENTS

Add meaningful automated tests.

Tests must exercise actual implementation.

At minimum test:

1. Business Urgency lower bound.
2. Business Urgency upper bound.
3. Ability lower bound.
4. Ability upper bound.
5. Willingness lower bound.
6. Willingness upper bound.
7. Contactability lower bound.
8. Contactability upper bound.
9. Timing lower bound.
10. Timing upper bound.
11. Strategic Adjustment lower bound.
12. Strategic Adjustment upper bound.
13. Total score <= 100.
14. Total score >= 0.
15. Total equals component sum.
16. cashflow feature calculated from source transactions.
17. payment feature calculated from source events.
18. PTP KEPT handled according to locked score rule.
19. PTP PARTIAL handled according to locked score rule.
20. PTP BROKEN handled according to locked score rule.
21. PTP OPEN handled according to locked score rule.
22. payment_ptp_ability remains human signal.
23. repeated UTC handled only in correct component.
24. NIN handled only in correct component.
25. technical Success does not create willingness/PTP.
26. missing evidence != negative evidence.
27. reference date controls time windows.
28. score deterministic.
29. ranking deterministic.
30. G01 baseline beats G02 under baseline as specified.
31. G02 Recovery Opportunity beats G01 under locked demo configuration.
32. G07 routing remains challenge CALL.
33. G08 routing remains challenge CBS.
34. G19 technical/business boundary preserved.
35. G20 aggregation remains 400M / MAX DPD 12.
36. all 3,000 CIF component bounds.
37. all 3,000 CIF total bounds.
38. all 3,000 CIF unique recovery ranks if the locked tie-break contract guarantees unique ranking.
39. no score changes routing.
40. TASK-001 and TASK-002 regression suites still pass.

If a requested test requires a scoring formula that is NOT specified:

STOP.

Do not invent the formula merely to satisfy the test list.

---

# REGRESSION REQUIREMENTS

Run all existing tests.

TASK-003 must not break:

TASK-001
TASK-002

The full suite must PASS.

---

# OUT-OF-SCOPE STATIC CHECK

Before reporting PASS, inspect source code for accidental implementation of:

treatment
WAIT_SELF_CURE
PTP_RECOVERY
recommended_channel
recommended_when
GreenNode
AgentBase
OpenAI
Anthropic
LightGBM
XGBoost

References in documentation/comments/tests describing out-of-scope behavior are acceptable.

Actual implementation is not.

---

# SECURITY / PRIVACY

Use synthetic data only.

Do not introduce:

real MSB customer data
real customer phone numbers
real recordings
production credentials
API keys
GreenNode secrets

Do not commit secrets.

---

# EXISTING CODE

Preserve accepted TASK-001 and TASK-002 behavior.

Do not broadly refactor accepted modules.

If an accepted implementation defect is discovered:

STOP.

Report:

ACCEPTED TASK REGRESSION / DEFECT FOUND

Include:

task
file
scenario
expected
actual
proposed correction

Do not silently modify accepted behavior.

---

# README

Update the project README only as necessary to document:

TASK-003 execution
TASK-003 validation
output paths

Do not rewrite product requirements.

Do not modify docs/spec-v1.

---

# GIT DISCIPLINE

Do NOT commit automatically.

Before implementation run:

git status
git log --oneline -5

Working tree must be clean.

Expected history should include accepted checkpoints for:

- locked V1 specs;
- TASK-001;
- TASK-002;
- TASK-003 authorization after it is committed.

At completion run:

git status --short
git diff --stat
git diff -- docs/spec-v1

The last command must return no spec changes.

Do not commit implementation changes.

---

# STOP CONDITIONS

STOP and report NOT READY if:

1. scoring formula is incomplete;
2. scoring thresholds are missing;
3. sub-feature weights require invention;
4. ranking tie-break requires invention;
5. hard-suppression scoring behavior is ambiguous and encountered;
6. specs conflict;
7. TASK-001 data cannot support a required score;
8. TASK-002 PolicyResult lacks a required immutable input;
9. Golden expectations require changing accepted source fixtures;
10. TASK-001 or TASK-002 regression is discovered;
11. implementing TASK-003 requires treatment/action logic;
12. a real MSB rule is required but only an assumption exists.

Do not bypass a STOP condition.

---

# REQUIRED PRE-IMPLEMENTATION REPORT

Before writing scoring code, print:

# TASK-003 PRECHECK

## GIT BASELINE

commit:
working_tree:

## SCORING RULE INVENTORY

List every score-related rule ID found in RULE_BASE_V1.

For each:

rule_id
component
formula/threshold defined?
implementation possible without invention?

## COMPONENT FORMULA COMPLETENESS

BUSINESS_URGENCY:
ABILITY_TO_PAY:
WILLINGNESS_TO_PAY:
CONTACTABILITY:
TIMING_OPPORTUNITY:
STRATEGIC_ADJUSTMENT:

For each return:

COMPLETE
or
INCOMPLETE

If ANY component is INCOMPLETE:

STOP.

Return:

TASK-003 BLOCKED — SCORING FORMULA NOT FULLY SPECIFIED

Do not write implementation code.

## RANKING CONTRACT

State exact deterministic ranking/tie-break rule from the specification.

If incomplete:

STOP.

## HARD SUPPRESSION CONTRACT

State scoring behavior for hard-suppressed cases if applicable.

If required but undefined:

STOP.

Only after this precheck is fully PASS may implementation begin.

---

# REQUIRED FINAL REPORT

Return exactly this structure:

# TASK-003 RESULT

PASS
or
FAIL

## BASELINE

Git commit before implementation:
Working tree before implementation:

## PRECHECK RESULT

SCORING FORMULA:
RANKING CONTRACT:
HARD SUPPRESSION CONTRACT:

## FILES CREATED / MODIFIED

List every file.

Explicitly state whether any file under docs/spec-v1 was modified.

## SCORING RULES IMPLEMENTED

For every implemented scoring rule:

RULE_ID
component
points/formula
implementation location
test location

Do not list unimplemented rules.

## FEATURE DERIVATION

List every derived feature actually implemented.

For each:

feature
source table
window/formula
consumer component

## SCORE STRUCTURE

BUSINESS URGENCY:
max 20

ABILITY TO PAY:
max 25

WILLINGNESS TO PAY:
max 20

CONTACTABILITY:
max 15

TIMING OPPORTUNITY:
max 15

STRATEGIC ADJUSTMENT:
max 5

TOTAL:
max 100

## GOLDEN RESULTS

Report:

G01: PASS / NOT_APPLICABLE / FAIL
...
G20: PASS / NOT_APPLICABLE / FAIL

For each HERO scenario G01-G05 include:

baseline_rank
recovery_rank
final_route
component scores
total score
key evidence

## CRITICAL ASSERTIONS

G01 baseline position:
G02 baseline position:
G01 recovery position:
G02 recovery position:
G02 ranks above G01 by Recovery Opportunity:
G07 final_route preserved:
G08 final_route preserved:
G19 Success != PTP/willingness:
G20 400M / MAX DPD 12:
score bounds:
routing mutation count:

## ALL-PORTFOLIO RESULTS

CIF count:
minimum score:
maximum score:
average score:
component bound violations:
total bound violations:
routing mutations:
duplicate CIFs:

Do not present synthetic score statistics as real MSB performance.

## TEST RESULTS

List every command actually executed.

Include:

TASK-001 regression
TASK-002 regression
TASK-003 unit tests
TASK-003 validator
full test suite

Do not claim commands that were not executed.

## OUTPUT ARTIFACTS

List generated artifact paths and record counts.

## DETERMINISM

Describe exact determinism validation performed.

## DATA QUALITY

Describe how missing evidence is represented.

Confirm:

missing evidence != negative evidence

## SPEC DEVIATIONS

NONE

or list every deviation.

## ASSUMPTIONS

Technical assumptions only.

Do not hide business assumptions.

## UNRESOLVED BUSINESS QUESTIONS

NONE

or list them.

## ACCEPTED TASK REGRESSIONS

NONE

or list them.

## OUT-OF-SCOPE CONFIRMATION

Explicitly confirm TASK-003 did NOT implement:

Routing changes
Treatment optimization
WAIT_SELF_CURE
PTP_RECOVERY
Channel recommendation
Best-time recommendation
GreenNode
AgentBase
LLM
ML
Frontend
AEV

## GIT STATUS

Show:

git status --short
git diff --stat
git diff -- docs/spec-v1

## NEXT GATE

Return exactly one:

READY FOR TASK-004 REVIEW

or

NOT READY FOR TASK-004

STOP.

Do not implement TASK-004.