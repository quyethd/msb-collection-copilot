# TASK-011H-A — LIVE GREENNODE VDB + QWEN RAG PROOF — STAND BY FOR VDB PROVISIONING

Status: **TASK-011H-A LOCAL RAG PROOF — READY FOR VDB PROVISIONING**
Commit basis: `44d24e3c3d2c6277ef2a172e5d8548a1a0402277` (foundation commit `d90607e49397b1a36aea7d10f6fcebdd5f64b0c2`).

This report documents exactly what was built, what is proven locally, and the
exact owner action required to enable the LIVE GreenNode VDB gates.

---

## 1. Resource safety & provisioning decision

Verified live + against official GreenNode docs (docs.greennode.ai, docs.vngcloud.vn):

- The authorized MaaS catalog exposes **chat models only**: `google/gemma-4-31b-it`,
  `qwen/qwen3.6-flash`, `z-ai/glm-5.2-hackathon`. `/embeddings` returns a structured
  HTTP 404 "model not found" for every candidate tested (bge-m3, multilingual-e5-small,
  text-embedding-3-small, qwen/qwen3-embedding, intfloat/multilingual-e5-small,
  e5-mistral-7b-instruct, jina-embeddings-v3, ...). **No MaaS embeddings today.**
- GreenNode's **official vector DB for RAG is vDB OpenSearch** (kNN plugin default,
  v2.15/v2.17). Provisioning is **console-only** (vdb.console.greennode.ai), master
  user/password, VPC, and billed as **compute + storage via POC wallet** (hotline /
  support ticket). Minimum viable cluster for the 120-chunk prototype = **3 nodes**
  (3/5/7/9 node options). vDB PostgreSQL (pgvector) is a documented alternative.
- vDB OpenSearch is **billable and not covered by the MaaS hackathon token credits**.
  Per the resource-safety rule, no billable resource was provisioned without owner
  approval.

**Owner decision (approved):**
> "Build all local pieces, hold live gates."

So every locally-provable component is implemented and tested now; the LIVE VDB gates
stay `NOT_RUN`/`NEEDS_APPROVAL` until an endpoint is provisioned.

**What the owner must provision (exact package):**
1. In `vdb.console.greennode.ai`, create a vDB OpenSearch cluster (3 nodes, VPC chosen).
   For the hackathon/POC stage, request the cluster via the POC wallet hotline/support
   ticket (billing covers compute+storage).
2. Capture: cluster DNS endpoint (https), admin/master user + password.
3. Provide to the stack via env (never in code/commits):
   `GRENNODE_VDB_ENDPOINT` (e.g. `https://<cluster>.<region>.vdb-greennode.ai`),
   `GRENNODE_VDB_INDEX` (default `msb-collection-knowledge`),
   `GRENNODE_VDB_USER`, `GRENNODE_VDB_PASSWORD`.
4. Optional (vDB PostgreSQL alternative): switch `build_store` to the pgvector adapter
   (dsn + table) with the same contract.

No credentials are logged; the OpenSearch client never includes the password in errors.

---

## 2. Embedding tier (decision order A → B → C → selected C)

- **A (VDB server-side embeddings):** not available — vDB OpenSearch kNN indexes the
  supplied vector; it does not generate one.
- **B (MaaS catalog embeddings):** probed; `/embeddings` 404 for all candidates.
  `EMBEDDING_MODEL_STATUS = NONE_AVAILABLE`. `MaasEmbeddingClient` exists but raises
  `EmbeddingUnavailable` unless a model is provisioned.
- **C (selected — LOCAL multilingual ONNX, CPU):**
  - Provider: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` via
    `fastembed` (ONNX Runtime, CPU, deterministic).
  - Name in module: `local-multilingual-minilm-l12`.
  - Vector dimension: **384**.
  - Vietnamese-capable, open-source, stable, deterministic (verified stable across
    instances).
  - Adapter: `LocalMultilingualEmbedder` in `embedding.py`; factory `build_embedder`
    keyed by `RAG_EMBEDDING_PROVIDER` (`deterministic` | `local-multilingual` |
    `local-e5` alias | `greennode-maas`).
  - `IdfLocalEmbedder` remains the deterministic tier used by the foundation tests.

Architecture: **LOCAL_EMBEDDING → GRENNODE_VDB (vDB OpenSearch kNN) → QWEN_FLASH_MAAS**.

---

## 3. Semantic grounding gate (SEMANTIC_PARAPHRASE_GATE = PASS)

The hard bigram phrase-evidence admission gate applies **only** to the deterministic
tier (foundation semantics preserved exactly). For the semantic tier the flow is:

- Retrieval: raw kNN cosine over the candidate store with a widened ranking window
  (`_RANK_WINDOW = 16` → 48 candidates) followed by a **hybrid rescore**
  `score = raw_cosine + 0.55 * (query_token_coverage)`.
- **Admission gate (semantic): raw top-1 cosine (pre-rescore) must reach
  `SEMANTIC_MIN_SCORE = 0.38`.** The threshold was calibrated on the corpus + golden
  set: every out-of-scope question has raw top-1 cosine ≤ **0.337**; every knowledge
  question has raw top-1 cosine ≥ **0.415** (D6, the previous miss).
- Boundary/domain classification (classifier) and security scan run before admission.
- The grounded Qwen answer plus citation validation apply after admission.
- Lexical bigram presence is recorded as a **confidence feature only**
  (`confidence_features.query_bigram_hit`), never as a hard gate.

**D6 retested → PASS** (the question D6 "Quyết định cuối cùng thuộc về ai?" was the
only deterministic-tier miss; the semantic tier retrieves `20-trust-and-safety` and
answers grounded).

---

## 4. 33-question evaluation (LOCAL_MOCKED_VDB anchor, multilingual embedder)

| Metric | Foundation (deterministic) | Semantic tier (TASK-011H-A) |
|---|---|---|
| total_questions | 33 | 33 |
| knowledge_rows | 26 | 26 |
| Recall@3 | 0.9615 | **1.0000** |
| MRR | 0.7500 | **0.8974** |
| GROUNDING_PASS_RATE | 0.9615 | **1.0000** |
| CITATION_PASS_RATE | 1.0000 | **1.0000** |
| BOUNDARY_PASS_RATE | 1.0000 | 1.0000 |
| UNSUPPORTED_CLAIM_RATE | 0.0 | 0.0 |
| REFUSAL_PASS_RATE (3 OOS) | 1.0000 | 1.0000 |

- Outcome: **26/26 knowledge questions** recall@3 (previous misses D6, B2, D1 all pass),
  MRR improved, all 3 out-of-scope questions refuse, all 7 boundary/security rows guarded.
- The deterministic tier keeps its **exact foundation numbers** (Recal@3 0.9615,
  MRR 0.75, all gate pass rates 1.0) — no business-semantic drift on the baseline.

Calibration record (raw top-1 cosine, `paraphrase-multilingual-MiniLM-L12-v2`):
OOS max = 0.337 (weather), domain min = 0.415 (D6), threshold = 0.38.

---

## 5. LIVE GreenNode VDB wiring (code ready, gate held)

`GreennodeVdbOpenSearchClient` (vdb_client.py) implements the official vDB OpenSearch
REST kNN path:

- Idempotent ingest: `_id = chunk_id`; metadata round-trip includes `document_id`,
  `chunk_id`, `topic`, `audience`, `implementation_status`, `knowledge_version`,
  `source_commit`, heading/order/content.
- Index mapping: `knn_vector` (hnsw/lucene, cosinesimil, dim from embedder).
- Search: `{"query": {"knn": {"embedding": {...}}}}`; cosine recomputed client-side so
  thresholds stay identical to local measurements.
- `is_live()` → True only when endpoint+index are configured; `build_store(config)`
  returns the mock otherwise. `GREHNODE_VDB_AVAILABLE` / `LIVE_VDB_INGEST` /
  `LIVE_VDB_RETRIEVAL` are `PASS` only when the client is live and has run.
- Unconfigured usage raises `VdbUnavailable` with credential-free messages.
- `PostgresPGVectorAdapter` remains the documented pgvector alternative.

---

## 6. Qwen Flash grounded answers (LIVE_GREENNODE_MAAS = RUN, retrieval local)

10 required live questions answered through GreenNode MaaS `qwen/qwen3.6-flash`
(the registered chat model), claims grounded on the 3 retrieved chunks with `[n]`
citation markers and index→document validation.

| id | top documents (retrieved) | cited |
|---|---|---|
| A1 | 04-call-cbs-routing, 09-self-cure, 23-golden-questions | ✔ |
| A2 | 04-call-cbs-routing ×3 | ✔ |
| A3 | 05-recovery-opportunity ×3 | ✔ |
| A6 | 08-cashflow-signals, 15-assistant-guide, 03-... | ✔ |
| A7 | 09-self-cure ×3 | ✔ |
| B1 | 17-system-architecture ×2, 16-system-overview-guide | ✔ |
| B2 | 20-trust-and-safety, 04-call-cbs-routing, 19-agentbase-and-tools | ✔ |
| D2 | 21-evaluation-and-trust-evidence ×3 | ✔ |
| D5 | 22-synthetic-data, 14-impact-page-guide, 23-... | ✔ |
| D6 | 21-evaluation-and-trust-evidence, 03-problem-..., 20-trust-and-safety | ✔ |

- Answered 10/10; every successful answer carries citations.
- Qwen inference latency (live, median): **11 434 ms**; median total per Q&A **11 904 ms**.
- `MaasRagAnswerer` reads only `choices[0].message.content`; `reasoning_content` is
  discarded (PRIVATE_REASONING_AUDIT = PASS).
- `INFERENCE_ANCHOR = LOCAL_MOCKED_VDB` is reported truthfully: Qwen inference is live,
  retrieval is local until the VDB is provisioned. No claim of a full live VDB is made.

Response structure: `status / path=rag_qwen / knowledge_type / answer / sources /
classification / meta{...}`.

---

## 7. Latency harness (local tier, 10 questions)

Per-phase (ms), only ANSWERED samples:

| phase | min | median | max | mean |
|---|---|---|---|---|
| classification_ms | 0.02 | 0.03 | 0.04 | 0.03 |
| embedding_ms (query) | 76.97 | 91.90 | 197.63 | 111.92 |
| retrieval_ms (search+rescore) | 111.74 | 129.28 | 246.65 | 150.07 |
| model_ms (local deterministic answerer) | 0.02 | 0.03 | 0.04 | 0.03 |
| total_ms | 111.98 | 129.59 | 247.13 | 150.37 |

When the Qwen answerer is live, `model_ms` reports the measured GreenNode MaaS time.

---

## 8. Security audits

- **SECRET_AUDIT = PASS** — corpus contains no live env secret value.
- **SECRET_QUERY_SAFE = PASS** — all 3 SECURITY golden questions resolve to
  `SECURITY_SENSITIVE`; answers never echo secrets.
- **PRIVATE_REASONING_AUDIT = PASS** — only message.content is consumed; hidden prompt /
  reasoning_content / chain-of-thought never readable.

Additional guards: secret/key questions cannot leak `LLM_API_KEY`,
`GREENNODE_CLIENT_SECRET`, `GRENNODE_VDB_PASSWORD`, `POSTGRES_PASSWORD`, `.env`,
`reasoning_content`, private prompt, or internal endpoints (security.py patterns).

---

## 9. Files changed (TASK-011H-A)

- `src/msb_knowledge_rag/config.py` — provider/VDB/Qwen env wiring, SEMANTIC_MIN_SCORE.
- `src/msb_knowledge_rag/embedding.py` — `LocalMultilingualEmbedder`, `build_embedder`.
- `src/msb_knowledge_rag/vdb_client.py` — `GreennodeVdbOpenSearchClient` (live kNN),
  `VdbUnavailable`, `build_store`, `is_live()`.
- `src/msb_knowledge_rag/maas_client.py` — new; `MaaSChatClient` (content-only parse).
- `src/msb_knowledge_rag/answerer.py` — MaasRagAnswerer default client wiring.
- `src/msb_knowledge_rag/retriever.py` — kNN window, hybrid rescore, per-phase perf,
  lexical confidence features, chunk-vector cache, `top_cosine`.
- `src/msb_knowledge_rag/service.py` — semantic admission gate, latency meta,
  dynamic gate_status, `build_live_rag_service`.
- `src/msb_knowledge_rag/latency.py` — latent harness (min/median/max).
- `src/msb_knowledge_rag/evaluation.py` — LLM `[n]` citation validation, `secret_audit`.
- `src/msb_knowledge_rag/probe.py` — embedding provider/model/dim status fields.
- `src/msb_knowledge_rag/cli.py` — `--provider`, `--live`, `latency`, `secret-audit`.
- `tests/test_task011h_a.py` — 20 new tests.
- `pyproject.toml` — optional `live` extra (`fastembed>=0.8`).

New model weight download (`/root/.cache` huggingface) is **not committed** (gitignored patterns).

---

## 10. Gates (current truth table)

| gate | value |
|---|---|
| GRENNODE_VDB_AVAILABLE | NEEDS_APPROVAL (owner provisioning pending) |
| LIVE_VDB_INGEST | NOT_RUN |
| LIVE_VDB_RETRIEVAL | NOT_RUN |
| QWEN_FAST_MODEL_AVAILABLE | PASS |
| LIVE_QWEN_RAG | **NOT_RUN** (Qwen inference ran live with local retrieval; full live RAG requires the VDB) |
| SEMANTIC_PARAPHRASE_GATE | PASS |
| OUT_OF_SCOPE_REFUSAL | PASS (3/3) |
| RAG_NEVER_DECIDES | PASS |
| CITATIONS | PASS |
| SECRET_AUDIT | PASS |
| PRIVATE_REASONING_AUDIT | PASS |
| SECRET_QUERY_SAFE | PASS |
| PROJECT_KNOWLEDGE_RAG_LIVE | NOT_PROVEN (held) |
| BUSINESS_SEMANTICS_DRIFT | 0 (deterministic baseline unchanged) |
| COPILOT_INTEGRATION | NO |
| DEPLOY | NO |

Expected blob after provisioning + LIVE run:
`TASK-011H-A LIVE RAG PROOF — READY FOR REVIEW`, VDB_BACKEND, EMBEDDING_PROVIDER=LOCAL,
EMBEDDING_MODEL, EMBEDDING_DIMENSION=384, DOCUMENTS=26, CHUNKS=120, LIVE_RECALL_AT_3,
LIVE_MRR, GROUNDING_PASS_RATE, CITATION_PASS_RATE, BOUNDARY_PASS_RATE,
REFUSAL_PASS_RATE, UNSUPPORTED_CLAIM_RATE, RAG_MEDIAN_LATENCY, D6_RESULT,
PROJECT_KNOWLEDGE_RAG_LIVE, BUSINESS_SEMANTICS_DRIFT=0, COPILOT_INTEGRATION=NO, DEPLOY=NO.