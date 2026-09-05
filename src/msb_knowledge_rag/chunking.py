from __future__ import annotations

import hashlib
import re

from .corpus import _parse_frontmatter
from .models import KnowledgeChunk, KnowledgeDocument

_HEADING_RE = re.compile(r"^(?P<level>#+)\s+(?P<title>.+?)\s*$")


class ChunkingError(Exception):
    pass


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def chunk_document(document: KnowledgeDocument, body: str) -> list[KnowledgeChunk]:
    lines = body.splitlines()
    sections: list[dict] = []
    current_heading = document.title
    current_lines: list[str] = []
    section_order = 0

    for line in lines:
        match = _HEADING_RE.match(line)
        if match and match.group("level") in ("#", "##"):
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(
                        {
                            "heading": current_heading,
                            "order": section_order,
                            "content": content,
                        }
                    )
                    section_order += 1
            current_heading = match.group("title").strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(
                {
                    "heading": current_heading,
                    "order": section_order,
                    "content": content,
                }
            )

    if not sections:
        content = body.strip()
        if content:
            sections.append(
                {
                    "heading": document.title,
                    "order": 0,
                    "content": content,
                }
            )

    chunks: list[KnowledgeChunk] = []
    for section in sections:
        material = "\n".join(
            [
                document.document_id,
                document.title,
                section["heading"],
                section["content"],
            ]
        )
        chunk_id = (
            f"{document.document_id}::chunk::{section['order']:02d}-"
            f"{_stable_hash(material)}"
        )
        chunks.append(
            KnowledgeChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                title=document.title,
                section=document.section,
                topic=document.topic,
                audience=document.audience,
                knowledge_version=document.knowledge_version,
                source_commit=document.source_commit,
                source_type=document.source_type,
                implementation_status=document.implementation_status,
                heading=section["heading"],
                order=section["order"],
                content=section["content"],
            )
        )
    return chunks


def chunk_all(documents: list[KnowledgeDocument]) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for document in documents:
        body = _read_body(document)
        chunks.extend(chunk_document(document, body))
    return chunks


def _read_body(document: KnowledgeDocument) -> str:
    from pathlib import Path

    text = Path(document.path).read_text(encoding="utf-8")
    _, body = _parse_frontmatter(text)
    return body