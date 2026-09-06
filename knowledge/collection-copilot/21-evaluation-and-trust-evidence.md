---
document_id: 21-evaluation-and-trust-evidence
title: Đánh giá hệ thống và bằng chứng tin cậy
section: evaluation
topic: TRUST
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Đánh giá hệ thống và bằng chứng tin cậy

## Đánh giá ban đầu (baseline eval)

Bộ đánh giá ban đầu gồm 40 câu hỏi cho Trợ lý Thu hồi Nợ, chia nhóm:

- **Quyết định (Decision)**: câu hỏi về hành động/tuyến/kênh/thời điểm của
  các khách hàng mẫu (chấm theo exact expected).
- **Tình huống (Situational)**: câu hỏi ngữ cảnh về khách hàng mẫu, mô phỏng
  what-if.
- **Chính sách (Policy)**: câu hỏi về chính sách sản phẩm, ranh giới, my-data /
  knowledge-talk.
- **Độ tin cậy (Trust & Safety)**: câu hỏi về decision fidelity, fabricate,
  unknown CIF, override, threat, reasoning leak, permissions, PII.-safe.
- **AI cuối dòng (End-to-end)**: câu hỏi sử dụng cả luồng tìm nạp ngữ cảnh.

## Kết quả chính (đã kiểm chứng)

- Độ chính xác quyết định (decision fidelity): gần như tuyệt đối với các câu
  hỏi được thiết kế.
- Không xảy ra bịa dữ liệu khách hàng chưa biết.
- Không cho phép override quyết định.
- Không lộ reasoning nội bộ.
- Tool-use đúng intent, response dựa trên output structured từ tool.

## Đánh giá mở rộng (TASK-011E)

- Mở rộng bộ 40 câu hỏi thành bộ 50+ câu cho evaluation suite.
- Bao phủ thêm trường hợp biên, câu hỏi có rủi ro, câu hỏi ngôn ngữ tự nhiên
  biến thể.
- Randomized order, deterministic seed để tái lặp; score công khai khi có kết
  quả chính thức.

## Nguyên tắc công khai số liệu

Chỉ công bố số liệu khi:

- có cách tái lặp rõ ràng (seed, dataset, phiên bản);
- nêu rõ nguồn dữ liệu (dữ liệu mô phỏng, không phải dữ liệu thật);
- phân biệt kết quả demo / foundation test với kết quả production.

## Đánh giá RAG (TASK-011H / TASK-011H-A)

Bộ golden questions cho RAG gồm các câu hỏi chia nhóm A/B/C/D; chỉ số đo:
Recall@3, MRR, GROUNDING_PASS_RATE, CITATION_PASS_RATE, BOUNDARY_PASS_RATE,
UNSUPPORTED_CLAIM_RATE, REFUSAL_PASS_RATE. Ngưỡng admission semantic:
SEMANTIC_MIN_SCORE = 0.38 (hiệu chỉnh trên phiên bản kiến thức hiện tại).

## Kết quả live (TASK-011H live proof)

- **Live GreenNode vDB OpenSearch**: ingest và truy xuất live PASS.
- **Live Qwen Flash RAG**: câu trả lời có nguồn (citation) PASS.
- Chỉ số live proof: R@3 = 1.0, MRR = 0.8974, GROUNDING/CITATION/BOUNDARY =
  1.0, UNSUPPORTED_CLAIM_RATE = 0.0, REFUSAL_PASS_RATE = 1.0, D6 = PASS.
- Bộ security audit: SECRET_AUDIT = PASS, SECRET_QUERY_SAFE = PASS,
  PRIVATE_REASONING_AUDIT = PASS.
- INFERENCE_ANCHOR = LIVE_GREENNODE_VDB; RAG_LIVE_PROOF = PASS;
  COPILOT_INTEGRATION = NO; DEPLOY = NO.

## Kiểm chứng kho kiến thức V2 (TASK-011H-A.1)

- Kho kiến thức được cập nhật lên **TASK-011H-V2** dựa trên current main
  (commit 617a1ed84e6001155ae87b467bffbf962d3ce3cc) và ingest vào index
  `msb-collection-knowledge-v2` trên GreenNode vDB.
- Index phiên bản V1 được giữ nguyên (V1_PRESERVED) để có thể rollback.
- Kiểm tra rò rỉ kiến thức cũ (V1_ACTIVE_RETRIEVAL_LEAK, STALE_PRODUCT_FACTS_ACTIVE,
  STALE_NAVIGATION_ANSWER) đều PASS: không có chunk phiên bản V1 xuất hiện trong
  index V2, không có tuyên bố điều hướng/sp cũ còn hiệu lực.
- BUSINESS_SEMANTICS_DRIFT = 0: các quyết định nghiệp vụ (routing, score, NBA,
  PTP, dòng tiền, self-cure, mô phỏng, tác động) không đổi.

## Nguồn

- Bộ golden queries và kết quả eval nằm trong kho kiến thức và bộ đánh giá của
  dự án; chỉ số chính thức được công bố tại thời điểm foundation test.