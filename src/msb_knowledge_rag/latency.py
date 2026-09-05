"""Per-phase latency measurement for the RAG pipeline (TASK-011H-A).

Each answered question emits classification_ms / embedding_ms / retrieval_ms /
model_ms / total_ms. retrieval_ms covers search+rerank; embedding_ms is the
query embedding only. The report gives min/median/max per phase.
"""

from __future__ import annotations

import statistics

from .service import KnowledgeRagService

PHASES = ("classification_ms", "embedding_ms", "retrieval_ms", "model_ms", "total_ms")


def answer_latency(service: KnowledgeRagService, question: str) -> dict:
    answer = service.answer(question)
    meta = dict(answer.meta or {})
    return {
        "question": question,
        "status": answer.status,
        "classification": answer.classification,
        **{phase: meta.get(phase, 0.0) for phase in PHASES},
    }


def latency_samples(
    service: KnowledgeRagService, questions: list[str]
) -> list[dict]:
    return [answer_latency(service, question) for question in questions]


def _stats(values: list[float]) -> dict:
    if not values:
        return {"min": 0.0, "median": 0.0, "max": 0.0, "mean": 0.0, "count": 0}
    return {
        "min": round(min(values), 3),
        "median": round(statistics.median(values), 3),
        "max": round(max(values), 3),
        "mean": round(sum(values) / len(values), 3),
        "count": len(values),
    }


def latency_report(service: KnowledgeRagService, questions: list[str]) -> dict:
    samples = latency_samples(service, questions)
    report: dict = {"samples": len(samples), "phases": {}}
    for phase in PHASES:
        values = [sample.get(phase, 0.0) for sample in samples if sample["status"] == "ANSWERED"]
        report["phases"][phase] = _stats(values)
    return report