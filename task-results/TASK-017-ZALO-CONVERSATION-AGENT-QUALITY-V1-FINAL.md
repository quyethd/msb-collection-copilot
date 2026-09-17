# TASK-017 Zalo Conversation Agent Quality V1 — Gate Record

TASK_ID=TASK-017-ZALO-CONVERSATION-AGENT-QUALITY-V1

PREVIOUS_HEAD=429adeaf81f1fc884c0c6f15550414d0b5e776e5

## Root-cause matrix

| Transcript symptom | Classification | Evidence / corrective scope |
| --- | --- | --- |
| Natural worklist variants fall back | NLU | Deterministic normalization and intent markers did not cover `nay`, `hnay`, `thao tác`, or short worklist requests. |
| `CBS thì sao` loses CALL/CBS topic | CONTEXT | State lacked a knowledge-topic field and follow-up routing was overridden by case context. |
| Active-CIF score question reaches evaluation knowledge | TOOL_ROUTING | Score phrasing did not include `được tính` / `dựa trên`, allowing knowledge routing. |
| Priority questions return generic case response | NLU / TOOL_ROUTING | No explicit priority intent or canonical decision-backed explanation. |
| `Khách không trả nợ thì sao` gets an unsuitable answer | CONTEXT | No pending clarification state. |
| Duplicate/no-response evidence | DELIVERY / DEDUP | Worker has update watermark and bridge has update-key cache; review also found a hard-coded active CIF in poller context, removed to avoid a context leak. |
| Pairing/reconnect | PAIRING | The configured systemd worker is inactive; a manually launched worker exists. Live pairing cannot be verified without restarting/re-pairing a production recipient. |

## Implemented, locally verified changes

- Added normalized natural-language routing for the real worklist variants.
- Added narrowly bounded `SNYxxxxxx` → `SYNxxxxxx` correction.
- Added case-score routing ahead of knowledge routing whenever an active CIF exists.
- Added explicit CALL/CBS knowledge-topic continuity.
- Added pending clarification for non-payment hypotheticals and one-word resolution.
- Added simulation follow-up/baseline wording while retaining Simulation Core as authority.
- Added the required conversation-state fields, CIF-owned simulation invalidation, and removed the poller's hard-coded `SYN002846` context seed.
- Added transcript/state regression coverage in `tests/test_task017_zalo_conversation_quality.py`.
- No Decision Core, scoring, routing, NBA, PTP, landing, or frontend architecture source was changed.

## Evidence

```text
PYTHONPATH=src pytest -q \
  tests/test_task017_zalo_conversation_quality.py::test_pending_clarification_resolves_one_word_replies \
  tests/test_task017_zalo_conversation_quality.py::test_active_cif_score_breakdown_never_routes_to_knowledge \
  tests/test_zalo_worker.py -x

25 passed in 20.20s

Decision canaries: PASS
SYN002846 = CALL / WAIT_SELF_CURE / NONE / 47
SYN002846 inflow_7d=0 = CONTACT / CALL
SYN000746 score = 69
```

## Closeout status

This is **not a closure report**. Mandatory production gates remain unverified:

```text
PRODUCTION_ZALO_LIVE_ROUNDTRIP=NOT_RUN
PRODUCTION_DUPLICATE_RESPONSE_RATE=NOT_MEASURED
PRODUCTION_NO_RESPONSE_RATE=NOT_MEASURED
PRODUCTION_WRONG_CIF=NOT_MEASURED
PRODUCTION_CONTEXT_LEAK=NOT_MEASURED
PRODUCTION_DECISION_PARITY=NOT_MEASURED
PRODUCTION_SCORE_PARITY=NOT_MEASURED
VERY_AUDIT=NOT_RUN
READY_TO_DEPLOY=NO
TASK_017_CLOSED=NO
```

Blocker: `zalo-worker.service` is inactive while a manually launched worker is running; no approved live paired recipient/roundtrip is available. Restarting it or deploying would alter production state before all required pre-deploy tests and live QA can be truthfully completed.
