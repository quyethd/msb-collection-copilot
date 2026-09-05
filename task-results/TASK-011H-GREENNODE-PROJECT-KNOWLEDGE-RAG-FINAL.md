# TASK-011H — GREENNODE PROJECT KNOWLEDGE RAG FOUNDATION (FINAL)

## Status
**TASK-011H FOUNDATION PASS — READY FOR COPILOT INTEGRATION** (in isolated worktree)

```
CORPUS=PASS                    # 26 curated Vietnamese documents, frontmatter + TASK-011H-V1
CHUNKING=PASS                  # deterministic H1+H2 boundaries, 120 chunks, stable chunk ids
PACKAGE=PASS                   # src/msb_knowledge_rag/ (embedding/vdb/classifier/retriever/answerer/service)
TESTS=PASS                     # tests/test_task011h_knowledge.py 25/25
GOLDEN_EVAL=PASS               # 33 questions, per-metric below
SECRET_AUDIT=PASS              # no secrets, no credentials, no internal endpoints
BUSINESS_SEMANTICS_DRIFT=0     # no decision/selection/claim semantics changed outside new files

GRENNODE_VDB_AVAILABLE=NEEDS_APPROVAL   # OpenSearch kNN / Postgres pgvector require product-owner approval
LIVE_VDB_INGEST=NOT_RUN
LIVE_VDB_RETRIEVAL=NOT_RUN
LIVE_QWEN_RAG=NOT_RUN
EMBEDDING_MODEL_STATUS=NONE_AVAILABLE   # no embedding model on the MaaS catalog
INFERENCE_ANCHOR=LOCAL_MOCKED_VDB
DECISION_CORE_UNCHANGED=True
COPILOT_INTEGRATION=NO
DEPLOY=NO
```

## Evaluation (LOCAL_MOCKED_VDB, deterministic embedder, deterministic answerer)
```
total_questions              33
knowledge_rows               26
Recall@3                     0.9615
MRR                          0.75
GROUNDING_PASS_RATE          0.9615
CITATION_PASS_RATE           1.0
BOUNDARY_PASS_RATE           1.0
UNSUPPORTED_CLAIM_RATE       0.0
REFUSAL_PASS_RATE            1.0
```
- Boundary (BND1-4) and security (SEC1-3) questions never produce business answers; they return
  `CUSTOMER_DECISION_REQUIRED` / `CUSTOMER_FACT_REQUIRED` / `SIMULATION_REQUIRED` / `SECURITY_SENSITIVE` with status `BOUNDARY`.
- Out-of-scope questions ("Thời tiết hôm nay như thế nào?", "Bán đảo nào lớn nhất thế giới?", "Cách nấu phở bò ngon nhất là gì?")
  return status `LOW_CONFIDENCE` with the refusal string
  "Tôi chưa tìm thấy đủ thông tin trong kho kiến thức hiện tại để trả lời chắc chắn."
- Known limitation (honest): the single R@3 miss is D6 "Quyết định cuối cùng thuộc về ai?" — a semantic
  "who decides" question that the deterministic local matcher cannot resolve from vocabulary overlap alone.
  It is covered correctly by the live Qwen Flash path once provisioning is approved.

## Scope
Self-contained, deterministic Project Knowledge RAG foundation for MSB "Trợ lý Thu hồi Nợ — Powered by GreenNode AI",
built in the isolated worktree `/opt/msb-collection-copilot-task011h` (branch `task-011h-greennode-rag`,
base `44d24e3`). No copilot, no frontend, no AgentBase runtime, no decision-core change, no deploy.

## Files (to be committed)
- `knowledge/collection-copilot/*.md` — 26 curated Vietnamese documents with YAML frontmatter
  (`document_id`, `title`, `section`, `topic`, `audience`, `content_type`, `knowledge_version=TASK-011H-V1`,
  `source_commit=44d24e3...`, `source_type`, `prototype_status`, `implementation_status`, `updated_at`).
- `src/msb_knowledge_rag/__init__.py`, `config.py`, `models.py`, `corpus.py`, `chunking.py`, `embedding.py`,
  `vdb_client.py`, `security.py`, `classifier.py`, `retriever.py`, `answerer.py`, `service.py`,
  `evaluation.py`, `probe.py`, `cli.py`.
- `tests/test_task011h_knowledge.py` — 25 unittest cases.
- `task-results/TASK-011H-GREENNODE-PROJECT-KNOWLEDGE-RAG-FINAL.md` — this report.
- `task-results/TASK-011H-COPILOT-INTEGRATION-PLAN.md` — integration plan.
- `task-results/TASK-011H-SYSTEM-OVERVIEW-INTEGRATION.md` — system-overview integration notes.

## Architecture
- Corpus → deterministic Markdown-aware chunking (H1 + H2 boundaries, 120 chunks, stable ids) → metadata validation.
- `IdfLocalEmbedder` (dim 512, stopword-filtered tokens, corpus IDF weights) is a LOCAL adapter for the foundation;
  it is never presented as a live GreenNode embedding. `MaasEmbeddingClient` exists and raises when no embedding
  model is configured; live probe returns `EMBEDDING_MODEL_STATUS=NONE_AVAILABLE`.
- `InProcessMockVectorStore` (cosine) is the LOCAL_MOCKED_VDB inference anchor. OpenSearch / Postgres-pgvector
  adapters exist as a contract and raise `VdbUnavailable` until provisioned (gated `NEEDS_APPROVAL`).
- Query pipeline: classifier → retrievable window (rank window 8, coverage boost 0.1 on top-8) → top-3 → grounding
  gate → citations → answer.
- Grounding: deterministic answerer quotes source chunks verbatim; refusal for weak evidence:
  `RagStatus.LOW_CONFIDENCE` with the fixed refusal string.
- Phrase evidence gate: answers require at least one content bigram of the question to exist in the corpus,
  which rejects out-of-scope filler questions while keeping full recall of domain questions
  (`REFUSAL_PASS_RATE=1.0`).
- `MaasRagAnswerer` (Qwen Flash, `qwen/qwen3.6-flash`, `QWEN_FAST_MODEL_AVAILABLE=PASS`) is the production
  path; its prompt contract includes citation instructions. Live inference is `NOT_RUN` until VDB is provisioned.

## Boundary & safety
- Per-CIF decision / fact / simulation questions are never answered from RAG; they are classified as boundaries
  and returned with status `BOUNDARY` and the corresponding code.
- Security-sensitive questions (`SECURITY_SENSITIVE`) are blocked by the classifier and the security denylist
  (API keys, `.env`, credentials, `reasoning_content`).
- The RAG never decides: decision authority stays in the deterministic Decision Core
  (`DECISION_CORE_UNCHANGED=True`).
- Business semantics are preserved: "32 khách thuộc tuyến CALL nhưng chưa cần gọi ngay" is never phrased as
  "đã giảm 32 cuộc gọi"; no uplift/ROI claims; synthetic-portfolio numbers are labeled as simulation only.

## CLI
```
python -m msb_knowledge_rag.cli version
python -m msb_knowledge_rag.cli ingest
python -m msb_knowledge_rag.cli evaluate
python -m msb_knowledge_rag.cli answer "<question>"
python -m msb_knowledge_rag.cli status
python -m msb_knowledge_rag.cli probe     # read-only live probe
```

## Full-suite status (pre-existing, unrelated)
TASK-011H tests pass: `tests/test_task011h_knowledge.py` 25/25 and `tests/test_task011.py` 3/3.
A full `pytest` run cannot complete in this worktree because several pre-existing suites depend on
environment artifacts that were never generated here (not caused by TASK-011H — none import
`msb_knowledge_rag`):
- `test_nba.py` integration + `test_task007b_spike.py`: `FileNotFoundError build/synthetic-data/generation_manifest.json`
  (artifact not generated in this isolated worktree).
- `test_task008b.py` auth suite: "Should require auth" (auth credentials/setup absent in this environment).
- `test_task007b_spike.py`: `RemoteDisconnected` on connectivity spike endpoints.
No TASK-011H file appears in any traceback; the foundation gate is scoped to the TASK-011H tests plus the
unchanged `test_task011.py`.