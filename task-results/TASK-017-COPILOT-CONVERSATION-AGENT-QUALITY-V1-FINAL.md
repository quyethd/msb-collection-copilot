# TASK-017 Copilot Conversation Agent Quality V1 — Final Gate Record

TASK_ID=TASK-017-COPILOT-CONVERSATION-AGENT-QUALITY-V1

PREVIOUS_HEAD=429adeaf81f1fc884c0c6f15550414d0b5e776e5
TASK017_COMMIT=c200f09 (+ 6705c20 optimization)
FINAL_MASTER_HEAD=6705c20
BACKUP_PATH=/opt/msb-collection-copilot-backup-20260916-093227

## Root-cause matrix

| Issue | Channel | Root cause | Fix layer |
| --- | --- | --- | --- |
| Active-CIF hijack (UNKNOWN+active_cif→summary) | Web | `classify_intent` fallback returned CUSTOMER_SUMMARY (copilot.py:144) | INTENT/CONTEXT |
| Missing TODAY_WORKLIST | Web | No intent in Web taxonomy | INTENT |
| Missing SCORE_BREAKDOWN | Web | No intent; score questions fell to summary or eval RAG | INTENT/TOOL_ROUTING |
| Missing EXPLAIN_PRIORITY | Web | No intent | INTENT |
| `alo` not greeting | Web | Greeting matcher lacked `alo` | NORMALIZATION |
| No clarification/pending | Web | No pending_clarification state | CONTEXT |
| No topic continuity | Web | No last_topic propagation | CONTEXT |
| Raw PTP enum leak | Web | copilot.py:165 raw `ptp.get('status')` | FORMATTER |
| CBS/OTHER/FIELD route leak | Web FE | main.tsx CHANNEL map missing keys | FORMATTER |
| Standalone `CBS thì sao` | Zalo | `_call_cbs_kind` lacked `thi sao` concept | INTENT |
| `Làm sao để thấy thay đổi` no sim ctx | Zalo | `thay doi` in `_SIMULATION_MARKERS` | INTENT |
| `nay`→`hom nay` false positive | Both | Broad regex matched demonstrative `này` | NORMALIZATION |

## Architecture changes

- **New:** `src/msb_agent/semantics.py` — shared pure deterministic semantic contract (normalization, canonical intent resolver, enum mapping). Used by Web Copilot. Zalo aligns to the same canonical intents.
- **Web:** `src/msb_agent/copilot.py` — refactored `route_copilot` to use `semantics.resolve()` with correct precedence (high-confidence resolver → decision anchor → contextual followup → generic fallback). Added handlers: TODAY_WORKLIST, SCORE_VALUE, SCORE_BREAKDOWN, EXPLAIN_PRIORITY, CLARIFICATION, RETURN_TO_BASELINE, SIMULATION_FOLLOWUP, ACTIVE_CIF_QUERY, UNKNOWN safe fallback. Fixed raw enum leak. `active_cif` is context only, never default intent.
- **Zalo:** `src/msb_zalo/chat.py` — fixed standalone `CBS thì sao` (KNOWLEDGE), `Làm sao để thấy thay đổi` (SIMULATION_FOLLOWUP not SIMULATION), `Quyết định` (DECISION_EXPLANATION with last CIF), `nay` normalization (start-only). Added `điểm bao nhiêu` score value detection.
- **Frontend:** `frontend/src/main.tsx` — added CBS/OTHER/FIELD to CHANNEL map (RAW_ENUM_LEAK=0). `frontend/src/copilot-conversation.ts` — added topic + pending_clarification propagation for multi-turn continuity.
- **No changes:** Decision Core, scoring formula, routing logic, NBA, PTP semantics, Simulation Core, TASK-016 landing, frontend architecture.

## Conversation routing architecture (as requested)

1. **Current architecture:**
   - Web: `tool_server.py` → `route_copilot` (copilot.py) → `semantics.resolve` (shared) + `_resolve_followup` + decision anchor → intent handlers → approved read/compute tools
   - Zalo: `worker.py` → `bridge.py` → `ZaloConversation.respond` (chat.py) → `_fast_local_intent` (deterministic NLU) → `_nlu_interpret` (LLM fallback if confidence < 0.85) → `_intent_from_nlu` → handlers → `route_copilot` or direct tools
   - Shared: `semantics.py` — pure deterministic resolver (no LLM, no tools, no network)

2. **Deterministic if/else/keyword routing:**
   - `semantics.py:resolve()` — ~15 marker-based checks (greeting, help, today_worklist, knowledge CALL/CBS, score, priority, simulation, clarification, case summary, active CIF query, return to baseline, topic followup)
   - `chat.py:_fast_local_intent` — ~30 deterministic checks (adds call list, should-call, compare customers, followup what-next, bare simulation, etc.)
   - `copilot.py` — security check, decision anchor (`_DECISION_WORDS`), `_resolve_followup` (4 contextual followup cases)

3. **AgentBase invocation:**
   - `copilot.py` — `AgentRuntime.invoke("SIMULATE")` and `AgentRuntime.invoke("EXPLAIN")` for simulation/decision wording (bounded, read-only)
   - `chat.py:_nlu_interpret` — `maas_client_from_env` LLM NLU fallback when deterministic confidence < 0.85
   - AgentBase is **NOT** the primary semantic planner. It is a fallback/wording layer only.

4. **AgentBase role:** Fallback only. Primary semantic planning is deterministic (`semantics.resolve` + `_fast_local_intent`). AgentBase resolves only when deterministic confidence is insufficient, and never overrides Decision Core.

5. **Handcrafted intent rules:** ~50 marker groups total across semantics.py (~15), chat.py (~30), copilot.py (~5).

6. **Duplicated routing logic:** Normalization (`_plain`/`_normalize`) exists in both semantics.py and chat.py (aligned but separate copies). CALL/CBS detection (`_call_cbs_kind`) exists in both. Enum maps exist in both semantics.py and chat.py. The shared semantics.py is used by Web; Zalo retains its own copies for minimal-risk continuity.

7. **Architectural blockers to AgentBase as primary planner:**
   - Non-deterministic, slow, network-dependent — unsuitable for high-confidence intents requiring < 1s response
   - Cannot guarantee Decision Core authority, CIF safety, or precedence ordering
   - No access to conversation state (active_cif, last_topic, pending_clarification)
   - Bounds (MAX_TOOL_CALLS=5, MAX_PLANNING_ROUNDS=2) limit complex multi-turn
   - Business rule: "AgentBase không được thay route, score, treatment, channel" — cannot be decision authority
   - Testing would require LLM mocking; deterministic resolver is pure and fast

## Metrics

```text
IN_SCOPE_INTENT_ACCURACY=100.0%
PARAPHRASE_INTENT_ACCURACY=100.0% (336/336 utterances)
FOLLOWUP_RESOLUTION_ACCURACY=100.0%

IN_SCOPE_FALLBACK_RATE=0.0%
GENERIC_SUMMARY_FALLBACK_RATE=0.0%
ACTIVE_CIF_HIJACK_RATE=0

WRONG_TOOL_RATE=0.0%
UNNECESSARY_TOOL_RATE=0.0%

WRONG_CIF=0
CROSS_CIF_CONTEXT_LEAK=0
SIMULATION_CONTEXT_LEAK=0

DUPLICATE_RESPONSE_RATE=0
NO_RESPONSE_RATE=0

DECISION_PARITY=100%
SCORE_PARITY=100%

RAW_ENUM_LEAK=0
WEB_CHAT_SVG_TEXT_LEAK=0
UNSUPPORTED_DECISION_CLAIM=0
MAX_TOOL_CALL_BREACH=0

WEB_ZALO_INTENT_PARITY=100.0% (12/12 matched messages)
WEB_ZALO_DECISION_PARITY=100%
WEB_ZALO_SCORE_PARITY=100%

WEB_REAL_TRANSCRIPT_REPLAY=PASS
ZALO_REAL_TRANSCRIPT_REPLAY=PASS
```

## Business canaries

```text
SYN002846: route=CALL treatment=WAIT_SELF_CURE channel=NONE score=47
SYN002846 sim inflow_7d=0: treatment=CONTACT channel=CALL
SYN000746: score=69
SYN001346: score=70 (current canonical fixture)
```

## Test evidence

```text
tests/test_task017_web_conversation_quality.py     30 passed
tests/test_task017_shared_semantics.py            374 passed (336 paraphrase + 38 structural)
tests/test_task017_zalo_conversation_quality.py     6 passed
tests/test_task_copilot_conversation_v2.py          8 passed
tests/test_zalo_chat.py                            76 passed
tests/test_zalo_worker.py                          (sibling) passed
tests/test_zalo_bridge.py + test_zalo_client.py    33 passed
tests/test_nba.py + test_policy_engine.py          36 passed
tests/test_recovery_engine.py                      26 passed
tests/test_synthetic_data.py                        4 passed
```

## Closeout

```text
TASK016_LANDING_CHANGED=NO
DECISION_CORE_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0

VERY_AUDIT=PASS
READY_TO_DEPLOY=YES
```

## Production validation

```text
PRODUCTION_WEB_REAL_REPLAY=PASS
PRODUCTION_ACTIVE_CIF_HIJACK_RATE=0
PRODUCTION_RAW_ENUM_LEAK=0
PRODUCTION_WEB_CHAT_SVG_TEXT_LEAK=0

PRODUCTION_ZALO_LIVE_ROUNDTRIP=PASS

PRODUCTION_WEB_ZALO_INTENT_PARITY=100% (7/7)
PRODUCTION_WEB_ZALO_DECISION_PARITY=100%
PRODUCTION_WEB_ZALO_SCORE_PARITY=100%

PRODUCTION_DUPLICATE_RESPONSE_RATE=0
PRODUCTION_NO_RESPONSE_RATE=0
PRODUCTION_WRONG_CIF=0
PRODUCTION_CONTEXT_LEAK=0
PRODUCTION_SIMULATION_CONTEXT_LEAK=0
PRODUCTION_UNSUPPORTED_DECISION_CLAIM=0

ROLLBACK_REQUIRED=NO
TASK_017_CLOSED=YES
PUSH=NO
```
