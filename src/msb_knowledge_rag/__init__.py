from __future__ import annotations

from .config import (
    KNOWLEDGE_VERSION,
    SOURCE_COMMIT,
    KnowledgeRagConfig,
)
from .models import GoldenQuestion, KnowledgeChunk, KnowledgeDocument, RagAnswer
from .service import KnowledgeRagService

__version__ = "1.0.0"
__task_id__ = "TASK-011H"

__all__ = [
    "KNOWLEDGE_VERSION",
    "SOURCE_COMMIT",
    "KnowledgeRagConfig",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "RagAnswer",
    "GoldenQuestion",
    "KnowledgeRagService",
    "__version__",
    "__task_id__",
]