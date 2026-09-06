from __future__ import annotations

import re
from pathlib import Path

from .config import KNOWLEDGE_VERSION, SOURCE_COMMIT
from .models import KnowledgeDocument

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)\Z", re.DOTALL
)
_KEY_RE = re.compile(r"^(?P<key>[a-z_]+)\s*:\s*(?P<value>.*)$")


class CorpusError(Exception):
    pass


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    fields: dict[str, str] = {}
    for raw_line in match.group("fm").splitlines():
        line = raw_line.strip()
        key_match = _KEY_RE.match(line)
        if not key_match:
            continue
        fields[key_match.group("key")] = key_match.group("value").strip().strip("'\"")
    return fields, match.group("body")


def load_document(path: Path) -> KnowledgeDocument:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    required = (
        "document_id",
        "title",
        "section",
        "topic",
        "audience",
        "content_type",
        "knowledge_version",
        "source_commit",
        "source_type",
        "implementation_status",
        "updated_at",
    )
    missing = [key for key in required if not meta.get(key)]
    if missing:
        raise CorpusError(f"{path.name}: missing frontmatter fields: {', '.join(missing)}")
    if meta["knowledge_version"] != KNOWLEDGE_VERSION:
        raise CorpusError(
            f"{path.name}: unsupported knowledge_version {meta['knowledge_version']!r}"
        )
    return KnowledgeDocument(
        document_id=meta["document_id"],
        title=meta["title"],
        section=meta["section"],
        topic=meta["topic"],
        audience=meta["audience"],
        content_type=meta["content_type"],
        knowledge_version=meta["knowledge_version"],
        source_commit=meta["source_commit"],
        source_type=meta["source_type"],
        implementation_status=meta["implementation_status"],
        updated_at=meta["updated_at"],
        path=str(path),
    )


def load_corpus(corpus_dir: Path) -> list[KnowledgeDocument]:
    if not corpus_dir.is_dir():
        raise CorpusError(f"corpus directory not found: {corpus_dir}")
    documents = []
    for path in sorted(corpus_dir.glob("*.md")):
        documents.append(load_document(path))
    if not documents:
        raise CorpusError(f"no markdown documents found in {corpus_dir}")
    return documents