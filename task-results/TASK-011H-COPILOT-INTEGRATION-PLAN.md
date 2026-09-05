# TASK-011H — COPILOT INTEGRATION PLAN

## Context
TASK-011H delivered the Project Knowledge RAG foundation in an isolated worktree with
`INFERENCE_ANCHOR=LOCAL_MOCKED_VDB`. This plan describes the continuation work required before the
knowledge RAG can serve the customer-facing copilot in production.

## Current gates (must be lifted in order)
```
1  GRENNODE_VDB_AVAILABLE   NEEDS_APPROVAL   # product-owner approval for OpenSearch (kNN) or PostgreSQL (pgvector)
2  EMBEDDING_MODEL_STATUS   NONE_AVAILABLE   # no embedding model on the MaaS catalog; provision one
3  LIVE_VDB_INGEST          NOT_RUN          # after 1+2: run ingest on the live store
4  LIVE_VDB_RETRIEVAL       NOT_RUN          # after 3: golden-question retrieval live
5  LIVE_QWEN_RAG            NOT_RUN          # after 4: grounded answers via qwen/qwen3.6-flash
6  COPILOT_INTEGRATION      NO               # after 5: wire into msb_agent/msb_tools and the demo copilot
7  DEPLOY                   NO               # after 6, with product approval
```

## Step-by-step

### 1. Provision the vector database (approval required)
- Choose OpenSearch with kNN (`greennode` infra) or Postgres+pgvector in the product environment.
- Fill `KnowledgeRagConfig` (`vdb_kind=opensearch|postgres`, hosts, index, credentials via env vars only).
- Extend `OpenSearchVdbClient`/`PostgresVdbClient` in `src/msb_knowledge_rag/vdb_client.py` with real clients
  and map vectors to the configured embedding dimension (512 for the local embedder; use the provisioned
  model's dimension if changing).
- Re-run `python -m msb_knowledge_rag.cli status` → expect `GRENNODE_VDB_AVAILABLE=AVAILABLE`.

### 2. Provision an embedding model
- Register an embedding model on the MaaS catalog; set `embedding_model` in config.
- Re-run `python -m msb_knowledge_rag.cli probe` → expect `EMBEDDING_MODEL_STATUS=AVAILABLE`.
- Re-fit `IdfLocalEmbedder` weights are optional once real embeddings are used; keep the deterministic
  embedder only as a fallback/test fixture.

### 3. Ingest the corpus into the live store
- `python -m msb_knowledge_rag.cli ingest` against the live VDB.
- Verify chunk count (120) and metadata (`knowledge_version=TASK-011H-V1`) round-trip.

### 4. Live retrieval verification
- Re-run `python -m msb_knowledge_rag.cli evaluate` with `INFERENCE_ANCHOR=LIVE_GREENNODE_VDB`.
- Track Recall@3 / MRR vs baseline (0.9615 / 0.75) and the D6 miss; expect closure of D6 under real
  embeddings (semantic "who decides" question).

### 5. Whole product: RETRIEVAL gate inside `KnowledgeRagService.answer`
- Keep grounding gate and phrase-evidence gate; switch to real embeddings; keep `LOW_CONFIDENCE` refusal.
- Re-run the 33-question evaluation with LR:QGwen Flash — require the same grounded/citation quality.

### 6. Copilot integration (separate task with owner approval)
- Expose `onUserQuery` surface, i.e. a Q&A tool in `msb_tools` that calls `KnowledgeRagService`.answer
  and returns the grounded answer + sources; the Agent explains from retrieved chunks, never fabricates.
- Keep the boundary classifier before retrieval for per-CIF decision/fact/simulation and security questions.
- Add regression coverage: golden 33 under live anchor, boundary refusal, refusal strings unmodified.

### 7. Deploy (product approval)
- Build, run `SECRET_AUDIT`, deploy the docroot; verify the running demo answers matches the committed
  evaluation on a realistic sample.

## Non-goals (sticky)
- The RAG never decides business decisions; per-CIF actions remain deterministic Decision Core outputs.
- No uplift/ROI claims; simulation numbers stay labeled as synthetic portfolio data.
- No runtime IDs, credentials, internal endpoints, or private reasoning exposure in any output.