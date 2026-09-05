from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


KNOWLEDGE_VERSION = "TASK-011H-V1"
SOURCE_COMMIT = "44d24e3c3d2c6277ef2a172e5d8548a1a0402277"

QWEN_FAST_MODEL = "qwen/qwen3.6-flash"
GLM_MODEL = "z-ai/glm-5.2-hackathon"
EMBEDDING_MODEL = None  # probe /embeddings on authorized MaaS returned 404 (model-not-found)
EMBEDDING_MODEL_STATUS = "NONE_AVAILABLE"

# TASK-011H-A: no MaaS embedding model exists on the authorized catalog, so the
# live embedding tier uses a local multilingual ONNX model (fastembed) until a
# GreenNode embedding endpoint is provisioned. Provider selection:
#   RAG_EMBEDDING_PROVIDER=deterministic|local-multilingual|local-e5|greennode-maas
LOCAL_MULTILINGUAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LOCAL_MULTILINGUAL_NAME = "local-multilingual-minilm-l12"
LOCAL_MULTILINGUAL_DIM = 384

# Calibrated on TASK-011H-A: all 3 out-of-scope questions max top-1 cosine 0.337;
# all 26 knowledge questions min top-1 0.415 (D6). Threshold 0.38 separates them.
SEMANTIC_MIN_SCORE = 0.38

CORPUS_REL_DIR = Path("knowledge/collection-copilot")

DEFAULT_TOP_K = 3
DEFAULT_MIN_SCORE = 0.15
LOCAL_EMBEDDING_DIM = 512
LOCAL_TOKEN_WEIGHT = 0.75

TOPICS = {
    "PRODUCT",
    "ROUTING",
    "RECOVERY_SCORE",
    "NBA",
    "PTP",
    "CASHFLOW",
    "SELF_CURE",
    "SIMULATION",
    "IMPACT",
    "DATA",
    "USER_GUIDE",
    "ARCHITECTURE",
    "GRENNODE",
    "TRUST",
    "EVALUATION",
    "ROADMAP",
}

AUDIENCES = {"COLLECTION_OFFICER", "MANAGER", "TECH", "JUDGE", "ALL"}

IMPLEMENTATION_STATUSES = {"IMPLEMENTED", "PROVEN", "FUTURE", "PROTOTYPE_ONLY"}

LOW_CONFIDENCE_REFUSAL = (
    "Tôi chưa tìm thấy đủ thông tin trong kho kiến thức hiện tại để trả lời "
    "chắc chắn."
)

BOUNDARY_RESPONSES = {
    "CUSTOMER_DECISION_REQUIRED": (
        "Câu hỏi này yêu cầu quyết định nghiệp vụ cho một khách hàng cụ thể. "
        "Quyết định thuộc về Decision Core deterministic và được truy vấn qua "
        "công cụ nghiệp vụ, không phải kho kiến thức RAG. Vui lòng dùng Trợ lý "
        "Thu hồi Nợ cho câu hỏi về quyết định của khách hàng."
    ),
    "CUSTOMER_FACT_REQUIRED": (
        "Câu hỏi này yêu cầu dữ kiện của một khách hàng cụ thể. Dữ kiện khách "
        "hàng được truy vấn qua công cụ nghiệp vụ (get_customer_360, "
        "get_cashflow_intelligence...), không phải kho kiến thức RAG."
    ),
    "SIMULATION_REQUIRED": (
        "Câu hỏi này cần mô phỏng kịch bản what-if cho một khách hàng cụ thể. "
        "Mô phỏng chạy lại cùng deterministic engine qua công cụ "
        "simulate_decision, không phải kho kiến thức RAG."
    ),
    "SECURITY_SENSITIVE": (
        "Tôi không thể hỗ trợ yêu cầu này vì nó liên quan đến thông tin nhạy "
        "cảm hoặc bí mật."
    ),
}


@dataclass
class KnowledgeRagConfig:
    corpus_dir: Path = field(default_factory=lambda: _default_corpus_dir())
    top_k: int = DEFAULT_TOP_K
    min_score: float = DEFAULT_MIN_SCORE
    knowledge_version: str = KNOWLEDGE_VERSION
    llm_base_url: str | None = field(default_factory=lambda: os.environ.get("LLM_BASE_URL"))
    llm_api_key: str | None = field(default_factory=lambda: os.environ.get("LLM_API_KEY"))
    qwen_fast_model: str | None = field(
        default_factory=lambda: os.environ.get("QWEN_FAST_MODEL", QWEN_FAST_MODEL)
    )
    local_embedding_dim: int = LOCAL_EMBEDDING_DIM
    embedding_provider: str = field(
        default_factory=lambda: os.environ.get("RAG_EMBEDDING_PROVIDER", "deterministic")
    )
    local_multilingual_model: str = LOCAL_MULTILINGUAL_MODEL
    semantic_min_score: float = field(
        default_factory=lambda: float(os.environ.get("RAG_SEMANTIC_MIN_SCORE", str(SEMANTIC_MIN_SCORE)))
    )
    grennode_vdb_endpoint: str | None = field(
        default_factory=lambda: os.environ.get("GRENNODE_VDB_ENDPOINT")
    )
    grennode_vdb_index: str | None = field(
        default_factory=lambda: os.environ.get("GRENNODE_VDB_INDEX", "msb-collection-knowledge")
    )
    grennode_vdb_user: str | None = field(
        default_factory=lambda: os.environ.get("GRENNODE_VDB_USER")
    )
    grennode_vdb_password: str | None = field(
        default_factory=lambda: os.environ.get("GRENNODE_VDB_PASSWORD")
    )

    def live_maas_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_api_key)

    def greennode_vdb_configured(self) -> bool:
        return bool(self.grennode_vdb_endpoint and self.grennode_vdb_index)


def _default_corpus_dir() -> Path:
    explicit = os.environ.get("KNOWLEDGE_CORPUS_DIR")
    if explicit:
        return Path(explicit)
    return _repo_root() / CORPUS_REL_DIR


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return here