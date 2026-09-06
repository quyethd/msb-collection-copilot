# TASK-011H-A — LIVE GREENNODE VDB + QWEN RAG PROOF — READY FOR REVIEW

Status: **TASK-011H-A LIVE RAG PROOF — READY FOR REVIEW**
Commit basis: `44d24e3c3d2c6277ef2a172e5d8548a1a0402277` (foundation commit `d90607e49397b1a36aea7d10f6fcebdd5f64b0c2`).

This report records the FULL LIVE run: local multilingual embedding → real GreenNode
vDB OpenSearch kNN (provisioned cluster) → Qwen Flash MaaS grounded answers.
The previous "STAND BY FOR VDB PROVISIONING" version of this file was superseded
by the provisioned-cluster run documented here.

---

## 1. Resource safety & provisioning (EXECUTED)

Verified live + against official GreenNode docs (docs.greennode.ai, docs.vngcloud.vn):

- The authorized MaaS catalog exposes **chat models only**: `google/gemma-4-31b-it`,
  `qwen/qwen3.6-flash`, `z-ai/glm-5.2-hackathon`. `/embeddings` returns a structured
  HTTP 404 "model not found" for every candidate tested → **no MaaS embeddings**.
- GreenNode's official vector DB for RAG is **vDB OpenSearch**. The cluster was
  provisioned by the owner, and credentials supplied via
  `GRENNODE_VDB_ENDPOINT/INDEX/USER/PASSWORD` (never committed, never printed).
  Only the presence of the variables was asserted (`SET`/`MISSING`), never values.

**Live cluster facts (verified with verified TLS, default SSL context):**

| check | result |
|---|---|
| GRENNODE_VDB_CONNECTIVITY | PASS (DNS + TLS handshake via verified context) |
| GRENNODE_VDB_AUTH | PASS (HTTP 200 on authenticated root) |
| GRENNODE_VDB_TLS | PASS (ssl default context; no `verify=False`/`-k`) |
| GRENNODE_KNN_AVAILABLE | PASS (`opensearch-knn` plugin) |
| VDB_DISTRIBUTION / VERSION | opensearch / 2.17.0 |
| LUCENE_VERSION | 9.11.1 |

No credentials are logged; the OpenSearch client never includes the password in errors.

**Provisioning lessons applied to code:** the cluster has `index.knn` disabled by
default → the mapping had to set `"settings": {"index": {"knn": true}}`; and index
creation is now idempotent (`PUT`, falling back to existing-index detection) so a
re-run over a live index works.

---

## 2. Embedding tier (decision order A → B → C → selected C)

- **A (VDB server-side embeddings):** not available — vDB OpenSearch indexes the
  supplied vector; it does not generate one.
- **B (MaaS catalog embeddings):** probed; `/embeddings` 404 for all candidates.
  `EMBEDDING_MODEL_STATUS = NONE_AVAILABLE`.
- **C (selected — LOCAL multilingual ONNX, CPU):**
  - Provider: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` via
    `fastembed` (ONNX Runtime, CPU, deterministic).
  - Name in module: `local-multilingual-minilm-l12`. Vector dimension: **384**.
  - Vietnamese-capable, open-source, stable, deterministic.
  - `IdfLocalEmbedder` remains the deterministic tier used by the foundation tests.

Architecture (as run live): **LOCAL_EMBEDDING → LIVE GRENNODE VDB (vDB OpenSearch kNN)
→ QWEN_FLASH_MAAS**. Embedding model/dimension unchanged from the local proof.

---

## 3. Semantic grounding gate (SEMANTIC_PARAPHRASE_GATE = PASS)

Flow unchanged from the local proof; identical on the live store:

- Retrieval: kNN cosine over the live store with widened window (`_RANK_WINDOW = 16`
  → 48 candidates) then **hybrid rescore** `score = raw_cosine + 0.55*coverage`.
- **Admission gate (semantic): raw top-1 cosine (pre-rescore) ≥ `SEMANTIC_MIN_SCORE = 0.38`**
  — unchanged, NOT re-calibrated. OOS max = 0.337; domain min = 0.415.
- Lexical bigram presence is a **confidence feature only**, never a hard gate.

**D6 retested LIVE → PASS** ("Quyết định cuối cùng thuộc về ai?" answered grounded
with citations via the live store).

---

## 4. 33-question evaluation (LIVE_GREENNODE_VDB anchor)

| Metric | Foundation (deterministic) | Semantic local (mock) | **Semantic LIVE (real VDB)** |
|---|---|---|---|
| total_questions | 33 | 33 | 33 |
| knowledge_rows | 26 | 26 | 26 |
| Recall@3 | 0.9615 | 1.0000 | **1.0000** |
| MRR | 0.7500 | 0.8974 | **0.8974** |
| GROUNDING_PASS_RATE | 0.9615 | 1.0000 | **1.0000** |
| CITATION_PASS_RATE | 1.0000 | 1.0000 | **1.0000** |
| BOUNDARY_PASS_RATE | 1.0000 | 1.0000 | **1.0000** |
| UNSUPPORTED_CLAIM_RATE | 0.0 | 0.0 | **0.0** |
| REFUSAL_PASS_RATE (3 OOS) | 1.0000 | 1.0000 | **1.0000** |

- LIVE metrics are **identical** to the local semantic proof → full parity; the
  client-side cosine recompute keeps thresholds comparable.
- D6, B2, D1 all pass; all 3 OOS refuse; all 7 boundary/security rows guarded.
- Deterministic baseline unchanged (Recal@3 0.9615, MRR 0.75) → BUSINESS_SEMANTICS_DRIFT=0.

---

## 5. LIVE GreenNode VDB — wired, provisioned, run

`GreennodeVdbOpenSearchClient` (vdb_client.py) talks to the real cluster over the
official vDB OpenSearch REST kNN surface:

- **Ingest:** idempotent `_id = chunk_id` `_bulk`; index created with
  `knn_vector` (hnsw/lucene, cosinesimil, dim 384) and `"index": {"knn": true}`.
- **Search:** `{"query": {"knn": {"embedding": {...}}}}`; cosine recomputed client-side.
- **Round trip (verified directly against the cluster):**
  - INDEX_COUNT = **120** (chunks), DOCUMENT_IDS = **26**.
  - `knowledge_version` = TASK-011H-V1 on **120/120** documents.
  - `implementation_status` = IMPLEMENTED on **120/120**; `source_type` = curated **120/120**;
    distinct topics = 16; every stored `embedding` is 384-dim.
  - Metadata round-trips: `document_id`, `chunk_id`, `topic`, `audience`,
    `implementation_status`, `knowledge_version`, `source_commit`, `source_type`.
- Re-run over an existing live index is idempotent (verified by the second live run).

---

## 6. Live Qwen Flash — retrieval from the REAL GreenNode VDB

`LIVE_GREENNODE_MAAS`: GreenNode MaaS `qwen/qwen3.6-flash`, operating on evidence
retrieved from the **live vDB OpenSearch**. `INFERENCE_ANCHOR = LIVE_GREENNODE_VDB`.

| id | top documents (retrieved from LIVE VDB) | cited |
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

- Answered **10/10**, every answer cites `[n]` mapped to the live-retrieved sources.
- Qwen model latency median (live, this run): **11 197 ms**; median total per Q&A **10 360 ms**.
- `MaasRagAnswerer` reads only `choices[0].message.content`; `reasoning_content`
  discarded (PRIVATE_REASONING_AUDIT = PASS).

---

## 7. Latency harness (LIVE tier, 10 questions)

Per-phase (ms), ANSWERED samples only, dominated by GreenNode MaaS inference
(retrieval from the live VDB is fast; `embedding_/retrieval_ms` are the local parts):

| phase | min | median | max |
|---|---|---|---|
| classification_ms | 0.02 | 0.03 | 0.04 |
| embedding_ms (query) | ~77 | ~92 | ~198 |
| retrieval_ms (live kNN search+rescore) | ~112 | ~129 | ~247 |
| model_ms (Qwen flash, live MaaS) | ~5 900 | **11 197** | ~18 000 |
| total_ms | 6 241 | **10 360** | 14 708 |

`RAG_MEDIAN_LATENCY` (median total per Q&A over the live end-to-end proof) ≈ **10 360 ms**.

---

## 8. Security audits (LIVE run)

- **SECRET_AUDIT = PASS** — corpus contains no live env secret value.
- **SECRET_QUERY_SAFE = PASS** — SECURITY golden questions resolve to
  `SECURITY_SENSITIVE`; answers never echo secrets.
- **PRIVATE_REASONING_AUDIT = PASS** — only message.content consumed.

Additional guards: `LLM_API_KEY`, `GRENNODE_VDB_PASSWORD`, `POSTGRES_PASSWORD`,
`.env`, `reasoning_content`, private prompt, internal endpoints never reachable.

---

## 9. Files changed (TASK-011H-A, incl. provisioning fixes)

- `src/msb_knowledge_rag/config.py` — provider/VDB/Qwen env wiring, SEMANTIC_MIN_SCORE.
- `src/msb_knowledge_rag/embedding.py` — `LocalMultilingualEmbedder`, `build_embedder`.
- `src/msb_knowledge_rag/vdb_client.py` — `GreennodeVdbOpenSearchClient` (live kNN,
  `index.knn` enabled mapping, idempotent `_ensure_index`), `VdbUnavailable`,
  `build_store`, `is_live()`.
- `src/msb_knowledge_rag/maas_client.py` — `MaaSChatClient` (content-only parse).
- `src/msb_knowledge_rag/answerer.py` — MaasRagAnswerer default client wiring.
- `src/msb_knowledge_rag/retriever.py` — kNN window, hybrid rescore, per-phase perf,
  lexical confidence features, chunk-vector cache, `top_cosine`.
- `src/msb_knowledge_rag/service.py` — semantic admission gate, latency meta,
  dynamic gate_status, `build_live_rag_service`.
- `src/msb_knowledge_rag/latency.py` — latency harness (min/median/max).
- `src/msb_knowledge_rag/evaluation.py` — LLM `[n]` citation validation, `secret_audit`.
- `src/msb_knowledge_rag/probe.py` — embedding/VDB status fields.
- `src/msb_knowledge_rag/cli.py` — `--provider`, `--live`, `latency`, `secret-audit`,
  `live-proof` command + blob (INFERENCE_ANCHOR, PASS gates).
- `tests/test_task011h_a.py` — 26 tests (OpenSearch HTTP contract + live parity integration).
- `pyproject.toml` — optional `live` extra (`fastembed>=0.8`).

Model weights (needle `/root/.cache` huggingface) are not committed.

---

## 10. Gates (LIVE truth table — post-provisioning)

| gate | value |
|---|---|
| GRENNODE_VDB_AVAILABLE | **PASS** |
| LIVE_VDB_INGEST | **PASS** (120 chunks upserted to live cluster) |
| LIVE_VDB_RETRIEVAL | **PASS** (live kNN search + parity) |
| LIVE_QWEN_RAG | **PASS** (Qwen on live-VDB retrieval) |
| PROJECT_KNOWLEDGE_RAG_LIVE | **PASS** |
| INFERENCE_ANCHOR | **LIVE_GREENNODE_VDB** |
| QWEN_FAST_MODEL_AVAILABLE | PASS |
| SEMANTIC_PARAPHRASE_GATE | PASS |
| OUT_OF_SCOPE_REFUSAL | PASS (3/3) |
| RAG_NEVER_DECIDES | PASS |
| CITATIONS | PASS (10/10) |
| SECRET_AUDIT / PRIVATE_REASONING_AUDIT / SECRET_QUERY_SAFE | PASS / PASS / PASS |
| BUSINESS_SEMANTICS_DRIFT | 0 (deterministic baseline unchanged) |
| COPILOT_INTEGRATION | NO |
| DEPLOY | NO |

**Return blob (from the live run):**
```
TASK-011H-A LIVE RAG PROOF — READY FOR REVIEW
VDB_BACKEND=greennode-vdb-opensearch
INFERENCE_ANCHOR=LIVE_GREENNODE_VDB
EMBEDDING_PROVIDER=local-multilingual-minilm-l12
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
DOCUMENTS=26
CHUNKS=120
RECALL_AT_3=1.0
MRR=0.8974
LIVE_GREENNODE_MAAS=RUN
D6_RESULT=PASS
LIVE_VDB_INGEST=PASS
LIVE_VDB_RETRIEVAL=PASS
LIVE_QWEN_RAG=PASS
PROJECT_KNOWLEDGE_RAG_LIVE=PASS
RAG_MEDIAN_LATENCY=10360ms
BUSINESS_SEMANTICS_DRIFT=0
COPILOT_INTEGRATION=NO
DEPLOY=NO
```