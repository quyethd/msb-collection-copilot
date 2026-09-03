# TASK-007A — DETERMINISTIC NEXT BEST ACTION ENGINE

## STATUS

AUTHORIZED ONLY AFTER TASK-006 ACCEPTANCE AND COMMIT.

TASK-001 = ACCEPTED
TASK-002 = ACCEPTED
TASK-003 = ACCEPTED
TASK-004 = ACCEPTED
TASK-005 = ACCEPTED
TASK-006 = ACCEPTED

TASK-007A implementation MUST remain uncommitted until independent audit ACCEPT.

---

# 1. PURPOSE

Build the deterministic Next Best Action engine for Collection Decision Copilot.

The engine converts already accepted deterministic facts into an
authorized collection recommendation.

It answers:

WHAT should happen?
HOW should it happen?
WHEN should it happen?
WHY did the deterministic engine choose it?
WHAT is the operational objective?

The engine MUST NOT use an LLM.

The engine MUST NOT predict payment probability.

The engine MUST NOT change:

- routing;
- suppression;
- Recovery Opportunity Score;
- component scores;
- ranks;
- source facts.

TASK-007A exists specifically so the future GreenNode Agent cannot
invent treatment/channel/time.

---

# 2. ARCHITECTURE

Accepted architecture:

TASK-001 Synthetic Data
        ?
TASK-002 Policy / Routing
        ?
TASK-003 Recovery Opportunity
        ?
TASK-004 Evaluation
        ?
TASK-005 Decision Context
        ?
TASK-006 Read-only Tool Layer
        ?
TASK-007A Deterministic Next Best Action
        ?
TASK-007B GreenNode Collection Decision Agent

Authority boundary:

BUSINESS DECISION
=
TASK-007A

LANGUAGE / EXPLANATION / ORCHESTRATION
=
TASK-007B

The future Agent may explain a TASK-007A decision.

It may NOT replace it.

Rule:

NBA-AUTHORITY-001

---

# 3. REQUIRED READING

Before writing code, read completely:

TASK-007A.md
TASK-006.md
TASK-005.md
TASK-004.md
TASK-003.md
TASK-003_SCORING_CONTRACT.md
TASK-002.md
TASK-001.md

and:

docs/spec-v1/PRODUCT_SPEC_V1.md
docs/spec-v1/RULE_BASE_V1.md
docs/spec-v1/SYNTHETIC_DATA_SPEC.md
docs/spec-v1/GOLDEN_SCENARIOS_V1.md
docs/spec-v1/README.md
docs/spec-v1/UBUNTU_BUILD_HANDOFF.md

Inspect accepted implementations:

src/msb_synthetic/
src/msb_policy/
src/msb_recovery/
src/msb_evaluation/
src/msb_context/
src/msb_tools/

and all accepted tests.

Repository specifications are authoritative.

Do NOT use conversation summaries as business-rule authority.

---

# 4. SPEC PRECEDENCE

Business semantics precedence:

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
TASK-003_SCORING_CONTRACT.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

TASK-002 is authoritative for policy/routing.

TASK-003 is authoritative for Recovery Opportunity scoring.

TASK-005 is authoritative for Decision Context.

TASK-006 is authoritative for tool interfaces.

TASK-007A may only implement recommendation semantics already authorized
by the specifications.

Rule:

NBA-SPEC-001

---

# 5. CRITICAL PRECHECK — DO NOT INVENT BUSINESS RULES

Before coding, construct a Decision Contract Matrix from the repository.

For every candidate:

TREATMENT
CHANNEL
WHEN
OBJECTIVE

identify:

- exact specification file;
- exact rule/scenario;
- required inputs;
- precedence;
- expected output.

Do NOT code until this matrix is complete enough to produce an
authorized deterministic recommendation.

If the repository specifies vocabulary but does NOT specify sufficient
conditions/precedence for choosing a value:

STOP.

Return:

TASK-007A BLOCKED — NEXT BEST ACTION BUSINESS RULES INCOMPLETE

Then list exactly:

DEFINED:
UNDEFINED:
AMBIGUOUS:
CONFLICTING:

Do NOT fill gaps with industry knowledge.

Do NOT infer rules merely because they seem reasonable.

Do NOT ask an LLM to decide them.

Rule:

NBA-CONTRACT-GATE-001

---

# 6. ALLOWED OUTPUT VOCABULARY

Candidate treatment vocabulary already defined by product specifications
must be verified during precheck.

Expected existing vocabulary includes:

WAIT
REMIND
CONTACT
PTP_FOLLOW_UP
PTP_RECOVERY
PARTIAL_PAYMENT
CALLBACK
ESCALATE
VERIFY_CONTACT

Do NOT assume every value is authorized merely because it appears here.

Repository specs remain authoritative.

No new treatment value may be introduced.

Rule:

NBA-TREATMENT-VOCAB-001

---

# 7. CHANNEL VOCABULARY

Candidate existing channels:

CALL
SMS
ZALO
EMAIL
FIELD
NONE

Verify against repository specifications.

Do NOT add:

WHATSAPP
MESSENGER
PUSH
ROBOCALL

or another channel without explicit authorization.

Rule:

NBA-CHANNEL-VOCAB-001

---

# 8. OBJECTIVE VOCABULARY

Candidate existing objectives:

PAYMENT
PTP
PTP_KEEP
CALLBACK
CONTACT_VERIFICATION
INFORMATION_COLLECTION

Verify against repository specifications.

No new objective without authorization.

Rule:

NBA-OBJECTIVE-VOCAB-001

---

# 9. WHEN MODEL

TASK-007A MUST NOT invent a fake exact contact time.

The WHEN output may only use deterministic timing semantics explicitly
supported by accepted source/spec rules.

Possible representations may include:

NOW
TODAY
ON_SOURCE_NEXT_ACTION_DATE
ON_PTP_DATE
WAIT

or another repository-authorized representation.

DO NOT adopt these values automatically.

Verify them during the Decision Contract Gate.

If exact time-of-day recommendation is not authorized:

do NOT implement exact best-contact-time.

Rule:

NBA-WHEN-001

---

# 10. ROUTING VS TREATMENT

Routing and treatment are different.

Examples conceptually:

final_route = CALL

does NOT automatically mean:

treatment = CONTACT

unless an authorized rule explicitly states that.

Similarly:

final_route = CBS

does NOT automatically mean:

treatment = REMIND.

TASK-007A must preserve this distinction.

Rule:

NBA-ROUTE-TREATMENT-001

---

# 11. POLICY AUTHORITY

TASK-007A receives accepted:

base_route
challenge_override_route
final_route
hard_suppressed

It MUST NOT recalculate them.

It MUST NOT override them.

Rule:

NBA-POLICY-IMMUTABILITY-001

---

# 12. HARD SUPPRESSION PRECEDENCE

Hard suppression precedes recommendation logic.

If accepted policy says:

hard_suppressed = true

TASK-007A must not generate an unauthorized active contact action.

Exact suppressed treatment/channel/when/objective behavior MUST come
from repository-authorized rules.

If that behavior is not defined:

BLOCK TASK-007A.

Do not invent:

WAIT/NONE

merely because it appears intuitive.

Rule:

NBA-SUPPRESSION-001

---

# 13. SOURCE NEXT ACTION

Source facts:

source_next_action_date
source_next_operation_channel

are factual employee/source data.

They are NOT automatically TASK-007A recommendations.

TASK-007A may use them only according to explicitly authorized rules.

The output must distinguish:

source_next_action

from:

recommended_action.

Rule:

NBA-SOURCE-ACTION-001

---

# 14. PTP PRECEDENCE

PTP facts may include:

OPEN
KEPT
PARTIAL
BROKEN
EXPIRED
CANCELLED

plus:

promise_date
promise_amount
actual_paid_amount
human_assessed_ability
next_action_date
next_channel

Exact PTP-to-treatment rules MUST be sourced from specifications.

Do not infer:

BROKEN => PTP_RECOVERY

unless repository rule explicitly authorizes it.

Do not infer:

PARTIAL => PARTIAL_PAYMENT

solely from vocabulary naming.

Rule:

NBA-PTP-001

---

# 15. SELF-CURE

Self-cure treatment is safety-sensitive from a business correctness
perspective.

Good cashflow alone MUST NOT imply WAIT/self-cure.

Any WAIT/self-cure recommendation must satisfy every condition defined
by the repository specification.

If complete self-cure conditions are not defined:

do not invent them.

BLOCK that recommendation rule.

Rule:

NBA-SELF-CURE-001

---

# 16. RECOVERY SCORE ROLE

Recovery Opportunity Score prioritizes opportunity.

It does NOT by itself determine treatment.

No rule of the form:

score >= X => CALL

score >= Y => WAIT

may be invented.

Score may influence treatment only if an explicit authorized rule says
so.

Rule:

NBA-SCORE-001

---

# 17. HUMAN PTP ABILITY

payment_ptp_ability:

CERTAIN
HIGH
MEDIUM
LOW
VERY_LOW

is human-assessed evidence.

It MUST NOT be represented as model confidence.

It MUST NOT become probability.

Rule:

NBA-HUMAN-ASSESSMENT-001

---

# 18. CONTACTABILITY

Technical call history may support deterministic recommendation only
through explicitly authorized rules.

Technical:

Success

does not mean:

customer agreed
PTP
payment
recovery success.

Rule:

NBA-CONTACT-BOUNDARY-001

---

# 19. DECISION OUTPUT

Once business contract is fully authorized, each decision should have a
stable typed representation.

Conceptual shape:

{
  "decision_version": "1.0",
  "cif": "...",
  "reference_date": "2026-08-28",

  "policy": {
    "final_route": "...",
    "hard_suppressed": false
  },

  "recommendation": {
    "treatment": "...",
    "channel": "...",
    "when": {...},
    "objective": "..."
  },

  "reason_codes": [...],

  "evidence_refs": [...],

  "decision_trace": [...],

  "provenance": {
    "synthetic_data": true,
    "synthetic_label": "SYNTHETIC PROTOTYPE DATA"
  }
}

Exact schema must follow authorized rules and existing data semantics.

Rule:

NBA-OUTPUT-001

---

# 20. REASON CODES

TASK-007A must produce deterministic reason codes.

Reason codes are NOT natural-language AI explanations.

Example conceptual forms:

PTP_BROKEN
PTP_DUE
PARTIAL_PAYMENT_PRESENT
RECENT_INFLOW
SOURCE_CALLBACK_DUE
CONTACT_UNAVAILABLE
HARD_SUPPRESSED

These examples are NOT automatically authorized production codes.

Derive actual reason codes from the authorized Decision Contract Matrix.

Every reason code must map to:

rule_id
input evidence
decision effect

Rule:

NBA-REASON-001

---

# 21. DECISION TRACE

Every recommendation must expose a deterministic trace.

Conceptual:

[
  {
    "rule_id": "...",
    "matched": true,
    "effect": "..."
  }
]

The trace must make it possible to answer:

Why was this treatment selected?

Why this channel?

Why this timing?

Why this objective?

No chain-of-thought.

No LLM reasoning.

Rule:

NBA-TRACE-001

---

# 22. EVIDENCE REFERENCES

Recommendation must point back to accepted structured evidence.

Examples:

policy rule IDs
PTP source IDs
cashflow evidence IDs
call IDs
operation IDs

where available and authorized.

Do not copy or fabricate nonexistent IDs.

Rule:

NBA-EVIDENCE-001

---

# 23. DECISION PRECEDENCE

Implement only the precedence explicitly authorized by repository rules.

Global architecture precedence remains:

1. HARD POLICY
2. ROUTING
3. HARD SUPPRESSION
4. PTP / SOURCE NEXT ACTION
5. RECOVERY OPPORTUNITY
6. TREATMENT
7. CHANNEL
8. WHEN
9. EXPLANATION

TASK-007A owns deterministic stages:

6
7
8

and operational objective/reason codes where authorized.

TASK-007A must not modify stages 1–5.

Rule:

NBA-PRECEDENCE-001

---

# 24. ONE FINAL RECOMMENDATION

For V1 each CIF should resolve to one deterministic recommendation
only if specifications authorize a unique result.

No unordered set of possible actions.

No:

"CALL or SMS"

No:

"probably REMIND"

No:

"consider WAIT"

If two rules conflict and precedence is undefined:

BLOCK.

Rule:

NBA-UNIQUE-001

---

# 25. NO CONFIDENCE SCORE

TASK-007A MUST NOT create:

confidence
confidence_score
certainty
probability

Rule:

NBA-NO-CONFIDENCE-001

---

# 26. NO EXPECTED RECOVERY

TASK-007A MUST NOT create:

expected_recovery
expected_payment
expected_value
expected_collection
recovery_probability
payment_probability
cure_probability

Rule:

NBA-NO-PREDICT-001

---

# 27. NO AI TEXT

TASK-007A outputs structured deterministic facts only.

No:

AI explanation
generated recommendation narrative
LLM summary
chain-of-thought

Rule:

NBA-NO-AI-TEXT-001

---

# 28. DETERMINISTIC ENGINE

Same:

Decision Context
+
authorized rules
+
reference date

must always produce identical recommendation.

No randomness.

No system clock.

No external network.

No LLM.

Rule:

NBA-DETERMINISM-001

---

# 29. REFERENCE DATE

Use accepted deterministic reference date from source context/manifest.

V1 expected:

2026-08-28

Do NOT use:

date.today()
datetime.now()
system timezone

for business decisions.

Rule:

NBA-DATE-001

---

# 30. INPUT AUTHORITY

Preferred input:

TASK-005 Decision Context.

TASK-007A must not independently reconstruct:

policy
score
rank
cashflow aggregates
PTP state

if TASK-005 already exposes them.

Rule:

NBA-INPUT-001

---

# 31. TOOL RELATIONSHIP

TASK-007A is a deterministic business engine.

TASK-006 tools remain read-only access surfaces.

Do NOT implement recommendation by asking a tool-calling LLM.

TASK-007A may use the same underlying accepted repository/context
access layer.

Rule:

NBA-TOOLS-001

---

# 32. REQUIRED PACKAGE

Only after Decision Contract Gate PASS.

Preferred:

src/msb_nba/

Suggested:

__init__.py
models.py
rules.py
engine.py
io.py
cli.py
validate.py

Keep the engine explicit and auditable.

Avoid generic rules engines unless necessary.

No Drools.

No ML framework.

No workflow engine.

---

# 33. RULE REPRESENTATION

Each production decision rule must have a stable rule ID.

Conceptually:

NBA-xxx-001

Each rule should identify:

priority
conditions
effect
reason_code

No anonymous if/else containing undocumented business semantics.

Rule:

NBA-RULE-ID-001

---

# 34. NO GOLDEN-SPECIFIC PRODUCTION LOGIC

Never write:

if cif == "GOLDEN_G04"

or equivalent.

Golden scenarios validate general rules.

They do not define special customer behavior.

Rule:

NBA-NO-GOLDEN-HACK-001

---

# 35. CLI

Only after contract gate passes.

Preferred:

PYTHONPATH=src python -m msb_nba.cli \
  --input build/decision-context \
  --output build/next-best-action

Expected artifacts:

next_best_action.jsonl
golden_nba_validation.json
nba_manifest.json

Exact naming may follow repository conventions.

---

# 36. OUTPUT CARDinality

If complete authorized rules cover all applicable CIFs:

one decision per applicable CIF.

Do not fabricate a recommendation merely to reach 3,000.

During precheck determine:

total CIF
eligible CIF
covered CIF
uncovered CIF

If uncovered cases exist because business semantics are missing:

BLOCK.

Report them by rule/category.

Rule:

NBA-COVERAGE-001

---

# 37. COVERAGE GATE

Before production implementation, enumerate all distinct relevant
decision-state combinations present in the 3,000-CIF synthetic dataset.

At minimum consider accepted dimensions relevant to authorized rules:

final_route
hard_suppressed
PTP state
source next action state
contact evidence state
cashflow evidence availability
recovery evidence

Do not create a combinatorial explosion unnecessarily.

Goal:

prove authorized rules cover actual V1 dataset states.

Report:

distinct states:
covered:
uncovered:
ambiguous:

Required before implementation:

uncovered = 0
ambiguous = 0

unless repository explicitly defines a safe deterministic fallback.

Rule:

NBA-COVERAGE-GATE-001

---

# 38. FALLBACK RULE

No catch-all business fallback may be invented.

Do NOT write:

else => CONTACT

or:

else => WAIT

unless explicitly authorized.

If no rule matches:

return a typed internal:

UNRESOLVED_DECISION

during development/validation.

Production Definition of Done requires:

UNRESOLVED_DECISION = 0

for the intended V1 population.

Rule:

NBA-FALLBACK-001

---

# 39. GOLDEN SCENARIOS

After the contract is proven complete, TASK-007A must validate every
Golden scenario for which an expected recommendation is explicitly
specified.

At minimum inspect:

G01
G02
G03
G04
G05
G06
G07
G08
G09
G10
G11
G12
G13
G14
G15
G16
G17
G18
G19
G20

Do NOT assume recommendation expectations for a Golden scenario merely
because earlier stages validated it.

If Golden specifies facts but not expected treatment/channel/when:

mark:

NOT_APPLICABLE_TO_NBA_EXPECTATION

Do not invent expected output.

Rule:

NBA-GOLDEN-001

---

# 40. HERO SCENARIOS

The five HERO scenarios are especially important for eventual demo.

Verify whether specs explicitly authorize NBA behavior for:

HERO 1:
high debt/high DPD but low opportunity

HERO 2:
moderate debt + recent cashflow + PTP due

HERO 3:
self-cure / WAIT case

HERO 4:
broken PTP + recent inflow

HERO 5:
What-if

TASK-007A must NOT implement What-if mutation.

HERO 5 belongs to later simulation work.

If HERO 1–4 expected treatment semantics are incomplete:

report blocker.

---

# 41. G04 SAFETY CHECK

Do not automatically turn G04 into:

PTP_RECOVERY

unless an exact authorized rule supports it.

The fact pattern:

BROKEN PTP
recent inflow
successful technical contact

is evidence.

It is not itself permission to invent a treatment rule.

Rule:

NBA-G04-001

---

# 42. G19 SAFETY CHECK

G19 has technical Success but no PTP.

TASK-007A must not infer willingness from technical call success.

Any treatment must follow other authorized rules.

Rule:

NBA-G19-001

---

# 43. ROUTE OVERRIDE GOLDENS

G07 and G08 must preserve final accepted route.

TASK-007A recommendation may never undo challenge routing.

Rule:

NBA-ROUTE-GOLDEN-001

---

# 44. BUSINESS IMMUTABILITY

For every CIF compare before/after:

policy
cashflow
payment
PTP
contact
Recovery score
component scores
baseline rank
Recovery rank

Required mutations:

0.

Rule:

NBA-IMMUTABILITY-001

---

# 45. SYNTHETIC PROVENANCE

Every persisted recommendation must retain:

synthetic_data = true
synthetic_label = "SYNTHETIC PROTOTYPE DATA"
reference_date = accepted deterministic date

Rule:

NBA-PROVENANCE-001

---

# 46. SECURITY / READ-ONLY

TASK-007A must not:

write accepted source files
modify Decision Context
execute shell from input
execute arbitrary Python
accept SQL
accept arbitrary file path from business input
make network calls

Rule:

NBA-SECURITY-001

---

# 47. TEST REQUIREMENTS

Do NOT write recommendation tests until Decision Contract Gate passes.

After gate PASS, tests must cover:

- exact rule precedence;
- every treatment rule;
- every channel rule;
- every when rule;
- every objective rule;
- every fallback/unresolved path;
- hard suppression;
- routing immutability;
- PTP states;
- missing evidence;
- technical/business boundary;
- self-cure exact conditions;
- source-next-action distinction;
- Golden scenarios with explicit NBA expectations;
- deterministic output;
- no system clock;
- no source mutation;
- no unauthorized vocabulary;
- no future prediction fields;
- no LLM/network;
- no Golden-specific branches.

Test expected values must come from specifications, not from the engine
under test.

Rule:

NBA-TEST-001

---

# 48. MUTATION / NEGATIVE TESTS

For every high-impact rule, test near-boundary negative cases.

Example methodology:

If rule requires:

A AND B AND C

test:

A+B+C => matches
not A+B+C => no match
A+not B+C => no match
A+B+not C => no match

This is especially mandatory for:

self-cure
broken PTP
partial payment
callback
hard suppression

where those rules are actually authorized.

Rule:

NBA-NEGATIVE-TEST-001

---

# 49. DECISION MATRIX ARTIFACT

Before coding business rules create:

build/next-best-action/decision_contract_matrix.json

or equivalent deterministic artifact.

It must contain only repository-authorized semantics:

rule_id
source_spec
priority
conditions
treatment
channel
when
objective
reason_codes

If contract is incomplete, produce an audit/report instead and STOP.

Do not create invented rows to make matrix complete.

Rule:

NBA-MATRIX-001

---

# 50. PRECHECK OUTPUT

Return before coding:

# TASK-007A PRECHECK

## GIT

HEAD:
TASK-006 accepted commit:
working tree:
spec drift:

## REQUIRED SPECS

RULE_BASE:
GOLDEN_SCENARIOS:
PRODUCT_SPEC:
TASK-005:
TASK-006:

## VOCABULARY

Authorized treatments:
Authorized channels:
Authorized objectives:
Authorized when values:

## DECISION CONTRACT MATRIX

For every discovered rule:

RULE ID:
SOURCE:
PRECEDENCE:
CONDITIONS:
TREATMENT:
CHANNEL:
WHEN:
OBJECTIVE:
REASON CODES:

## HARD SUPPRESSION

Defined:
Exact behavior:

## PTP

OPEN:
KEPT:
PARTIAL:
BROKEN:
EXPIRED:
CANCELLED:

For each state report whether exact NBA behavior is defined.

## SELF-CURE

Exact authorized conditions:
Treatment:
Channel:
When:
Objective:

## SOURCE NEXT ACTION

Exact precedence:
Exact behavior:

## ROUTING

CALL behavior:
CBS behavior:
OTHER behavior:

Do not infer missing behavior.

## GOLDEN NBA EXPECTATIONS

G01:
G02:
...
G20:

Use:

DEFINED
NOT_DEFINED
NOT_APPLICABLE

## HERO NBA EXPECTATIONS

HERO1:
HERO2:
HERO3:
HERO4:
HERO5:

## DATASET STATE COVERAGE

Total CIF:
Distinct relevant states:
Covered states:
Uncovered states:
Ambiguous states:

List uncovered/ambiguous state groups and counts.

## BUSINESS GAPS

List exact missing semantics.

## RESULT

Return exactly one:

TASK-007A PRECHECK PASS — BUSINESS CONTRACT COMPLETE

or

TASK-007A BLOCKED — NEXT BEST ACTION BUSINESS RULES INCOMPLETE

If BLOCKED:

STOP.

DO NOT IMPLEMENT THE ENGINE.

---

# 51. IMPLEMENTATION AUTHORIZATION

The existence of TASK-007A.md does NOT itself authorize Codex to invent
missing recommendation rules.

Implementation is authorized only when:

TASK-007A PRECHECK PASS — BUSINESS CONTRACT COMPLETE

If precheck BLOCKS:

the user/business owner must explicitly authorize the missing rule
contract.

Rule:

NBA-AUTHORIZATION-001

---

# 52. EXPECTED IMPLEMENTATION GATES AFTER PRECHECK PASS

T7A-01 Contract
- matrix complete
- no ambiguity
- no uncovered intended states

T7A-02 Vocabulary
- no unauthorized outputs

T7A-03 Policy
- routing/suppression preserved

T7A-04 Treatment
- exact authorized rules only

T7A-05 Channel
- exact authorized rules only

T7A-06 When
- exact authorized rules only

T7A-07 Objective
- exact authorized rules only

T7A-08 Reasons
- deterministic reason codes

T7A-09 Trace
- rule/evidence trace

T7A-10 Golden
- explicit NBA expectations pass

T7A-11 Coverage
- unresolved = 0 for intended V1 population

T7A-12 Determinism
- identical artifacts

T7A-13 Immutability
- upstream mutation = 0

T7A-14 Scope
- no Agent
- no LLM
- no MaaS
- no deploy
- no What-if
- no AEV/ROI

T7A-15 Regression
- TASK-001?006 all PASS

---

# 53. INDEPENDENT AUDIT REQUIREMENT

TASK-007A must undergo a fresh independent audit.

Auditor must independently reconstruct the Decision Contract Matrix
from repository specifications.

Auditor must NOT trust:

engine rule definitions
engine validator
engine tests
developer report

as business-rule authority.

Required comparison:

SPEC MATRIX
vs
IMPLEMENTED MATRIX

Mismatch count:

0.

This is the central TASK-007A audit.

---

# 54. GIT RULE

Do not commit TASK-007A implementation before independent audit ACCEPT.

After implementation:

git status --short
git diff --stat
git diff --check
git diff -- docs/spec-v1

No TASK-001–006 accepted implementation may be modified without explicit
authorization.

---

# 55. DEFINITION OF DONE

TASK-007A is DONE only when:

1. Repository specs completely authorize V1 NBA behavior.
2. Decision Contract Matrix has no invented semantics.
3. Intended V1 state coverage has no unresolved decisions.
4. Treatment is deterministic.
5. Channel is deterministic.
6. When is deterministic.
7. Objective is deterministic.
8. Reason codes are deterministic.
9. Decision trace is deterministic.
10. Routing is unchanged.
11. Hard suppression is unchanged.
12. Recovery score/ranks are unchanged.
13. Missing evidence is preserved.
14. Technical/business boundary is preserved.
15. No probability/confidence/expected recovery exists.
16. No AI-generated recommendation text exists.
17. No system clock affects decisions.
18. No source mutation occurs.
19. No Golden-specific production logic exists.
20. TASK-001?006 regressions pass.
21. Independent audit reconstructs same rules.
22. Independent audit ACCEPTS.
23. Only then may implementation be committed.

END OF TASK-007A