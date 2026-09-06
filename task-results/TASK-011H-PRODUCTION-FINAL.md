# TASK-011H Production Integration + Deployment

## Integration

- `FINAL_MASTER_COMMIT=af3e6d63a02ed709d23854fc5db119d179ab5d22`
- `TASK011H_B_COMMIT=af3e6d6`
- `AF3E6D6_ALREADY_IN_MASTER=YES`
- `INTEGRATION_ACTION=NONE`
- `SOURCE_INTEGRATION=PASS`
- `KNOWLEDGE_VERSION=TASK-011H-V2`
- `VDB_INDEX=msb-collection-knowledge-v2`
- `BUSINESS_SEMANTICS_DRIFT=0`

The accepted TASK-011H-B source, RAG service, copilot boundary routing, V2 corpus, frontend integration, and tests are present on master. No business rules or RAG architecture were changed during production closure.

## Production Runtime

- `PRODUCTION_RAG_ENV=PASS`
- `RAG_EMBEDDING_PROVIDER=local-multilingual`
- `PRODUCTION_FASTEMBED=PASS`
- `PRODUCTION_EMBEDDING_LOAD=PASS`
- `PRODUCTION_EMBEDDING_DIMENSION=384`
- Production interpreter: `/root/miniconda3/bin/python3.14`
- Production process: root-owned `tool_server.py` on `127.0.0.1:18080`
- Model cache was readable by the production runtime; no model weights were committed.

## GreenNode VDB And Qwen

- `PRODUCTION_VDB_CONNECTIVITY=PASS`
- `PRODUCTION_VDB_AUTH=PASS`
- `PRODUCTION_VDB_TLS=PASS`
- `PRODUCTION_VDB_INDEX=msb-collection-knowledge-v2`
- `PRODUCTION_VDB_CHUNKS=129`
- `PRODUCTION_KNOWLEDGE_VERSION=TASK-011H-V2`
- `V1_PRESERVED=PASS`
- `PRODUCTION_QWEN_AVAILABLE=PASS`
- Qwen model: `qwen/qwen3.6-flash`
- `PRODUCTION_RAG_V2=PASS`
- `PRODUCTION_RAG_CITATIONS=PASS`

The VDB probe was read-only. No re-ingestion or V1 modification occurred.

## Deployment

- `BACKUP_PATH=/www/wwwroot/msb-collection-copilot.duckdns.org.backup-20260906T092600Z`
- `BACKEND_DEPLOY=PASS`
- `BACKEND_HEALTH=PASS`
- `FRONTEND_DEPLOY=PASS`
- `DEPLOYED_BUILD_MATCH=PASS`
- Static deployed artifacts are owned by `www:www`.
- `.user.ini`, `.htaccess`, and `.well-known` were preserved.

## Public Landing And Application QA

- `LANDING_PUBLIC=PASS`
- `LANDING_NO_OPERATIONAL_SIDEBAR=PASS`
- `LANDING_NO_HORIZONTAL_OVERFLOW=PASS`
- `LANDING_LOGIN_CTA=PASS`
- `VI_FIRST_CONTENT=PASS`
- `UNEXPLAINED_TECH_JARGON=0`
- `GREENNODE_VISIBLE_IN_HERO=PASS`
- `GREENNODE_DEDICATED_SECTION=PASS`
- `AGENTBASE_VISIBLE=PASS`
- `GLM_VISIBLE=PASS`
- `QWEN_VISIBLE=PASS`
- `VDB_VISIBLE=PASS`
- `LOCAL_EMBEDDING_TRUTHFUL=PASS`
- `DECISION_CORE_AUTHORITY_CLEAR=PASS`
- `PRODUCTION_LOGIN=PASS`
- `PRODUCTION_AUTH_GUARD=PASS`
- `PRODUCTION_LOGOUT=PASS`
- `PRODUCTION_COOKIE_SECURITY=PASS`
- `APPLICATION_REGRESSION=PASS`

Rendered public landing QA passed at 1366x768, 1440x900, 1920x1080, and 390x844. Authenticated rendered application QA passed for overview, priority, customer, impact, no horizontal overflow, and logout.

## Deterministic And Boundary QA

- `SYN002846_REGRESSION=PASS`
- Accepted result remains `CALL / WAIT_SELF_CURE / NONE / score 47`.
- `CUSTOMER_DECISION_BOUNDARY=PASS`
- `PRODUCTION_CUSTOMER_BOUNDARY=PASS`
- `PRODUCTION_FACT_BOUNDARY=PASS`
- `PRODUCTION_SIMULATION_BOUNDARY=PASS`
- `PRODUCTION_SECURITY_BOUNDARY=PASS`
- `PRODUCTION_LOW_CONFIDENCE_REFUSAL=PASS`

Decision, customer-fact, and simulation questions remained on deterministic/customer paths. The `.env` request was refused without RAG retrieval or secret disclosure.

## Production Copilot Knowledge QA

- `PRODUCTION_RAG_KNOWLEDGE=PASS`
- `PRODUCTION_RAG_CITATIONS=PASS`
- `PRODUCTION_RAG_V2=PASS`
- `VI_FIRST_ANSWER=PASS`
- `PROGRESSIVE_RAG_UX=PASS`

Knowledge questions returned `RAG_QWEN`, V2 metadata, and human-readable source titles. The low-confidence pho question returned the required Vietnamese refusal.

## Five-Query Production Latency

Measured metadata from five public production knowledge requests:

| Metric (ms) | Min | Median | Max |
|---|---:|---:|---:|
| classification_ms | 0.023 | 0.033 | 0.126 |
| embedding_ms | 234.393 | 266.776 | 2843.763 |
| retrieval_ms | 690.116 | 703.777 | 3577.661 |
| qwen_model_ms | 0.000 | 6673.957 | 12398.256 |
| total_ms | 690.780 | 10284.350 | 13103.060 |

The low-confidence request correctly skipped model generation (`model_ms=0`). Latency is reported as measured; no provider latency was hidden or altered.

## Tests And Security

- `TASK011H_TESTS=PASS` — 92 focused backend tests passed with socket permissions enabled.
- `FRONTEND_TESTS=50/50 PASS`
- `BUILD=PASS`
- `SECRET_AUDIT=PASS`
- `PRIVATE_REASONING_AUDIT=PASS`
- `BUSINESS_SEMANTICS_DRIFT=0`

The known `test_task008b.py` stale-auth assertions remain documented separately from TASK-011H: 64 passed plus 3 pre-existing assertions expecting old authentication behavior for browser-safe `/demo/timeline/`, `/demo/reset/`, and `/demo/events` routes. They are not TASK-011H regressions.

## Closure

- `TASK-011H=CLOSED`
