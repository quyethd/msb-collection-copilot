from __future__ import annotations

from typing import Protocol

from .config import KnowledgeRagConfig
from .models import KnowledgeChunk

_MAX_SOURCE_CHARACTERS = 9000


class RagAnswerer(Protocol):
    def answer(self, question: str, chunks: list[KnowledgeChunk]) -> str: ...


def _build_prompt(question: str, chunks: list[KnowledgeChunk]) -> str:
    sources: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        snippet = chunk.content
        if len(snippet) > _MAX_SOURCE_CHARACTERS:
            snippet = snippet[:_MAX_SOURCE_CHARACTERS] + "..."
        sources.append(
            f"[{index}] document_id={chunk.document_id}\n"
            f"title={chunk.title}\n"
            f"section={chunk.section}\n"
            f"heading={chunk.heading}\n"
            f"knowledge_version={chunk.knowledge_version}\n"
            f"content:\n{snippet}"
        )
    block = "\n\n".join(sources)
    return (
        "Bạn là trợ lý hỗ trợ cán bộ thu hồi nợ. Dựa DUY NHẤT trên các đoạn tài "
        "liệu trong kho kiến thức dưới đây, trả lời câu hỏi của người dùng bằng "
        "tiếng Việt.\n\n"
        "QUY TẮC:\n"
        "- Chỉ dùng thông tin có trong các đoạn [1], [2], ... được cung cấp.\n"
        "- Nếu thông tin không nằm trong các đoạn này, trả lời: "
        "\"Tôi chưa tìm thấy đủ thông tin trong kho kiến thức hiện tại để trả "
        "lời chắc chắn.\"\n"
        "- Sau mỗi luận điểm, trích dẫn nguồn bằng ký hiệu [n] tương ứng với "
        "đoạn bạn dùng. Không trích dẫn đoạn không có thông tin.\n"
        "- Câu trả lời ngắn gọn, tập trung, không bịa dữ liệu khách hàng, "
        "không tự quyết định nghiệp vụ cho một khách hàng.\n\n"
        f"=== KHO KIẾN THỨC ===\n{block}\n\n"
        f"CÂU HỎI: {question}"
    )


class DeterministicGroundedAnswerer:
    """Deterministic, no-LLM answerer.

    Builds the answer purely from the retrieved chunk content so evaluation of
    grounding/citations is well-defined WITHOUT an LLM. It is used by the
    LOCAL_MOCKED_VDB foundation proof and unit tests; it is NOT the production
    Qwen path.
    """

    def answer(self, question: str, chunks: list[KnowledgeChunk]) -> str:
        if not chunks:
            return "Tôi chưa tìm thấy đủ thông tin trong kho kiến thức hiện tại để trả lời chắc chắn."
        lines: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            excerpt = self._excerpt(chunk)
            citation = chunk.citation_label()
            lines.append(f"- Theo tài liệu {citation} (nguồn {index}): {excerpt}")
        return "\n".join(lines)

    @staticmethod
    def _excerpt(chunk: KnowledgeChunk) -> str:
        return chunk.content.replace("\n", " ").strip()[:400]


class MaasRagAnswerer:
    """Qwen Flash grounded answerer over the GreenNode MaaS chat endpoint.

    Uses the fast model (qwen/qwen3.6-flash) through a MaaS-compatible client.
    Requires a configured base URL, API key and model. Live use is gated behind
    LIVE_GREENNODE_RAG=PASS; foundation tests use the deterministic answerer.
    """

    def __init__(
        self,
        config: KnowledgeRagConfig,
        client=None,
        max_tokens: int = 512,
    ):
        self.config = config
        self._client = client
        self.max_tokens = max_tokens

    def _client_or_default(self):
        if self._client is not None:
            return self._client
        from .maas_client import build_chat_client

        return build_chat_client(self.config)

    def answer(self, question: str, chunks: list[KnowledgeChunk]) -> str:
        if not chunks:
            return "Tôi chưa tìm thấy đủ thông tin trong kho kiến thức hiện tại để trả lời chắc chắn."
        client = self._client_or_default()
        prompt = _build_prompt(question, chunks)
        content, model = client.complete(
            prompt, max_tokens=self.max_tokens, temperature=0
        )
        if not content:
            return "Tôi chưa tìm thấy đủ thông tin trong kho kiến thức hiện tại để trả lời chắc chắn."
        return content