# TASK-013A — Web Simulation NLU Corrective

Date: 2026-09-15
Scope: Web Copilot simulation-language extraction only

## Outcome

The production failure was reproduced on the rolled-back baseline and fixed with
a small deterministic phrase-normalization change. The Web Copilot now maps the
accepted zero-inflow Vietnamese phrases to `{"inflow_7d": 0}` and leaves the
simulation engine responsible for calculating the resulting decision.

## Root cause and reproduction

Exact production prompt:

`Nếu tiền vào 7 ngày bằng 0 thì quyết định có thay đổi không?`

Before the fix:

```text
intent=SIMULATION
simulate_decision changes={}
result=WAIT_SELF_CURE / NONE
```

`_simulation_changes()` only recognized the wording around `dòng tiền 7 ngày`,
not the natural `tiền vào 7 ngày` wording. The classifier also needed to admit
the short zero-inflow statement as a simulation input.

## Files changed

- `src/msb_agent/copilot.py` — bounded normalized patterns and one canonical
  `inflow_7d` mapping.
- `tests/test_task013a_web_simulation.py` — phrase, integration, follow-up, and
  CIF-context regression coverage.

No Decision Core, policy, NBA, recovery, simulation engine, RAG, synthetic data,
Zalo, frontend, or landing files were changed.

## Extraction contract

Positive phrases map to `{"inflow_7d": 0}`:

| Phrase | Result |
|---|---|
| `tiền vào 7 ngày bằng 0` | `inflow_7d=0` |
| `Nếu tiền vào 7 ngày bằng 0 thì quyết định có thay đổi không?` | `inflow_7d=0` |
| `Nếu tiền vào 7 ngày bằng 0 thì sao?` | `inflow_7d=0` |
| `không có tiền vào 7 ngày` | `inflow_7d=0` |
| `tiền vào tuần này bằng 0` | `inflow_7d=0` |
| `giả sử 7 ngày tới không có tiền vào` | `inflow_7d=0` |
| `nếu nó không có tiền vào tuần này thì sao` | `inflow_7d=0` |
| `Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?` | `inflow_7d=0` |

Negative current-fact/knowledge phrases remain non-simulation and produce no
extracted change:

`tiền vào 7 ngày là bao nhiêu?`; `dòng tiền gần đây thế nào?`; `khách này có
tiền vào không?`; `cho tôi xem tiền vào 7 ngày`; `CALL và CBS khác nhau thế nào?`.

## Integration and conversation proof

The real existing `simulate_decision` path was used for both required prompts:

```text
EXACT_PRODUCTION_PHRASE: PASS
  intent=SIMULATION
  changes={"inflow_7d": 0}
  before=WAIT_SELF_CURE / NONE
  after=CONTACT / CALL

SHORT_PRODUCTION_PHRASE: PASS
  changes={"inflow_7d": 0}
  after=CONTACT / CALL
```

The complete same-CIF sequence (`tiền vào 7 ngày bằng 0` → `Vậy nên làm gì?`)
reused only the safe `inflow_7d=0` change and returned the simulation after-state
`CONTACT / CALL`, never the baseline `WAIT_SELF_CURE / NONE`.

Switching the active CIF cleared the prior conversation context; the old
simulation was not sent to the new CIF.

## Test results

```text
FOCUSED_WEB_REGRESSION=PASS (23 tests, 13 phrase subtests)
WEB_SIMULATION_AFTER_STATE=PASS
WEB_SIMULATION_FOLLOWUP=PASS
NO_BASELINE_OVERRIDE_AFTER_SIMULATION=PASS
SIMULATION_CONTEXT_CIF_MATCH=PASS
CONTEXT_CIF_LEAK=0
```

The repository has no Zalo chat or Zalo transport test source available in this
checkout, so those suites could not be independently executed here. The
available RAG-focused run reached 27 passing tests but exceeded the bounded
60-second execution window before producing a completion summary.

```text
ZALO_SIMULATION_REGRESSION=NOT_RUN (no Zalo test source in checkout)
ZALO_TRANSPORT_REGRESSION=NOT_RUN (no Zalo test source in checkout)
RAG_REGRESSION=NOT_COMPLETED (bounded run timed out after 27 passing tests)
```

Business canary probe:

```text
SYN002846_ROUTE=CALL
SYN002846_TREATMENT=WAIT_SELF_CURE
SYN002846_CHANNEL=NONE
SYN002846_SCORE=47
SYN000746_SCORE=69
BUSINESS_SEMANTICS_DRIFT=0
```

## Safety and delivery gates

```text
ROOT_CAUSE_IDENTIFIED=YES
EXACT_PRODUCTION_FAILURE_REPRODUCED=YES
WEB_SIMULATION_CHANGE_EXTRACTION=inflow_7d:0
WEB_SIMULATION_RESULT=CONTACT/CALL
RAW_ENUM_LEAK=0
RAW_JSON_LEAK=0
RAW_NONE_LEAK=0
SECRET_SCAN=PASS
TOKEN_LEAK_COUNT=0
FRONTEND_CHANGED=NO
LANDING_CHANGED=NO
DIFF_CHECK=PASS
READY_FOR_VERY_AUDIT=NO
READY_TO_COMMIT=NO
COMMIT=NO
MERGE=NO
DEPLOY=NO
TASK_014_AUTHORIZED=NO
```
