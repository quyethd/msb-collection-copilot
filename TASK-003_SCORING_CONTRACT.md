# TASK-003A — RECOVERY OPPORTUNITY SCORING CONTRACT V1

## STATUS

LOCKED FOR HACKATHON V1

Classification:

[PROTOTYPE-RULE]

This contract defines deterministic prototype scoring logic for the
MSB Collection Decision Copilot hackathon demonstration.

It is NOT confirmed production MSB collection policy.

It MUST remain configurable and replaceable before any production use.

TASK-003 implementation is authorized to use this contract.

---

# 1. AUTHORITY

For TASK-003 scoring implementation, precedence is:

RULE_BASE_V1.md
>
GOLDEN_SCENARIOS_V1.md
>
TASK-003_SCORING_CONTRACT.md
>
SYNTHETIC_DATA_SPEC.md
>
PRODUCT_SPEC_V1.md

TASK-003_SCORING_CONTRACT.md fills scoring details that the locked
specification intentionally leaves undefined.

It MUST NOT override:

- hard policy;
- routing;
- challenge override;
- PTP status derivation;
- source next-action facts.

TASK-002 PolicyResult remains authoritative for those fields.

---

# 2. REFERENCE DATE

Default prototype reference date:

2026-08-28

All rolling windows are calculated relative to this configured reference date.

Do not use system current time.

For an N-day window:

reference_date - (N - 1) days
through
reference_date

inclusive.

Examples:

3-day:
2026-08-26 through 2026-08-28

7-day:
2026-08-22 through 2026-08-28

30-day:
2026-07-30 through 2026-08-28

---

# 3. SCORE STRUCTURE

Business Urgency        20
Ability to Pay          25
Willingness to Pay      20
Contactability          15
Timing Opportunity      15
Strategic Adjustment     5
                       ---
Maximum                100

Total:

recovery_opportunity_score =
    business_urgency_score
  + ability_to_pay_score
  + willingness_to_pay_score
  + contactability_score
  + timing_opportunity_score
  + strategic_adjustment_score

Each component MUST remain within:

0 <= score <= component maximum

No negative final component scores.

No hidden multiplier.

No route multiplier.

No LLM adjustment.

---

# 4. BUSINESS URGENCY — MAX 20

Business Urgency consists of:

A. MAX DPD                     max 12
B. Outstanding percentile      max 4
C. PTP urgency                 max 4

Total                          max 20

---

## 4.1 MAX DPD — MAX 12

Use TASK-002:

max_dpd_cif

Points:

DPD <= 0
? 0

DPD 1–4
? 2

DPD 5–14
? 5

DPD 15–29
? 8

DPD 30–59
? 10

DPD >= 60
? 12

Rule:

SCORE-URG-DPD-001

---

## 4.2 OUTSTANDING PERCENTILE — MAX 4

Use:

total_outstanding_cif

Calculate percentile across the entire evaluated portfolio.

Prototype empirical percentile:

outstanding_percentile =
    count(CIF where total_outstanding_cif <= current CIF total)
    / total CIF count

Ties therefore receive the same percentile.

Points:

percentile < 0.50
? 0

0.50 <= percentile < 0.75
? 1

0.75 <= percentile < 0.90
? 2

0.90 <= percentile < 0.97
? 3

percentile >= 0.97
? 4

Rule:

SCORE-URG-OUT-001

Raw debt must not contribute anywhere else solely because it is large.

---

## 4.3 PTP URGENCY — MAX 4

Use TASK-002 PTP status and promise date.

BROKEN
? 4

PARTIAL AND promise_date <= reference_date
? 3

OPEN AND promise_date <= reference_date + 1 day
? 2

OPEN AND promise_date <= reference_date + 3 days
? 1

KEPT
? 0

No applicable PTP
? 0

Rule:

SCORE-URG-PTP-001

---

# 5. ABILITY TO PAY — MAX 25

Ability consists of:

A. inflow_7d                    max 8
B. net_cashflow_30d             max 5
C. income-source signal         max 4
D. cashflow stability           max 4
E. liquidity_to_due_ratio       max 4

Total                           max 25

Cashflow must be derived from actual cashflow_transaction rows.

---

## 5.1 INFLOW 7 DAYS — MAX 8

Derived:

inflow_7d =
SUM(amount where direction = IN within 7-day window)

Points:

0
? 0

0 < inflow_7d < 5,000,000
? 1

5,000,000 <= inflow_7d < 15,000,000
? 3

15,000,000 <= inflow_7d < 30,000,000
? 6

inflow_7d >= 30,000,000
? 8

Rule:

SCORE-ABL-INFLOW7-001

---

## 5.2 NET CASHFLOW 30 DAYS — MAX 5

Derived:

inflow_30d =
SUM(IN transactions within 30 days)

outflow_30d =
SUM(OUT transactions within 30 days)

net_cashflow_30d =
inflow_30d - outflow_30d

Points:

net_cashflow_30d <= 0
? 0

0 < net_cashflow_30d < 10,000,000
? 2

10,000,000 <= net_cashflow_30d < 30,000,000
? 4

net_cashflow_30d >= 30,000,000
? 5

Rule:

SCORE-ABL-NET30-001

---

## 5.3 INCOME SOURCE SIGNAL — MAX 4

Within the last 30 days inspect IN transactions.

Structured source types:

SALARY
BUSINESS_INCOME

If both SALARY and BUSINESS_INCOME are present:
? 4

If either SALARY OR BUSINESS_INCOME is present:
? 3

If neither:
? 0

Rule:

SCORE-ABL-INCOME-001

Do not infer salary/business income from transaction text.

---

## 5.4 CASHFLOW STABILITY — MAX 4

Use three consecutive 30-day windows:

W1 = days 0–29 before/reference date
W2 = days 30–59 before/reference date
W3 = days 60–89 before/reference date

For each window calculate:

net_cashflow_window =
inflow - outflow

A window is positive when:

net_cashflow_window > 0

Points:

3 positive windows
? 4

2 positive windows
? 3

1 positive window
? 1

0 positive windows
? 0

Rule:

SCORE-ABL-STABILITY-001

---

## 5.5 LIQUIDITY TO DUE — MAX 4

Applicable only when a selected/latest applicable PTP has:

promise_amount > 0

Calculate:

liquidity_to_due_ratio =
inflow_7d / promise_amount

If there is no applicable PTP or promise_amount <= 0:

feature = unavailable
points = 0

This is MISSING EVIDENCE, not negative evidence.

Points when available:

ratio <= 0
? 0

0 < ratio < 0.5
? 1

0.5 <= ratio < 1
? 2

1 <= ratio < 2
? 3

ratio >= 2
? 4

Rule:

SCORE-ABL-LIQUIDITY-001

---

# 6. WILLINGNESS TO PAY — MAX 20

Willingness consists of:

A. PTP state                         max 8
B. PTP fulfillment ratio             max 4
C. payment-after-contact             max 4
D. employee PTP ability signal       max 4

Total                                max 20

Technical call Success must NOT itself add Willingness points.

---

## 6.1 PTP STATE — MAX 8

KEPT
? 8

PARTIAL
? 5

OPEN
? 3

BROKEN
? 0

No PTP evidence
? 0

Rule:

SCORE-WIL-PTPSTATE-001

---

## 6.2 PTP FULFILLMENT — MAX 4

Applicable only if:

promise_amount > 0

Calculate:

ptp_fulfillment_ratio =
actual_paid_amount / promise_amount

Points:

ratio >= 1
? 4

0.5 <= ratio < 1
? 3

0 < ratio < 0.5
? 1

ratio = 0
? 0

No applicable PTP:
? feature unavailable
? points 0

Rule:

SCORE-WIL-FULFILL-001

---

## 6.3 PAYMENT AFTER CONTACT — MAX 4

Inspect successful OUTBOUND calls in the 30-day window.

Technical success means:

call_history.status = Success

This technical event may only be used as a temporal anchor.

It MUST NOT itself count as willingness.

Find positive payment events after a successful outbound call.

If payment occurs within 3 calendar days after a successful call:
? 4

Else if payment occurs within 7 calendar days:
? 2

Else:
? 0

Only actual positive payment amount qualifies.

Rule:

SCORE-WIL-PAYAFTERCONTACT-001

---

## 6.4 EMPLOYEE PTP ABILITY — MAX 4

payment_ptp_ability is HUMAN ASSESSMENT.

Prototype mapping:

CERTAIN
? 4

HIGH
? 3

MEDIUM
? 1

LOW
? 0

VERY_LOW
? 0

Missing
? 0 and mark unavailable

Rule:

SCORE-WIL-HUMANABILITY-001

This signal must NEVER be presented as model probability or ground truth.

---

# 7. CONTACTABILITY — MAX 15

Contactability consists of:

A. technical call success rate        max 6
B. repeated UTC evidence              max 4
C. valid-contact evidence             max 3
D. successful-contact recency         max 2

Total                                 max 15

---

## 7.1 TECHNICAL SUCCESS RATE — MAX 6

Within 30 days:

outbound_attempts_30d =
count(call_history where call_type = OUTBOUND/OUT)

successful_calls_30d =
count(those attempts where status = Success)

success_rate_30d =
successful_calls_30d / outbound_attempts_30d

If no outbound attempts:

feature unavailable
points 0

Otherwise:

rate >= 0.70
? 6

0.40 <= rate < 0.70
? 4

0.20 <= rate < 0.40
? 2

0 < rate < 0.20
? 1

rate = 0
? 0

Rule:

SCORE-CON-SUCCESSRATE-001

---

## 7.2 UTC EVIDENCE — MAX 4

Count business outcomes:

operation_result = UTC

within the last 30 days.

If operation-history evidence is completely unavailable:

points 0
mark unavailable

Otherwise:

UTC count = 0
? 4

UTC count = 1
? 3

UTC count = 2
? 2

UTC count = 3
? 1

UTC count >= 4
? 0

Rule:

SCORE-CON-UTC-001

UTC affects Contactability only.

It MUST NOT automatically reduce Willingness.

---

## 7.3 VALID CONTACT EVIDENCE — MAX 3

Inspect business operation outcomes within 30 days.

If any:

NIN

exists:
? 0

Else if there is any call or operation contact evidence:
? 3

Else:
? 0 and mark evidence unavailable

Rule:

SCORE-CON-VALIDCONTACT-001

THIRT does not automatically invalidate the phone number.

---

## 7.4 SUCCESSFUL CONTACT RECENCY — MAX 2

Use latest successful OUTBOUND technical call.

days_since_last_successful_call <= 7
? 2

8–30 days
? 1

No successful call within 30 days
? 0

Rule:

SCORE-CON-RECENCY-001

---

# 8. TIMING OPPORTUNITY — MAX 15

Timing consists of:

A. source next-action proximity       max 5
B. PTP timing                         max 5
C. very recent inflow                 max 5

Total                                 max 15

TASK-003 does NOT recommend a WHEN.

These are timing opportunity facts only.

---

## 8.1 SOURCE NEXT-ACTION PROXIMITY — MAX 5

Use TASK-002:

source_next_action_date

If absent:
? 0
? mark unavailable

If date <= reference_date:
? 5

If date = reference_date + 1 day:
? 4

If date is +2 to +3 days:
? 2

Later than +3 days:
? 0

Rule:

SCORE-TIM-NEXTACTION-001

---

## 8.2 PTP TIMING — MAX 5

BROKEN
? 5

PARTIAL AND promise_date <= reference_date
? 4

OPEN AND promise_date <= reference_date
? 3

OPEN AND promise_date = reference_date + 1 day
? 2

OPEN AND promise_date is +2 to +3 days
? 1

KEPT
? 0

No applicable PTP
? 0

Rule:

SCORE-TIM-PTP-001

This intentionally reuses PTP evidence from another perspective.

It is allowed because:

Willingness measures commitment behavior.

Timing measures immediacy of action opportunity.

Trace both separately.

---

## 8.3 INFLOW 3 DAYS — MAX 5

Calculate:

inflow_3d =
SUM(IN cashflow in 3-day window)

Points:

0
? 0

0 < inflow_3d < 5,000,000
? 1

5,000,000 <= inflow_3d < 15,000,000
? 2

15,000,000 <= inflow_3d < 30,000,000
? 4

inflow_3d >= 30,000,000
? 5

Rule:

SCORE-TIM-INFLOW3-001

This is intentional evidence reuse.

Ability measures financial capacity.

Timing measures whether that capacity has appeared very recently.

---

# 9. STRATEGIC ADJUSTMENT — MAX 5

Hackathon V1 has no locked non-zero strategic priority input.

Therefore:

strategic_adjustment_score = 0

for every CIF.

Rule:

SCORE-STR-001

Do not infer strategic priority.

Do not use:

CALL
CBS
challenge override
outstanding
DPD

to create strategic adjustment points.

The reserved maximum remains 5 for future configuration.

---

# 10. MISSING EVIDENCE

Missing evidence != negative evidence.

Prototype rule:

If a feature requires evidence that is unavailable:

feature status = MISSING
feature contribution = 0

Do NOT:

- invent evidence;
- impute average values;
- penalize below zero;
- infer customer unwillingness.

Expose availability per evidence family:

cashflow_available
payment_available
ptp_available
call_history_available
operation_history_available

No numeric confidence score in TASK-003.

---

# 11. COMPONENT BOUNDING

Each component score is the sum of its explicit sub-feature contributions.

All defined sub-feature maxima already sum exactly to the component maximum.

Nevertheless enforce validation:

0 <= component_score <= component_max

If implementation produces a score above component maximum:

FAIL validation.

Do NOT silently clamp a programming error.

---

# 12. RECOVERY RANKING CONTRACT

Ranking applies to all evaluated CIFs.

Primary:

recovery_opportunity_score DESC

Tie-break 1:

ability_to_pay_score DESC

Tie-break 2:

willingness_to_pay_score DESC

Tie-break 3:

timing_opportunity_score DESC

Final deterministic technical tie-break:

cif ASC

The final CIF tie-break is:

[TECHNICAL-DETERMINISM]

not a collection business preference.

Do not use:

debt
DPD
baseline_rank
route

as Recovery Opportunity tie-breakers.

Rule:

RANK-RECOVERY-001

---

# 13. HARD-SUPPRESSED CASES

Current accepted 3,000-CIF dataset contains no hard-suppressed cases.

Prototype forward contract:

If hard_suppressed = true:

- still calculate analytical Recovery Opportunity Score;
- preserve hard_suppressed = true;
- score MUST NOT unsuppress the case;
- case may still receive recovery_rank for analysis;
- future actionable queue must respect suppression.

TASK-003 does not build the actionable queue.

Rule:

SCORE-SUPPRESSION-001

---

# 14. ROUTING IMMUTABILITY

The following TASK-002 fields are immutable:

base_route
challenge_override_route
final_route

TASK-003 may copy them to its output.

TASK-003 must never recalculate or modify them.

Score cannot override routing.

Rule:

SCORE-POLICY-BOUNDARY-001

---

# 15. BUSINESS/TECHNICAL OUTCOME BOUNDARY

call_history.status = Success

means only technical connection success.

It does NOT mean:

PTP
KEPT
high willingness

Business outcome comes only from operation-result evidence.

Rule:

SCORE-OUTCOME-BOUNDARY-001

G19 must continue proving this.

---

# 16. G01 / G02 PRODUCT ASSERTION

Under this prototype scoring configuration:

G01 must retain its baseline advantage over G02 where specified by
the Golden Scenario contract.

Recovery Opportunity must produce:

recovery_rank(G02) < recovery_rank(G01)

This must arise from actual generated evidence.

Do NOT add:

"G02 bonus"
"G01 penalty"
golden-specific scoring
CIF-specific scoring

If G02 does not rank above G01 under the generic rules above:

STOP.

Report the actual component breakdown for G01 and G02.

Do not modify generic scoring solely to force the Golden assertion without explicit approval.

Rule:

SCORE-HERO-001

---

# 17. NO GOLDEN-SPECIFIC LOGIC

Production/scoring source code must not contain conditions such as:

if cif == "GOLDEN_G02"

or:

if scenario == "G02"

Golden IDs may appear only in:

tests
validator
fixture selection
reporting

Never in generic scoring calculations.

---

# 18. DETERMINISM

Same:

dataset
reference_date
configuration

must produce identical:

features
component scores
total score
score trace
ranking

No randomness.
No network.
No LLM.
No current system clock.

---

# 19. CONFIGURATION

All prototype thresholds in this contract should be represented in a
centralized configuration where technically practical.

Defaults must exactly match this contract.

Changing configuration in future must not require rewriting the
scoring architecture.

However default values may not silently differ from this contract.

---

# 20. TASK-003 ACCEPTANCE

TASK-003 PASS requires:

- all 3,000 CIF evaluated;
- score bounds PASS;
- component bounds PASS;
- total = sum of six components;
- route mutation count = 0;
- G07/G08 routes preserved;
- G19 boundary preserved;
- G20 aggregation preserved;
- G02 recovery rank better than G01;
- no CIF-specific score logic;
- deterministic rerun PASS;
- TASK-001 regression PASS;
- TASK-002 regression PASS;
- no GreenNode/LLM/ML/treatment implementation;
- no docs/spec-v1 modification.

END OF LOCKED TASK-003A SCORING CONTRACT