# TASK-011H-A.1 — KNOWLEDGE V2 REFRESH AGAINST CURRENT MAIN (FINAL)

## Summary

TASK-011H-A.1 refreshes the Project Knowledge corpus to **TASK-011H-V2**,
aligned to current `main` (TASK-011I merged, `CURRENT_MAIN_COMMIT =
617a1ed84e6001155ae87b467bffbf962d3ce3cc`). The V2 corpus is ingested into a
**new GreenNode vDB index `msb-collection-knowledge-v2`** (live OpenSearch kNN),
the legacy V1 index `msb-collection-knowledge-v1`
is provably preserved, and a full live RAG proof (retrieval + Qwen Flash grounded
answers + security + latency + stale/leak admission) passes end-to-end.

Companion evidence: `task-results/TASK-011H-A1-LIVE-PROOF.json`
(`python -m msb_knowledge_rag.cli --provider local-multilingual --live live-proof`).

## What changed (V1 → V2)

- Product-structure truth re-derived from current `main` (TASK-011I):
  - Public landing/`/` = **Hướng dẫn trang giới thiệu sản phẩm (landing)** — the
    old **"Giới thiệu hệ thống"** page is **removed** and is now documented only
    as history inside doc `24` "Lịch sử phiên bản".
  - Access flow: `/login` demo auth (`/demo/auth/login`) → `/app`.
  - App menu (sidebar navigation) = **Tổng quan, Danh sách ưu tiên, Khách hàng,
    Tác động dự kiến** (+ Trợ lý); "Giới thiệu hệ thống" is **not** a sidebar page.
- Corpus sweeps:
  - All 26 documents frontmatter updated in lockstep:
    `knowledge_version=TASK-011H-V2`, `source_commit=617a1ed84e6001155ae87b467bffbf962d3ce3cc`,
    `updated_at=2026-09-06`.
  - Content rewritten in: `01` (product structure + platform), `02` (access flow),
    `11` (app menu/position), `15` (knowledge layer live status), `16` (full
    landing guide rewrite), `17` (FRONTEND + RAG-on-vDB section), `18`
    (live status + embedding + embedding-location + production admission),
    `21` (live proof + V2 verification), `23` (golden-question phrasing),
    `24` (versioning rewrite + history), `25` (roadmap implemented/GreenNode steps),
    `26` (glossary version fields).
- Golden set extended from 33 → **43 questions** adding **10 V2 questions**
  (C6 landing position, C7 access into the app, C8 app menu, C9 GreenNode usage,
   C10 GreenNode vDB, D7 embedding runs locally, D8 Qwen Flash role,
   D9 RAG never decides CALL/CBS, D10 knowledge live on GreenNode vDB,
   D11 RAG not integrated into the production assistant). D3 evidence tightened to
   `TASK-011H-V2`.
- Stale/leak admission (new `src/msb_knowledge_rag/stale.py`):
  - `STALE_PRODUCT_FACTS_ACTIVE=PASS` — zero V1 product-structure markers in the
    active corpus.
  - `V1_ACTIVE_RETRIEVAL_LEAK=PASS` — no retrieved chunk carries
    `knowledge_version=TASK-011H-V1`; on the V2 store the `knowledge_version`
    term aggregation reports exclusively `{"TASK-011H-V2": 129}`.
  - `STALE_NAVIGATION_ANSWER=PASS` — the app-menu question is answered from
    `11`/`17` and never mentions the removed page.
  - `V1_PRESERVED=PASS` — the live V1 index `msb-collection-knowledge-v1` still
    holds **120 chunks** tagged `TASK-011H-V1`.

## Status

**TASK-011H-A.1 KNOWLEDGE V2 LIVE — READY FOR COPILOT INTEGRATION**

```
CORPUS=PASS                        # 26 documents, all frontmatter TASK-011H-V2 / 617a1ed...
CHUNKING=PASS                      # deterministic H1+H2 boundaries, 129 chunks, stable chunk ids
KNOWLEDGE_VERSION=TASK-011H-V2
SOURCE_COMMIT=617a1ed84e6001155ae87b467bffbf962d3ce3cc
V1_INDEX=msb-collection-knowledge-v1          # preserved (V1_PRESERVED=PASS, 120 V1 chunks)
V2_INDEX=msb-collection-knowledge-v2          # V2_INDEX_CREATED=PASS, 129 V2 chunks
V1_ACTIVE_RETRIEVAL_LEAK=PASS
STALE_PRODUCT_FACTS_ACTIVE=PASS
STALE_NAVIGATION_ANSWER=PASS
GRENNODE_VDB_AVAILABLE=PASS
LIVE_VDB_INGEST=PASS
LIVE_VDB_RETRIEVAL=PASS
LIVE_QWEN_RAG=PASS
PROJECT_KNOWLEDGE_RAG_LIVE=PASS
INFERENCE_ANCHOR=LIVE_GREENNODE_VDB
DECISION_CORE_UNCHANGED=True
BUSINESS_SEMANTICS_DRIFT=0
COPILOT_INTEGRATION=NO
DEPLOY=NO
```

## Live evaluation (LIVE_GREENNODE_VDB anchor, semantic embedder)

Embedding remains the local `paraphrase-multilingual-MiniLM-L12-v2` (384d,
`EMBEDDING_MODEL_STATUS=LOCAL_MULTILINGUAL_AVAILABLE`, `SEMANTIC_MIN_SCORE=0.38`).
Live retrieval executes against the V2 GreenNode vDB index; live answers are
produced by Qwen Flash (`qwen/qwen3.6-flash`) with citation instructions.

| metric | V1 semantic live | V2 semantic live |
|---|---|---|
| Recall@3 | 1.0 | **1.0** |
| MRR | 0.8974 | **0.8981** |
| GROUNDING_PASS_RATE | 1.0 | **1.0** |
| CITATION_PASS_RATE | 1.0 | **1.0** |
| BOUNDARY_PASS_RATE | 1.0 | **1.0** |
| UNSUPPORTED_CLAIM_RATE | 0.0 | **0.0** |
| REFUSAL_PASS_RATE | 1.0 | **1.0** |
| D6 "Quyết định cuối cùng thuộc về ai?" | PASS | **PASS** |

```
eval_summary = {'total_questions': 43, 'knowledge_rows': 36, 'Recall@3': 1.0,
 'MRR': 0.8981, 'GROUNDING_PASS_RATE': 1.0, 'CITATION_PASS_RATE': 1.0,
 'BOUNDARY_PASS_RATE': 1.0, 'UNSUPPORTED_CLAIM_RATE': 0.0, 'REFUSAL_PASS_RATE': 1.0}
```

- Live-proof question set extended to 20 (incl. all 10 new V2 questions); every
  live answer is `ANSWERED` and cites its source `[n]`.
- Security gates: `SECRET_AUDIT=PASS`, `SECRET_QUERY_SAFE=PASS`,
  `PRIVATE_REASONING_AUDIT=PASS`.
- Latency harness recorded on the live path (per-phase min/median/max in the JSON
  artifact).

## Tests

`tests/test_task011h_a.py` + `tests/test_task011h_knowledge.py` — **61/61 PASS**
(semantic tier runs locally via fastembed). New A.1 coverage: V2 constants and
index names, golden-set membership + D3 evidence, corpus has no stale sidebar
phrase, `STALE_PRODUCT_FACTS_ACTIVE` scan on the corpus, `V1_ACTIVE_RETRIEVAL_LEAK`
pass/fail unit paths, live `stale_navigation_answer_check`, OpenSearch +
in-process `knowledge_versions()` aggregation, and `LIVE_PROOF_QUESTIONS`
extension.

## Scope

Self-contained V2 knowledge refresh in `/opt/msb-collection-copilot-task011h`.
No Copilot integration, no frontend change, no Decision Core change, no deploy,
no auto-merge.

## Blob summary

```
KNOWLEDGE_VERSION=TASK-011H-V2
SOURCE_COMMIT=617a1ed84e6001155ae87b467bffbf962d3ce3cc
V1_INDEX=msb-collection-knowledge-v1
V2_INDEX=msb-collection-knowledge-v2
V2_INDEX_CREATED=PASS
V1_PRESERVED=PASS
V1_ACTIVE_RETRIEVAL_LEAK=PASS
STALE_PRODUCT_FACTS_ACTIVE=PASS
STALE_NAVIGATION_ANSWER=PASS
DOCUMENTS=26
CHUNKS=129
RECALL_AT_3=1.0
MRR=0.8981
CITATION_PASS_RATE=1.0
BOUNDARY_PASS_RATE=1.0
UNSUPPORTED_CLAIM_RATE=0.0
LIVE_QWEN_RAG=PASS
LIVE_QWEN_RAG_V2=PASS
PROJECT_KNOWLEDGE_RAG_LIVE=PASS
BUSINESS_SEMANTICS_DRIFT=0
COPILOT_INTEGRATION=NO
DEPLOY=NO
```