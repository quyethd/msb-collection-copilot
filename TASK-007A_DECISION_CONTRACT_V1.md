# TASK-007A Decision Contract V1

## Status and classification

**Status:** PRODUCT OWNER AUTHORIZED FOR V1 PROTOTYPE

Every business decision rule and default in this document is classified:

- `[PROTOTYPE-RULE]`
- `[CONFIGURABLE]` only where explicitly marked

Nothing in this document is `[MSB-CONFIRMED]`. This contract does not modify
the classifications or rules in `docs/spec-v1/`.

## Authority and precedence

The following rules use first-match-wins precedence. A lower-priority rule
must not override a matched higher-priority rule.

1. P0 HARD SUPPRESSION
2. P1 CALLBACK / SOURCE NEXT ACTION
3. P2 VERIFY CONTACT
4. P3 PARTIAL PTP
5. P4 BROKEN PTP
6. P5 OPEN PTP
7. P6 KEPT PTP
8. P7 SELF-CURE
9. P8 RTP ESCALATION
10. P9 DEFAULT BY FINAL ROUTE

## Output vocabulary

### Treatment

`WAIT`, `WAIT_SELF_CURE`, `REMIND`, `CONTACT`, `PTP_FOLLOW_UP`,
`PTP_RECOVERY`, `PARTIAL_PAYMENT`, `CALLBACK`, `VERIFY_CONTACT`, `ESCALATE`

### Channel

`CALL`, `SMS`, `ZALO`, `EMAIL`, `FIELD`, `NONE`

### Objective

`PAYMENT`, `PTP`, `PTP_KEEP`, `CALLBACK`, `CONTACT_VERIFICATION`,
`INFORMATION_COLLECTION`

### WHEN

Classification: `[PROTOTYPE-RULE]`

WHEN is the following exact typed structure:

```json
{
  "type": "SOURCE_DATETIME | SOURCE_DATE | BEST_WINDOW | TODAY | NONE",
  "datetime": "ISO-8601 timestamp with offset or null",
  "date": "ISO date or null",
  "window": "08-10 | 10-12 | 13-15 | 15-17 | 17-19 | null"
}
```

The representations are:

- `SOURCE_DATETIME`: preserve the accepted source timestamp exactly;
  `datetime` is the original `source_next_action_date`, `date` is null, and
  `window` is null. Do not truncate timestamps or invent timezone conversion.
- `SOURCE_DATE`: use an accepted date-only business fact such as
  `promise_date`; `datetime` is null, `date` is the exact ISO date, and
  `window` is null.
- `BEST_WINDOW`: `datetime` is null, `date` is `reference_date`, and `window`
  is the deterministically selected authorized window.
- `TODAY`: `datetime` is null, `date` is `reference_date`, and `window` is
  null.
- `NONE`: `datetime`, `date`, and `window` are null.

## Decision rules

### P0 — NBA-000 HARD SUPPRESSION

Classification: `[PROTOTYPE-RULE]`

Condition: `hard_suppressed = true`.

Output:

- treatment: `WAIT`
- channel: `NONE`
- when: `{type: NONE, datetime: null, date: null, window: null}`
- objective: `INFORMATION_COLLECTION`
- primary reason code: `HARD_SUPPRESSED`

### P1 — NBA-100 CALLBACK / SOURCE NEXT ACTION

Classification: `[PROTOTYPE-RULE]`

Conditions:

- latest business outcome is `NA`; and
- a valid `source_next_action_date` exists.

Output:

- treatment: `CALLBACK`
- channel: use `source_next_operation_channel` only when it is an authorized
  NBA channel and operationally compatible with CALLBACK; for V1 the only
  compatible source channel is `CALL`; every other value falls back to `CALL`
- when: `{type: SOURCE_DATETIME, datetime: source_next_action_date, date: null, window: null}`;
  preserve the exact accepted source timestamp
- objective: `CALLBACK`
- primary reason code: `CALLBACK_DUE`

### P2 — NBA-110 INVALID CONTACT

Classification: `[PROTOTYPE-RULE]`

Condition: latest business outcome is `NIN`.

Output:

- treatment: `VERIFY_CONTACT`
- channel: `NONE`
- when: `{type: TODAY, datetime: null, date: reference_date, window: null}`
- objective: `CONTACT_VERIFICATION`
- primary reason code: `INVALID_CONTACT`

### P3 — NBA-200 PARTIAL PTP

Classification: `[PROTOTYPE-RULE]`

Condition: `ptp_state = PARTIAL`.

Output:

- treatment: `PARTIAL_PAYMENT`
- channel: `CALL`
- when: BEST_WINDOW
- objective: `PAYMENT`
- primary reason code: `PARTIAL_PTP`

### P4 — BROKEN PTP

Configuration:

`BROKEN_PTP_RECENT_INFLOW_THRESHOLD_VND = 5000000`

#### NBA-210 BROKEN PTP WITH RECENT INFLOW

Classification: `[PROTOTYPE-RULE] [CONFIGURABLE]`

Conditions:

- `ptp_state = BROKEN`;
- `cashflow_available = true`; and
- `inflow_3d >= BROKEN_PTP_RECENT_INFLOW_THRESHOLD_VND`.

Output:

- treatment: `PTP_RECOVERY`
- channel: `CALL`
- when: BEST_WINDOW
- objective: `PAYMENT`
- primary reason code: `BROKEN_PTP_RECENT_INFLOW`

#### NBA-220 OTHER BROKEN PTP

Classification: `[PROTOTYPE-RULE]`

Condition: `ptp_state = BROKEN` and NBA-210 did not match.

Output:

- treatment: `CONTACT`
- channel: `CALL`
- when: BEST_WINDOW
- objective: `PAYMENT`
- primary reason code: `BROKEN_PTP`

### P5 — NBA-230 OPEN PTP

Classification: `[PROTOTYPE-RULE]`

Condition: `ptp_state = OPEN`.

Output:

- treatment: `PTP_FOLLOW_UP`
- channel: `CALL`
- objective: `PTP_KEEP`
- primary reason code: `OPEN_PTP`

Timing uses the first matching branch:

1. If a valid `source_next_action_date` exists, use
   `{type: SOURCE_DATETIME, datetime: source_next_action_date, date: null, window: null}`
   and preserve the exact accepted source timestamp.
2. Otherwise, if a valid `promise_date` exists and
   `promise_date >= reference_date`, use
   `{type: SOURCE_DATE, datetime: null, date: promise_date, window: null}`.
3. Otherwise use BEST_WINDOW.

### P6 — NBA-240 KEPT PTP

Classification: `[PROTOTYPE-RULE]`

Condition: `ptp_state = KEPT`.

Output:

- treatment: `WAIT`
- channel: `NONE`
- when: `{type: NONE, datetime: null, date: null, window: null}`
- objective: `PTP_KEEP`
- primary reason code: `KEPT_PTP`

### P7 — SELF-CURE

Classification: `[PROTOTYPE-RULE]`

`SELF_CURE_ELIGIBLE` is true only when all conditions are true:

- `final_route` is in `{CALL, CBS}`;
- `max_dpd_cif <= SELF_CURE_MAX_DPD`;
- `ptp_state` is `NONE`;
- latest business outcome is not in `{RTP, NIN}`;
- `cashflow_available = true`;
- `net_cashflow_30d > 0`;
- `inflow_7d >= 15000000`;
- `hard_suppressed = false`; and
- `source_next_action_date` is null.

Historical quick-cure behavior is not a V1 condition because no accepted
upstream fact currently supports it.

Configuration:

`SELF_CURE_MAX_DPD = 14`

Classification of this threshold: `[PROTOTYPE-RULE] [CONFIGURABLE]`.

This threshold explicitly supersedes the previous Product Owner prototype
condition `max_dpd_cif <= 4`. It demonstrates that CALL routing does not
automatically imply immediate calling. It does not modify `docs/spec-v1/`.

#### NBA-300 CALL SELF-CURE

Additional condition: `final_route = CALL`.

Output:

- treatment: `WAIT_SELF_CURE`
- channel: `NONE`
- when: `{type: NONE, datetime: null, date: null, window: null}`
- objective: `PAYMENT`
- primary reason code: `CALL_SELF_CURE`

#### NBA-310 CBS SELF-CURE

Additional condition: `final_route = CBS`.

Output:

- treatment: `WAIT`
- channel: `NONE`
- when: `{type: NONE, datetime: null, date: null, window: null}`
- objective: `PAYMENT`
- primary reason code: `CBS_SELF_CURE`

### P8 — NBA-400 RTP ESCALATION

Classification: `[PROTOTYPE-RULE]`

Conditions:

- `final_route = CALL`; and
- latest business outcome is `RTP`.

Output:

- treatment: `ESCALATE`
- channel: `CALL`
- when: BEST_WINDOW
- objective: `PAYMENT`
- primary reason code: `RTP_ESCALATION`

Repeated-broken-PTP escalation is not implemented in V1.

### P9 — DEFAULT BY FINAL ROUTE

Classification: `[PROTOTYPE-RULE]`

#### NBA-900 CALL DEFAULT

Condition: `final_route = CALL`.

Output: `CONTACT`, `CALL`, BEST_WINDOW, `PAYMENT`, reason `CALL_DEFAULT`.

#### NBA-910 CBS DEFAULT

Condition: `final_route = CBS`.

Output: `REMIND`, `SMS`, BEST_WINDOW, `PAYMENT`, reason `CBS_DEFAULT`.

#### NBA-920 OTHER DEFAULT

Condition: `final_route = OTHER`.

Output: `WAIT`, `NONE`, `{type: NONE, datetime: null, date: null, window: null}`,
`INFORMATION_COLLECTION`, reason `OTHER_DEFAULT`.

## BEST_WINDOW

Classification: `[PROTOTYPE-RULE] [CONFIGURABLE]`

Configuration:

`BEST_CONTACT_LOOKBACK_DAYS = 30`

Authorized windows, in earliest-window order:

1. `08-10`
2. `10-12`
3. `13-15`
4. `15-17`
5. `17-19`

Source authority is the full accepted TASK-001 `call_history`, not the
TASK-005 preview. Use only technical outbound calls in the 30-day lookback,
with the accepted deterministic `reference_date` as cutoff. Do not use the
system clock or events after `reference_date`.

Historical evidence is sufficient when at least one successful outbound
technical call exists during the 30-day lookback.

For every authorized window calculate:

- `attempt_count`;
- `successful_call_count`;
- `success_rate = successful_call_count / attempt_count`.

Only accepted deterministic technical call status determines technical
success. Select by:

1. highest success rate;
2. highest successful-call count;
3. earliest window.

Technical `Success` remains technical evidence and must not be interpreted as
a PTP, payment, or other business success.

If there is no successful outbound technical call in the 30-day lookback,
use fallback window `10-12`.

BEST_WINDOW output is:

```json
{
  "type": "BEST_WINDOW",
  "datetime": null,
  "date": "reference_date",
  "window": "selected window"
}
```

## Evidence and reason codes

One primary reason code corresponding to the selected first-match rule is
sufficient for V1. Additional factual evidence references may be attached but
must not create new decision semantics.

## Legacy Golden expectation compatibility

Classification: `[PROTOTYPE-RULE]`

TASK-007A Golden validation must distinguish:

1. upstream fact assertions; and
2. NBA expectation assertions.

G03 and G18 contain legacy Golden treatment expectations that are not
derivable from their currently accepted upstream deterministic facts. For
both CIFs, the accepted facts include:

- `net_cashflow_30d = 0`; and
- `inflow_7d = 0`.

They therefore do not satisfy the Product Owner authorized V1 self-cure
contract. TASK-007A must report them as follows:

### G03

- upstream facts: `PASS`
- legacy NBA expectation: `NOT_DERIVABLE`
- actual deterministic rule: `NBA-900`
- actual deterministic result: `CONTACT / CALL / BEST_WINDOW / PAYMENT`
- classification: `LEGACY_GOLDEN_EXPECTATION_NOT_DERIVABLE_FROM_ACCEPTED_FACTS`

### G18

- upstream facts: `PASS`
- legacy NBA expectation: `NOT_DERIVABLE`
- actual deterministic rule: `NBA-900`
- actual deterministic result: `CONTACT / CALL / BEST_WINDOW / PAYMENT`
- classification: `LEGACY_GOLDEN_EXPECTATION_NOT_DERIVABLE_FROM_ACCEPTED_FACTS`

These actual decisions pass against the current Product Owner authorized NBA
contract. TASK-007A must not claim that the old `WAIT_SELF_CURE` expectations
are satisfied. This compatibility classification does not authorize changing
`docs/spec-v1/`, accepted upstream facts, cashflow windows, self-cure
thresholds, or production behavior for a Golden CIF.

## HERO_SELF_CURE_V1 presentation selector

Classification: `[PROTOTYPE-RULE]`

The demo self-cure representative must be selected only from actual CIFs whose
deterministic decision is `NBA-300`. Apply this deterministic presentation
ordering:

1. `final_route = CALL`;
2. selected rule is `NBA-300`;
3. `inflow_7d` descending;
4. `net_cashflow_30d` descending;
5. `max_dpd_cif` descending;
6. CIF ascending.

This selector is demo presentation logic only. It must not change a decision,
rename a CIF, mutate synthetic data, or appear as a production NBA decision
rule. Label the selected representative `HERO_SELF_CURE_V1`.

## Contract completeness gate

The contract is complete when all of the following equal zero across the
intended population:

- treatment unresolved;
- channel unresolved;
- WHEN unresolved;
- objective unresolved;
- decision ambiguity; and
- rule-match unresolved.

The separately reported G03/G18 legacy-expectation incompatibility does not
block implementation.

## Upstream immutability

TASK-007A must not change:

- `base_route`
- `challenge_override_route`
- `final_route`
- `hard_suppressed`
- Recovery Opportunity Score
- component scores
- baseline rank
- Recovery rank
- PTP state
- cashflow facts
- contact facts

## Prohibited scope

No LLM, MaaS, AgentBase Agent, probability, confidence, expected recovery,
generated explanation, What-if, AEV, or ROI is part of this contract.
