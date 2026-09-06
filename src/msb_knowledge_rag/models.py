from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

QuestionType = Literal[
    "PROJECT_KNOWLEDGE",
    "CUSTOMER_DECISION_REQUIRED",
    "CUSTOMER_FACT_REQUIRED",
    "SIMULATION_REQUIRED",
    "SECURITY_SENSITIVE",
    "LOW_CONFIDENCE",
]


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    section: str
    topic: str
    audience: str
    content_type: str
    knowledge_version: str
    source_commit: str
    source_type: str
    implementation_status: str
    updated_at: str
    path: str = ""


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    title: str
    section: str
    topic: str
    audience: str
    knowledge_version: str
    source_commit: str
    source_type: str
    implementation_status: str
    heading: str
    order: int
    content: str

    def citation_label(self) -> str:
        return f"[{self.document_id}:{self.heading}]"


@dataclass(frozen=True)
class RetrievalHit:
    chunk: KnowledgeChunk
    score: float

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, RetrievalHit):
            return NotImplemented
        if self.score != other.score:
            return self.score < other.score
        return self.chunk.chunk_id < other.chunk.chunk_id

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, RetrievalHit):
            return NotImplemented
        if self.score != other.score:
            return self.score > other.score
        return self.chunk.chunk_id > other.chunk.chunk_id


@dataclass(frozen=True)
class RagAnswer:
    status: str
    path: str
    knowledge_type: str
    answer: str
    sources: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    classification: QuestionType = "PROJECT_KNOWLEDGE"


@dataclass(frozen=True)
class GoldenQuestion:
    question_id: str
    group: Literal["A", "B", "C", "D", "BOUNDARY", "SECURITY"]
    question: str
    expected_topics: tuple[str, ...] = ()
    expected_documents: tuple[str, ...] = ()
    expected_evidence: tuple[str, ...] = ()
    forbidden_claims: tuple[str, ...] = ()
    question_type: QuestionType = "PROJECT_KNOWLEDGE"
    expected_boundary: QuestionType | None = None