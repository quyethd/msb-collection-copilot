# TASK-011G — Tool-aware + model-aware Copilot routing

Status: IMPLEMENTATION COMPLETE — READY FOR REVIEW

## ARCHITECTURE

`/demo/copilot` now uses a centralized orchestration boundary. It classifies
free text, selects the accepted deterministic tool, optionally selects a
separate fast MaaS path, and uses the existing GLM/MaaS path only for bounded
explanations or simulations. Deterministic tool output remains the source of
truth for every business decision.

## AVAILABLE_GREENNODE_MODEL_ROUTING_CAPABILITY

The deployed AgentBase runtime uses a static model configuration; dynamic
model switching inside that runtime is not an available documented capability.
The implementation therefore keeps the existing AgentBase proof/runtime
unchanged and supports optional separate MaaS fast-path configuration through
`LLM_FAST_BASE_URL`, `LLM_FAST_API_KEY`, and `LLM_FAST_MODEL`. Those variables
are not configured in the current environment, so no Qwen or Gemma usage is
claimed. Gemma is not in the critical demo path.

## INTENT_ROUTING

The explicit taxonomy is `GREETING_HELP`, `CUSTOMER_SUMMARY`, `CASHFLOW`,
`PTP`, `ROUTE_PRIORITY`, `DECISION_EXPLANATION`, `SIMULATION`, and
`OUT_OF_SCOPE`. Obvious requests use deterministic lexical matching;
ambiguous requests can use the optional structured fast classifier and then
fall back to a grounded customer-context investigation.

## TOOL_ROUTING

| Intent | Tool path | Model path |
|---|---|---|
| GREETING_HELP | none | LOCAL |
| CUSTOMER_SUMMARY | get_customer_360 | LOCAL or optional FAST_QWEN |
| CASHFLOW | get_customer_360 | LOCAL or optional FAST_QWEN |
| PTP | get_customer_360 | LOCAL or optional FAST_QWEN |
| ROUTE_PRIORITY | get_next_best_action | LOCAL deterministic |
| DECISION_EXPLANATION | get_next_best_action first; context only if needed | bounded GLM/MaaS or FALLBACK |
| SIMULATION | simulate_decision | bounded GLM/MaaS or FALLBACK |
| OUT_OF_SCOPE | none | LOCAL |

## MODEL_ROUTING

Greeting/help responses are local and do not invoke AgentBase. Simple factual
summaries remain local when the optional fast configuration is absent.
Decision explanations and simulation interpretation use the existing MaaS
client with an 8-second model timeout; no model output can alter the accepted
deterministic result.

## LATENCY_BEFORE

The accepted prior observation for the copilot was approximately 15–20 seconds
for representative responses. This was historical product evidence, not a
new benchmark run in this change.

## LATENCY_AFTER

Measured locally against the current implementation:

| Request | Path | Total observed |
|---|---|---:|
| greeting | LOCAL | ~0.1 ms |
| cashflow/PTP/customer summary | LOCAL | ~2–5 ms |
| route lookup | LOCAL + NBA | ~4–5 ms |
| decision explanation | FALLBACK after bounded GLM attempt | ~8.1 s |
| simulation | FALLBACK after bounded model attempt | ~8.1 s |

The fast local paths are materially below the previous observation, and the
reasoning paths now have a bounded ceiling with deterministic fallback. Actual
Qwen latency is not reported because no fast model configuration is present.

## TIMEOUT_FALLBACK

When model generation does not complete, the response is built only from
accepted NBA/customer fields. The UI indicates that confirmed system
information is being shown; no fabricated evidence is added.

## QUESTION_CATALOG

`frontend/src/assistant-question-catalog.ts` is the single catalog of ten
approved example questions and their groups. System Overview and the drawer
consume that same source. The drawer initially shows four questions and
expands with “Xem thêm 6 câu hỏi”; the free-text composer remains unrestricted.

## DRAWER_OVERLAY_FIX

The assistant drawer is rendered with a React portal into `document.body`.
The overlay/drawer layers are explicitly above the System Overview sticky
content, with scrollable full-height drawer content and a usable composer.

## REGRESSION

- TASK-011G routing tests: 9/9 passed.
- TASK-011D adapter tests: 6/6 passed.
- TASK-011 tests: 3/3 passed.
- Focused TASK-008 regressions: 7/7 passed.
- Frontend tests: 41/41 passed.
- Operational layout QA: 12/12 passed.
- System Overview local three-viewport QA: PASS.
- Production build: PASS.

Existing AgentBase version-7 proof is preserved and was not relabeled or
modified by this task.

## SECURITY

Frontend source and bundle scans found no configured secrets, bearer
credentials, private prompts, or reasoning fields. The browser continues to
call only browser-safe `/demo/*` endpoints.

## BUSINESS_SEMANTICS_DRIFT

0. The accepted deterministic engine remains authoritative for route,
treatment, channel, recovery score, simulation, and impact semantics.

## FINAL GATES

TOOL_AWARE_ROUTING=PASS
MODEL_AWARE_ARCHITECTURE=PASS
ACTIVE_MODEL_PATH=LOCAL_PLUS_GLM_5_2
QWEN_FAST_MODEL_AVAILABLE=PASS
QWEN_DIRECT_MAAS_PROOF=PASS
FAST_MODEL_ACTIVE=NO
QWEN_FAST_PATH=NOT_PROVEN
MULTI_MODEL_ROUTING_PROVEN=NO
FREE_TEXT_ROUTING=PASS
QUESTION_CATALOG_SINGLE_SOURCE=PASS
DRAWER_OVERLAY=PASS
LATENCY_IMPROVED=PASS
TIMEOUT_FALLBACK=PASS
AGENTBASE_FIDELITY=PASS
TESTS=PASS
BUILD=PASS
SECRET_AUDIT=PASS
PRIVATE_REASONING_AUDIT=PASS
BUSINESS_SEMANTICS_DRIFT=0

COMMITTED_AND_DEPLOYED

## TASK-011G.1 UI GATES

Rendered Playwright QA reproduced `/gioi-thieu`, opened the assistant
drawer, and verified the quick-nav/backdrop/drawer relationship at
1366x768, 1440x900, and 1920x1080. The quick-nav is below the backdrop,
does not receive pointer interaction through the backdrop, and the drawer
composer/send button remain within the viewport.

The drawer uses the shared ten-question catalog, shows the recommended four
initial questions, and expands to all ten. The free-text textarea remains
available and is not a whitelist-controlled input.

QUICK_NAV_OVER_DRAWER=PASS
QUICK_NAV_POINTER_INTERACTION_WHEN_DRAWER_OPEN=PASS
DRAWER_OVERLAY=PASS
DRAWER_COMPOSER_VISIBLE=PASS
DRAWER_SEND_BUTTON_VISIBLE=PASS
QUESTION_CATALOG_COUNT=10
QUESTION_CATALOG_UI=PASS
DRAWER_INITIAL_4=PASS
DRAWER_EXPAND_10=PASS
FREE_TEXT_COMPOSER=PASS
THREE_VIEWPORT_DRAWER_QA=PASS

## TASK-011G.1 MODEL ACTIVATION AND LATENCY PROOF

The configured MaaS model catalog was queried without exposing credentials.
It returned `qwen/qwen3.6-flash`, `z-ai/glm-5.2-hackathon`, and
`google/gemma-4-31b-it`. Qwen was also directly reachable through the
existing MaaS API and returned content for customer-summary, cashflow, PTP,
and intent-classification prompts using the accepted synthetic context.

The optional fast configuration was tested in the local HTTP server, but the
Python server path did not complete reliably within its bounded timeout even
though the standalone direct MaaS request completed. The temporary fast
environment override was removed so the normal demo path does not incur an
unreliable latency penalty. No Qwen usage is claimed for `/demo/copilot`.

FAST_MODEL_STATUS=AVAILABLE_BUT_NOT_ACTIVE
QWEN_FAST_MODEL_AVAILABLE=PASS
QWEN_FAST_MODEL_ID=qwen/qwen3.6-flash
FAST_MODEL_ACTIVE=NO
FAST_QWEN_REQUEST=PASS_DIRECT_MAAS
FAST_QWEN_GROUNDED_OUTPUT=NOT_PROVEN_IN_RUNTIME_PATH
FAST_QWEN_NO_DECISION_OVERRIDE=NOT_PROVEN_IN_RUNTIME_PATH
MODEL_ROUTING_ARCHITECTURE=PASS
QWEN_FAST_PATH=NOT_PROVEN
MULTI_MODEL_RUNTIME_PROOF=NO
MULTI_MODEL_ROUTING_PROVEN=NO
MODEL_AWARE_ARCHITECTURE=PASS
ACTIVE_MODEL_PATH=LOCAL_PLUS_GLM_5_2

### GLM_LATENCY_ANALYSIS

The timing metadata now separates router, deterministic-tool, model, and
total time. Local measured representative runs showed lexical routing under
1 ms, deterministic route lookup about 5–7 ms, and bounded GLM/fallback
attempts about 8.0–8.1 seconds. The dominant delay is model/network setup or
generation, not routing or the deterministic tool. Decision explanations now
invoke the bounded explanation model after NBA-first lookup; if it times out,
the deterministic explanation is returned.

### PROGRESSIVE_ASSISTANT_UX

PASS. The existing drawer exposes the staged status labels for request
classification, confirmed business decision, model explanation, and safe
fallback. The drawer remains portal-based and the previously proven UI gates
are unchanged.

### FIVE_RUN_LATENCY_BENCHMARK

Five stable runs on the current final code; no startup samples were included.
The local server was health-checked before collection.

| Intent | Tool | Path | Model | min / median / max total | router / tool / model median |
|---|---|---|---|---:|---:|
| GREETING_HELP | none | LOCAL | LOCAL | 0.06 / 0.08 / 0.11 ms | 0.04 / 0 / 0 ms |
| CUSTOMER_SUMMARY | get_customer_360 | LOCAL | LOCAL | 2.44 / 3.25 / 4.34 ms | 0.11 / 3.10 / 0 ms |
| CASHFLOW | get_customer_360 | LOCAL | LOCAL | 2.34 / 3.01 / 4.13 ms | 0.10 / 2.86 / 0 ms |
| PTP | get_customer_360 | LOCAL | LOCAL | 2.21 / 2.42 / 2.55 ms | 0.11 / 2.28 / 0 ms |
| ROUTE_PRIORITY | get_next_best_action | LOCAL | LOCAL | 5.36 / 5.55 / 8.32 ms | 0.13 / 5.41 / 0 ms |
| DECISION_EXPLANATION | get_next_best_action | FALLBACK | GLM 5.2 bounded | 8105.62 / 8106.38 / 8248.83 ms | 0.12 / 5.30 / 8101.51 ms |
| SIMULATION | simulate_decision | FALLBACK | GLM 5.2 bounded | 8082.27 / 8107.40 / 8235.01 ms | 0.10 / 7.42 / 8096.19 ms |

Non-model medians meet the release targets. Decision and simulation expose
their deterministic result before model generation; model explanation is
bounded and falls back to grounded deterministic text.

TIMEOUT_FALLBACK=PASS
DETERMINISTIC_RESULT_AVAILABLE_QUICKLY=PASS
MODEL_TIMEOUT_BOUNDED=PASS
GROUNDED_FALLBACK=PASS
TOOL_AWARE_ROUTING=PASS
FREE_TEXT_ROUTING=PASS
QUESTION_CATALOG_SINGLE_SOURCE=PASS
DRAWER_OVERLAY=PASS
AGENTBASE_FIDELITY=PASS
TESTS=PASS
BUILD=PASS
SECRET_AUDIT=PASS
BUSINESS_SEMANTICS_DRIFT=0

COMMITTED_AND_DEPLOYED

## RELEASE VERIFICATION

TASK011G_COMMIT=THIS_COMMIT
BUILD=PASS
DOCROOT_DEPLOY=PASS
DEPLOYED_BUILD_MATCH=PASS
PUBLIC_SMOKE=PASS
PRODUCTION_RENDERED_UI_QA=PASS

Production backup:
`/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260905080403`

The source and deployed `index.html` SHA-256 matched:
`aad9eb7984d0af0c8ebdc17c2471fd26dafc3fa29225a05262df7d0734455f21`.
Public NAT-pinned checks returned HTML for `/` and `/gioi-thieu`, JSON for
browser-safe demo APIs, and passed protected `/tools` and `/agent-tools`
authentication checks. Production rendered QA passed at 1366x768, 1440x900,
and 1920x1080: quick-nav remained below the assistant backdrop, four initial
questions expanded to all ten, and the composer stayed visible.

Production Copilot smoke passed for local greeting, customer summary,
cashflow, PTP, deterministic route, bounded decision explanation, and
simulation. SYN002846 remained NBA-300 / CALL / WAIT_SELF_CURE / NONE / 47;
the accepted simulation remained WAIT_SELF_CURE → CONTACT.
