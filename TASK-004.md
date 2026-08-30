# TASK-004 — BASELINE VS RECOVERY OPPORTUNITY EVALUATION

## STATUS

AUTHORIZED AFTER TASK-003 ACCEPTANCE

TASK-001 = ACCEPTED
TASK-002 = ACCEPTED
TASK-003 = ACCEPTED

TASK-004 must not begin unless:

- TASK-003 independent audit = ACCEPT;
- TASK-003 implementation is committed;
- working tree is clean;
- docs/spec-v1 has no drift.

---

# 1. PURPOSE

Implement a deterministic evaluation layer that compares:

CURRENT BASELINE PRIORITIZATION

versus

RECOVERY OPPORTUNITY PRIORITIZATION

for the accepted synthetic portfolio.

The purpose is to answer:

1. How different are the two rankings?
2. Which customers are promoted by Recovery Opportunity?
3. Which customers are demoted?
4. Why did those movements occur?
5. Does the HERO story G01 vs G02 remain true?
6. Can the comparison be represented as machine-readable evidence for later demo/UI tasks?

TASK-004 evaluates ranking behavior.

TASK-004 does NOT claim actual collection performance improvement.

---

# 2. PRODUCT QUESTION

Current baseline asks:

"Who owes the most and is most overdue?"

Recovery Opportunity asks:

"Where is the strongest recovery opportunity right now?"

TASK-004 must quantify the difference between those two prioritization approaches without claiming that either ranking has produced real-world recovery outcomes.

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
11. accepted TASK-001 implementation
12. accepted TASK-002 implementation
13. accepted TASK-003 implementation
14. all existing tests

Do not rely on previous conversational summaries.

The repository and locked specifications are authoritative.

---

# 4. SPEC PRECEDENCE

Business/spec precedence remains:

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
TASK-003_SCORING_CONTRACT.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

TASK-004.md defines evaluation behavior only.

TASK-004.md MUST NOT redefine:

- routing;
- PTP;
- score;
- feature derivation;
- Recovery ranking;
- baseline ranking.

---

# 5. ANTI-INVENTION RULE

TASK-004 must not invent:

- recovery uplift;
- payment probability;
- cure probability;
- expected recovery amount;
- collection success probability;
- monetary benefit;
- cost saving;
- collector productivity improvement;
- AEV;
- ROI;
- model accuracy;
- Precision@K against synthetic labels unless an explicitly approved ground-truth contract exists;
- Recall@K against synthetic labels unless an explicitly approved ground-truth contract exists;
- business-value weights;
- new scoring formulas;
- new ranking formulas;
- new Golden expected behavior.

If implementation requires an undefined business formula:

STOP.

Return:

TASK-004 BLOCKED — EVALUATION CONTRACT REQUIRES NEW BUSINESS ASSUMPTION

and list the exact missing decision.

Do not choose a reasonable default.

---

# 6. SCOPE

TASK-004 implements only:

Synthetic Data
      ?
TASK-002 PolicyResult
      ?
TASK-003 Recovery Opportunity Result
      ?
Baseline vs Recovery Evaluation
      ?
Machine-readable Evaluation Artifacts

Allowed:

- ranking comparison;
- rank movement;
- Top-K overlap;
- Top-K displacement;
- rank correlation;
- score/component descriptive statistics;
- route composition;
- evidence-based movement explanation;
- HERO comparison;
- deterministic artifacts;
- evaluation CLI;
- validator;
- tests.

Not allowed:

- changing synthetic data;
- changing Policy Engine;
- changing Recovery Opportunity Engine;
- treatment recommendation;
- WAIT_SELF_CURE;
- PTP_RECOVERY;
- channel recommendation;
- best-time recommendation;
- actionable queue;
- GreenNode;
- AgentBase;
- LLM;
- ML;
- frontend;
- AEV;
- financial uplift;
- real-world recovery prediction.

---

# 7. AUTHORITATIVE INPUTS

TASK-004 must consume accepted engine outputs.

Authoritative portfolio inputs:

TASK-002:
- total_outstanding_cif
- max_dpd_cif
- base_route
- challenge_override_route
- final_route
- hard_suppressed
- PTP facts
- source next-action facts

TASK-003:
- baseline_rank
- recovery_rank
- recovery_opportunity_score
- business_urgency_score
- ability_to_pay_score
- willingness_to_pay_score
- contactability_score
- timing_opportunity_score
- strategic_adjustment_score
- evidence availability
- score trace

TASK-004 must NOT recalculate TASK-003 scoring differently.

TASK-004 may independently reproduce ranking only for validation.

---

# 8. BASELINE CONTRACT

The accepted baseline order remains:

total_outstanding_cif DESC
max_dpd_cif DESC
cif ASC

TASK-004 must use the accepted baseline_rank.

For independent validation only, it may reproduce this sort and compare ranks.

No other baseline formula is authorized.

---

# 9. RECOVERY RANKING CONTRACT

The accepted Recovery Opportunity ranking remains:

recovery_opportunity_score DESC
ability_to_pay_score DESC
willingness_to_pay_score DESC
timing_opportunity_score DESC
cif ASC

TASK-004 must use accepted recovery_rank.

For independent validation only, it may reproduce the sort and compare ranks.

TASK-004 must not change this ordering.

---

# 10. CORE RANK MOVEMENT

For every CIF calculate:

rank_delta =
baseline_rank - recovery_rank

Interpretation:

rank_delta > 0
? PROMOTED

rank_delta < 0
? DEMOTED

rank_delta = 0
? UNCHANGED

Examples:

baseline rank 1209
recovery rank 84

rank_delta =
1209 - 84
= +1125

movement:
PROMOTED

baseline rank 1
recovery rank 917

rank_delta =
1 - 917
= -916

movement:
DEMOTED

Rule:

EVAL-MOVE-001

No arbitrary movement threshold is required for basic movement classification.

---

# 11. ABSOLUTE RANK MOVEMENT

Calculate:

absolute_rank_delta =
abs(rank_delta)

Rule:

EVAL-MOVE-002

This is descriptive only.

Do not interpret large movement as automatically correct or incorrect.

---

# 12. NORMALIZED RANK MOVEMENT

For a portfolio containing N CIFs:

normalized_rank_delta =
rank_delta / max(N - 1, 1)

Range:

-1 <= normalized_rank_delta <= 1

Use Decimal.

Rule:

EVAL-MOVE-003

This allows rank movement to remain comparable if portfolio size changes.

It is descriptive only.

---

# 13. TOP-K CONTRACT

Evaluate the following fixed descriptive cutoffs:

K = 10
K = 50
K = 100

These are:

[PROTOTYPE-EVALUATION-CONFIG]

They are NOT MSB business thresholds.

They exist only to make ranking comparison interpretable in the hackathon evaluation.

Do not use them to change scoring or routing.

---

# 14. TOP-K MEMBERSHIP

For each K calculate:

baseline_top_k =
CIFs where baseline_rank <= K

recovery_top_k =
CIFs where recovery_rank <= K

Rule:

EVAL-TOPK-001

---

# 15. TOP-K OVERLAP

For each K:

top_k_overlap_count =
|baseline_top_k n recovery_top_k|

top_k_overlap_ratio =
top_k_overlap_count / K

Rule:

EVAL-TOPK-002

Example:

baseline Top100 and Recovery Top100 share 40 CIFs:

overlap_count = 40
overlap_ratio = 0.40

This measures ranking similarity only.

It is NOT Precision@K.

Do not label it precision.

---

# 16. TOP-K DISPLACEMENT

For each K:

promoted_into_top_k =
recovery_top_k - baseline_top_k

demoted_out_of_top_k =
baseline_top_k - recovery_top_k

Counts:

promoted_into_top_k_count =
|promoted_into_top_k|

demoted_out_of_top_k_count =
|demoted_out_of_top_k|

For equal-size rankings:

promoted_into_top_k_count
must equal
demoted_out_of_top_k_count

Rule:

EVAL-TOPK-003

Any mismatch is a validation failure.

---

# 17. RANK CORRELATION

Calculate Spearman rank correlation between:

baseline_rank

and

recovery_rank

for all evaluated CIFs.

Because both are complete unique rankings from 1..N, calculate:

rho =
1 - (6 * SUM(d_i^2)) / (N * (N^2 - 1))

where:

d_i =
baseline_rank_i - recovery_rank_i

Use Decimal or exact integer intermediate calculations.

Output rho with deterministic decimal serialization.

Rule:

EVAL-CORR-001

Interpretation must remain descriptive.

Do not introduce qualitative labels such as:

HIGH
LOW
GOOD
BAD

unless explicitly approved later.

---

# 18. MOVEMENT EXPLANATION CONTRACT

TASK-004 must provide deterministic structured evidence explaining rank movement.

It must NOT use an LLM.

For every CIF output:

movement_factors

derived from TASK-003 component scores.

Allowed factor names:

BUSINESS_URGENCY
ABILITY_TO_PAY
WILLINGNESS_TO_PAY
CONTACTABILITY
TIMING_OPPORTUNITY
STRATEGIC_ADJUSTMENT

For deterministic ordering:

sort factors by:

component_score DESC
then factor name ASC

Only include factors with:

component_score > 0

Each factor must include:

factor
score
max_score
supporting_rule_ids

Rule:

EVAL-EXPLAIN-001

This describes score composition.

It must NOT claim causal proof that a factor caused repayment.

---

# 19. PRIMARY MOVEMENT FACTORS

For each CIF:

primary_movement_factors =
first up to 3 entries from movement_factors

using the deterministic ordering above.

Rule:

EVAL-EXPLAIN-002

If no component has score > 0:

primary_movement_factors = []

Do not invent a textual reason.

Later Agent/UI tasks may convert structured evidence into natural language.

---

# 20. BASELINE EVIDENCE

For each CIF preserve:

baseline_evidence:
- total_outstanding_cif
- max_dpd_cif

Recovery evidence:

- recovery_opportunity_score
- six component scores
- primary_movement_factors

Rule:

EVAL-EVIDENCE-001

This allows future UI to show:

"Baseline prioritized this customer because of debt/DPD."

versus:

"Recovery Opportunity prioritized this customer because of the score evidence."

TASK-004 itself should keep evidence structured.

---

# 21. ROUTE COMPOSITION

For descriptive evaluation only, calculate portfolio counts by:

final_route

for:

- full portfolio;
- baseline Top10;
- recovery Top10;
- baseline Top50;
- recovery Top50;
- baseline Top100;
- recovery Top100.

Rule:

EVAL-ROUTE-001

Do not interpret route composition as performance.

Do not modify route.

---

# 22. COMPONENT DESCRIPTIVE STATISTICS

For the full portfolio calculate for each component:

- minimum
- maximum
- arithmetic mean

Components:

business_urgency_score
ability_to_pay_score
willingness_to_pay_score
contactability_score
timing_opportunity_score
strategic_adjustment_score
recovery_opportunity_score

Rule:

EVAL-STATS-001

These are synthetic descriptive statistics.

Every output/report containing these statistics must clearly label:

SYNTHETIC PROTOTYPE STATISTIC

No production inference.

---

# 23. TOP-K COMPONENT PROFILE

For each K:

10
50
100

calculate arithmetic mean for the six Recovery Opportunity components among:

baseline_top_k

and:

recovery_top_k

Rule:

EVAL-STATS-002

Purpose:

show how the composition of the prioritized population differs.

Example conceptual use:

baseline Top100 may be dominated by urgency.

Recovery Top100 may contain stronger Ability/Timing/Contactability evidence.

TASK-004 must report the numbers only.

Do not claim improved collection outcomes.

---

# 24. HERO SCENARIO — G01

G01 remains a critical HERO example.

Expected accepted facts from prior tasks must remain true.

TASK-004 must report:

cif
baseline_rank
recovery_rank
rank_delta
movement
baseline evidence
Recovery Opportunity score
six component scores
primary movement factors
final_route

Expected direction:

DEMOTED

TASK-004 must not hard-code G01's result.

The result must come from accepted engine output.

Rule:

EVAL-HERO-G01

---

# 25. HERO SCENARIO — G02

G02 remains a critical HERO example.

TASK-004 must report:

cif
baseline_rank
recovery_rank
rank_delta
movement
baseline evidence
Recovery Opportunity score
six component scores
primary movement factors
final_route

Expected direction:

PROMOTED

TASK-004 must not hard-code G02's result.

Rule:

EVAL-HERO-G02

---

# 26. G01 VS G02 COMPARISON

Generate a structured HERO comparison:

baseline:

G01 rank
G02 rank
winner = lower rank

Recovery Opportunity:

G01 rank
G02 rank
winner = lower rank

Required accepted assertion:

baseline:
G01 ranks ahead of G02

Recovery:
G02 ranks ahead of G01

Rule:

EVAL-HERO-COMPARE-001

Do not add a business outcome claim.

Correct wording:

"Recovery Opportunity changes prioritization."

Forbidden wording:

"Recovery Opportunity proves G02 will repay."

---

# 27. GOLDEN SCENARIOS

TASK-004 must evaluate G01–G20 where TASK-004 has an applicable evaluation assertion.

Do not report a Golden scenario PASS unless an explicit TASK-004 assertion was executed.

Allowed statuses:

PASS
FAIL
NOT_APPLICABLE

Do not repeat the validator false-PASS problem fixed during TASK-003.

Rule:

EVAL-GOLDEN-001

At minimum explicitly validate:

G01
G02
G07
G08
G19
G20

Why:

G01/G02:
ranking comparison

G07/G08:
route preservation

G19:
technical Success/business PTP boundary must remain intact in source evidence

G20:
aggregation evidence remains intact

Other scenarios:

PASS only when an explicit TASK-004-relevant assertion exists.

Otherwise:

NOT_APPLICABLE

---

# 28. NO SYNTHETIC OUTCOME CLAIM

The synthetic dataset may contain:

payment events
PTP states
call outcomes

These may be used as accepted evidence where already defined by prior contracts.

TASK-004 MUST NOT convert them into an invented ground-truth label such as:

recovered = true
good recovery opportunity = true
model_correct = true

unless such label is explicitly locked in a later contract.

Therefore TASK-004 MUST NOT calculate:

Precision@10
Precision@50
Precision@100
Recall
F1
AUC
accuracy
recovery uplift
expected money recovered

Rule:

EVAL-NO-OUTCOME-001

This is a hard acceptance gate.

---

# 29. NO AEV

TASK-004 must not calculate:

annual economic value
hours saved
cost savings
incremental recovery
ROI
collector productivity uplift

AEV belongs to a later task.

Rule:

EVAL-NO-AEV-001

---

# 30. NO NEW SCORE

TASK-004 must not create:

evaluation_score
quality_score
business_value_score
ranking_quality_score
AI_score
confidence_score

Rule:

EVAL-NO-NEW-SCORE-001

TASK-003 Recovery Opportunity Score remains the only recovery prioritization score.

---

# 31. POLICY IMMUTABILITY

TASK-004 must preserve accepted TASK-002 fields exactly:

base_route
challenge_override_route
final_route
hard_suppressed
total_outstanding_cif
max_dpd_cif

TASK-004 must not modify accepted TASK-003 fields:

baseline_rank
recovery_rank
recovery_opportunity_score
all six component scores

Rule:

EVAL-IMMUTABILITY-001

Validation must compare all 3,000 CIFs.

Required mismatch count:

0

for every authoritative field.

---

# 32. DETERMINISM

Same:

synthetic dataset
TASK-002 output
TASK-003 output
evaluation configuration

must produce identical:

rank movements
Top-K sets
overlap metrics
displacement metrics
Spearman rho
route composition
component statistics
HERO comparison
machine-readable output

No randomness.

No LLM.

No network.

No current system clock.

Rule:

EVAL-DETERMINISM-001

---

# 33. NUMERIC SAFETY

Use:

Decimal
or exact integers

for:

normalized rank movement
ratios
means
Spearman correlation
Top-K overlap ratios

Do not use unsafe binary floating point for persisted deterministic metrics.

Rule:

EVAL-NUMERIC-001

---

# 34. REQUIRED IMPLEMENTATION STRUCTURE

Preferred package:

src/msb_evaluation/

Suggested modules:

__init__.py
engine.py
io.py
cli.py
validate.py

Names may differ slightly if repository architecture strongly suggests otherwise.

Do not create unnecessary framework abstractions.

---

# 35. REQUIRED RECORD — CIF EVALUATION

Each CIF evaluation result should contain at least:

cif

baseline_rank
recovery_rank

rank_delta
absolute_rank_delta
normalized_rank_delta
movement

total_outstanding_cif
max_dpd_cif

base_route
challenge_override_route
final_route
hard_suppressed

recovery_opportunity_score

business_urgency_score
ability_to_pay_score
willingness_to_pay_score
contactability_score
timing_opportunity_score
strategic_adjustment_score

movement_factors
primary_movement_factors

No textual AI explanation required.

---

# 36. REQUIRED SUMMARY ARTIFACT

Generate a machine-readable portfolio summary containing at least:

portfolio_size

spearman_rank_correlation

movement_counts:
- promoted
- demoted
- unchanged

rank_delta:
- minimum
- maximum
- mean_absolute

top_k:
- 10
- 50
- 100

For each K:

baseline_count
recovery_count
overlap_count
overlap_ratio
promoted_into_recovery_top_k_count
demoted_out_of_baseline_top_k_count
promoted_cifs
demoted_cifs

route_composition

component_statistics

top_k_component_profiles

hero_comparison

synthetic_statistic_label

Required label:

SYNTHETIC PROTOTYPE STATISTIC

---

# 37. REQUIRED OUTPUT ARTIFACTS

Preferred output:

build/evaluation/

Required:

baseline_vs_recovery.jsonl

One record per CIF.

portfolio_evaluation_summary.json

Machine-readable portfolio metrics.

golden_evaluation_validation.json

Explicit Golden validation statuses.

Optional:

baseline_vs_recovery.csv

Only if useful.

Do not generate presentation slides.

Do not generate frontend assets.

---

# 38. CLI

Provide a deterministic CLI.

Preferred shape:

PYTHONPATH=src python -m msb_evaluation.cli \
  --input build/synthetic-data \
  --output build/evaluation

The CLI may invoke accepted TASK-002/TASK-003 engines or consume their accepted outputs according to repository architecture.

It must not require:

network
LLM
GreenNode
database server
external API

---

# 39. VALIDATOR

Provide:

PYTHONPATH=src python -m msb_evaluation.validate \
  --input build/synthetic-data \
  --output build/evaluation/golden_evaluation_validation.json

Validator must independently verify critical TASK-004 invariants.

Do not simply trust values emitted by the evaluation engine.

At minimum independently validate:

- exactly 3,000 CIF;
- unique CIF;
- unique baseline ranks;
- unique recovery ranks;
- baseline ranks exactly 1..N;
- recovery ranks exactly 1..N;
- rank_delta formula;
- movement classification;
- Top-K set calculations;
- Top-K overlap;
- Top-K displacement equality;
- Spearman correlation;
- G01 baseline ahead of G02;
- G02 Recovery rank ahead of G01;
- G01 DEMOTED;
- G02 PROMOTED;
- G07 route preservation;
- G08 route preservation;
- G19 boundary preservation;
- G20 aggregation preservation;
- authoritative field mismatch count = 0;
- no forbidden outcome metrics;
- synthetic statistic label exists.

---

# 40. TEST REQUIREMENTS

TASK-004 tests must cover actual formulas, not merely validator PASS status.

Required tests include:

1. rank_delta positive ? PROMOTED
2. rank_delta negative ? DEMOTED
3. rank_delta zero ? UNCHANGED
4. absolute rank delta
5. normalized rank delta
6. Top10 membership
7. Top50 membership
8. Top100 membership
9. Top-K overlap
10. Top-K displacement
11. promoted count = demoted count for equal-size Top-K
12. Spearman identical rankings = 1
13. Spearman reversed toy rankings = -1
14. deterministic movement factor ordering
15. maximum 3 primary movement factors
16. zero-score components excluded from movement factors
17. route composition
18. component statistics
19. Top-K component profile
20. G01/G02 comparison
21. G07/G08 immutable routes
22. G19 boundary
23. G20 aggregation
24. all 3,000 CIF
25. unique complete ranks
26. deterministic rerun
27. no mutation of TASK-002 fields
28. no mutation of TASK-003 fields
29. no Precision/Recall/AUC/ROI/AEV outputs
30. synthetic-statistic labeling

Tests must independently construct expected results where practical.

Do not duplicate implementation code blindly inside tests.

---

# 41. FRESH-DATA REQUIREMENT

TASK-004 validation must be runnable from freshly generated TASK-001 data.

Do not rely solely on existing build artifacts.

Required fresh pipeline:

TASK-001 generator
? TASK-001 validator
? TASK-002 validator
? TASK-003 engine/validator
? TASK-004 engine/validator

Use /tmp for independent validation where practical.

---

# 42. REGRESSION GATES

Before TASK-004 PASS:

TASK-001 tests must PASS.

TASK-002 tests must PASS.

TASK-003 tests must PASS.

Full test discovery must PASS.

TASK-001 synthetic validator must PASS.

TASK-002 policy validator must PASS.

TASK-003 recovery validator must PASS.

TASK-004 validator must PASS.

No accepted behavior may regress.

---

# 43. STATIC SCOPE CHECK

Search executable TASK-004 implementation for accidental inclusion of:

GreenNode
AgentBase
LLM
OpenAI
Anthropic
Gemini
DeepSeek
LightGBM
XGBoost
machine learning
WAIT_SELF_CURE
PTP_RECOVERY
recommended_channel
recommended_when
AEV
ROI
Precision@
Recall@
AUC
expected_recovery
recovery_probability

Do not fail solely because terms appear in:

TASK files
spec documentation
tests asserting absence
comments describing forbidden scope

Fail if executable TASK-004 implementation performs those capabilities.

---

# 44. GOLDEN-SPECIFIC LOGIC CHECK

Production evaluation code must not contain behavior such as:

if cif == GOLDEN_G01
if cif == GOLDEN_G02
if scenario == G01

except code whose sole purpose is:

HERO report selection
validator scenario selection

Golden identity must never change:

ranking
movement
statistics
score
factor ordering

Rule:

EVAL-NO-GOLDEN-HACK-001

---

# 45. PRECHECK

Before coding, return internally or visibly:

# TASK-004 PRECHECK

## GIT BASELINE

commit:
working_tree:
docs_spec_drift:

## ACCEPTED CHECKPOINTS

TASK-001:
TASK-002:
TASK-003:

## INPUT CONTRACT

baseline ranking:
Recovery ranking:
portfolio size:
authoritative fields:

## EVALUATION FORMULAS

rank_delta:
normalized_rank_delta:
Top-K:
overlap:
displacement:
Spearman:
movement factors:

## FORBIDDEN CLAIMS

Confirm TASK-004 will not implement:

recovery uplift
payment probability
cure probability
Precision/Recall/AUC
financial value
AEV
ROI
ML
LLM
treatment
channel
when

## BLOCKERS

NONE

or exact blocker list.

If an undefined business assumption is required:

STOP BEFORE CODING.

---

# 46. IMPLEMENTATION GATES

GATE T4-01 — Repository baseline

PASS when:
- accepted TASK-003 commit exists;
- working tree clean before implementation;
- docs/spec-v1 unchanged.

GATE T4-02 — Evaluation formulas

PASS when:
- all formulas come directly from TASK-004;
- no new business score or outcome label exists.

GATE T4-03 — Portfolio completeness

PASS when:
- 3,000 CIF evaluated;
- no duplicates;
- complete baseline/recovery ranks.

GATE T4-04 — Immutability

PASS when:
- zero TASK-002 authoritative mismatches;
- zero TASK-003 authoritative mismatches.

GATE T4-05 — HERO comparison

PASS when:
- G01 baseline ahead of G02;
- G02 Recovery ahead of G01;
- G01 DEMOTED;
- G02 PROMOTED.

GATE T4-06 — Top-K

PASS when:
- Top10/50/100 independently validated;
- displacement counts balance.

GATE T4-07 — Correlation

PASS when:
- Spearman independently reproduced;
- deterministic.

GATE T4-08 — Evidence

PASS when:
- movement factors are structured;
- no LLM text;
- no unsupported causal claims.

GATE T4-09 — No fake outcome

PASS when:
- no Precision/Recall/AUC;
- no recovery uplift;
- no expected recovery;
- no ROI/AEV.

GATE T4-10 — Regression

PASS when:
- TASK-001/002/003/full suite PASS.

GATE T4-11 — Determinism

PASS when:
- repeated evaluation outputs are identical.

GATE T4-12 — Scope

PASS when:
- no TASK-005+ capability implemented.

---

# 47. GIT RULE

Do NOT automatically commit implementation.

At end run:

git status --short
git diff --stat
git diff --check
git diff -- docs/spec-v1

TASK-004 implementation must remain uncommitted until independent audit.

---

# 48. REQUIRED FINAL REPORT

Return exactly:

# TASK-004 RESULT

PASS
or
FAIL

## BASELINE

Git commit before implementation:
Working tree before implementation:
Accepted checkpoints:

## PRECHECK RESULT

Evaluation contract:
Business assumptions required:
Scope:

## FILES CREATED / MODIFIED

Modified:
Created:
Generated:
docs/spec-v1 modified:
Git commit created:

## EVALUATION RULES IMPLEMENTED

List:

EVAL-MOVE-001
EVAL-MOVE-002
EVAL-MOVE-003
EVAL-TOPK-001
EVAL-TOPK-002
EVAL-TOPK-003
EVAL-CORR-001
EVAL-EXPLAIN-001
EVAL-EXPLAIN-002
EVAL-EVIDENCE-001
EVAL-ROUTE-001
EVAL-STATS-001
EVAL-STATS-002
EVAL-HERO-G01
EVAL-HERO-G02
EVAL-HERO-COMPARE-001
EVAL-GOLDEN-001
EVAL-NO-OUTCOME-001
EVAL-NO-AEV-001
EVAL-NO-NEW-SCORE-001
EVAL-IMMUTABILITY-001
EVAL-DETERMINISM-001
EVAL-NUMERIC-001
EVAL-NO-GOLDEN-HACK-001

## PORTFOLIO RESULTS

CIF count:
Promoted:
Demoted:
Unchanged:

minimum rank_delta:
maximum rank_delta:
mean absolute rank movement:

Spearman correlation:

## TOP-K RESULTS

Top10:
baseline/recovery overlap:
overlap ratio:
promoted into Recovery Top10:
demoted from Baseline Top10:

Top50:
baseline/recovery overlap:
overlap ratio:
promoted into Recovery Top50:
demoted from Baseline Top50:

Top100:
baseline/recovery overlap:
overlap ratio:
promoted into Recovery Top100:
demoted from Baseline Top100:

## HERO COMPARISON

G01:
baseline rank:
recovery rank:
rank delta:
movement:
score:
primary factors:
route:

G02:
baseline rank:
recovery rank:
rank delta:
movement:
score:
primary factors:
route:

Baseline winner:
Recovery Opportunity winner:
PASS/FAIL:

## CRITICAL ASSERTIONS

G01 demoted:
G02 promoted:
G02 Recovery ahead of G01:
G07 route preserved:
G08 route preserved:
G19 boundary preserved:
G20 aggregation preserved:
TASK-002 mismatch count:
TASK-003 mismatch count:
forbidden outcome metrics:
AEV/ROI:
Golden-specific ranking logic:

## GOLDEN RESULTS

G01:
G02:
...
G20:

Use only:

PASS
FAIL
NOT_APPLICABLE

## OUTPUT ARTIFACTS

List generated artifacts and record counts.

## DETERMINISM

Run A digest:
Run B digest:
Result:

## TEST RESULTS

List exact commands and results.

TASK-001:
TASK-002:
TASK-003:
TASK-004:
Full suite:

## DATA QUALITY

Synthetic statistic label:
Unique CIF:
Unique baseline ranks:
Unique Recovery ranks:

## SPEC DEVIATIONS

NONE
or details.

## ASSUMPTIONS

NONE
or explicitly authorized technical assumptions only.

## UNRESOLVED BUSINESS QUESTIONS

NONE
or exact blockers.

## ACCEPTED TASK REGRESSIONS

NONE
or details.

## OUT-OF-SCOPE CONFIRMATION

TASK-004 did NOT implement:

- score changes
- routing changes
- treatment optimization
- channel recommendation
- best-time recommendation
- GreenNode
- AgentBase
- LLM
- ML
- frontend
- AEV
- ROI
- real-world recovery prediction

## GIT STATUS

git status --short:

git diff --stat:

git diff --check:

git diff -- docs/spec-v1:

## NEXT GATE

READY FOR TASK-005 REVIEW

or

NOT READY FOR TASK-005

Do not implement TASK-005.

STOP.

---

# 49. DEFINITION OF DONE

TASK-004 is DONE only when:

1. Baseline vs Recovery ranking comparison is deterministic.
2. Every one of 3,000 CIFs has rank movement.
3. Top10/50/100 comparisons are independently validated.
4. Spearman correlation is independently validated.
5. G01/G02 HERO inversion is proven from accepted engine outputs.
6. TASK-002/TASK-003 authoritative fields are unchanged.
7. Structured movement evidence exists.
8. No fake outcome/performance metric exists.
9. No AEV/ROI exists.
10. All regression tests pass.
11. Independent audit accepts TASK-004.
12. Implementation is committed only after independent audit acceptance.

END OF TASK-004