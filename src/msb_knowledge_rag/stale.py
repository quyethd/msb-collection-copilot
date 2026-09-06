from __future__ import annotations

from dataclasses import replace

from .config import KNOWLEDGE_VERSION, V1_KNOWLEDGE_VERSION, V1_VDB_INDEX
from .vdb_client import GreennodeVdbOpenSearchClient, VdbUnavailable

# Stale V1 product-structure claims that must NOT exist anywhere in the V2
# active corpus (STALE_PRODUCT_FACTS_ACTIVE=0).
STALE_PRODUCT_FACT_MARKERS = (
    "đường dẫn /gioi-thieu",
    "Hướng dẫn trang Giới thiệu hệ thống",
    "trang Giới thiệu hệ thống",
    "Giới thiệu hệ thống, Trợ lý",
    "Giới thiệu hệ thống và các bằng chứng",
)

# Navigation question used to prove the current menu is V2 (no stale
# "Giới thiệu hệ thống" claim in live answers).
STALE_NAV_QUESTION = "Menu bên trong khu vực ứng dụng gồm những trang nào?"
STALE_NAV_EXPECTED_DOCS = {"17-system-architecture", "11-overview-page-guide"}


def stale_product_fact_scan(chunks) -> dict:
    """STALE_PRODUCT_FACTS_ACTIVE: PASS only when no stale V1 product-structure
    marker appears in any active corpus chunk."""
    corpus_text = " ".join(chunk.content for chunk in chunks).lower()
    matches = [marker for marker in STALE_PRODUCT_FACT_MARKERS if marker in corpus_text]
    return {
        "STALE_PRODUCT_FACTS_ACTIVE": "PASS" if not matches else "FAIL",
        "stale_matches": matches,
    }


def v1_retrieval_leak_scan(service, questions: list[str] | None = None) -> dict:
    """V1_ACTIVE_RETRIEVAL_LEAK: PASS only when no retrieved chunk on the active
    store carries knowledge_version=TASK-011H-V1 (single-version corpus)."""
    from .evaluation import GOLDEN_QUESTIONS

    if questions is None:
        questions = [
            question.question
            for question in GOLDEN_QUESTIONS
            if question.group in ("A", "B", "C", "D")
        ]
    leaked = []
    v1_chunks = 0
    for question in questions:
        result = service.pipeline.retrieve(question=question)
        for hit in result.hits:
            if hit.chunk.knowledge_version == V1_KNOWLEDGE_VERSION:
                v1_chunks += 1
                leaked.append(question)
    return {
        "V1_ACTIVE_RETRIEVAL_LEAK": "PASS" if not leaked else "FAIL",
        "leaked_questions": sorted(set(leaked)),
        "v1_chunks_on_active_store": v1_chunks,
        "questions_checked": len(questions),
    }


def stale_navigation_answer_check(service) -> dict:
    """STALE_NAVIGATION_ANSWER: PASS only when the nav question is answered with
    V2 docs and the answer does not mention the removed sidebar page."""
    answer = service.answer(STALE_NAV_QUESTION)
    docs = [source["document_id"] for source in answer.sources]
    stale_claimed = "Giới thiệu hệ thống" in answer.answer
    ok = (
        answer.status == "ANSWERED"
        and any(doc in docs for doc in STALE_NAV_EXPECTED_DOCS)
        and not stale_claimed
    )
    return {
        "STALE_NAVIGATION_ANSWER": "PASS" if ok else "FAIL",
        "nav_status": answer.status,
        "nav_top_docs": docs,
        "nav_mentions_stale_claim": stale_claimed,
    }


def v1_index_preservation_check(config) -> dict:
    """V1_PRESERVED: PASS only when the live V1 index still holds documents with
    knowledge_version=TASK-011H-V1. NOT_RUN when the vDB is not configured."""
    if not config.greennode_vdb_configured():
        return {"V1_PRESERVED": "NOT_RUN", "reason": "vDB not configured"}
    v1_config = replace(config, grennode_vdb_index=V1_VDB_INDEX)
    client = GreennodeVdbOpenSearchClient(v1_config, dimension=384)
    try:
        versions = client.knowledge_versions()
    except VdbUnavailable as error:
        return {"V1_PRESERVED": "NOT_RUN", "reason": str(error)[:200]}
    count = versions.get(V1_KNOWLEDGE_VERSION, 0)
    return {
        "V1_PRESERVED": "PASS" if count > 0 else "FAIL",
        "v1_index": V1_VDB_INDEX,
        "v1_document_chunks": count,
        "versions": versions,
    }