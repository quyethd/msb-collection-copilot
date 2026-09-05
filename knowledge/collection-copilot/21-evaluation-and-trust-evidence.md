---
document_id: 21-evaluation-and-trust-evidence
title: Đánh giá hệ thống và bằng chứng tin cậy
section: evaluation
topic: TRUST
audience: TECH
content_type: technical
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
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

## Đánh giá RAG (TASK-011H)

Bộ golden questions cho RAG gồm khoảng 20-25 câu hỏi chia bốn nhóm; chỉ số đo:
Recall@3, MRR, GROUNDING_PASS_RATE, CITATION_PASS_RATE, BOUNDARY_PASS_RATE,
UNSUPPORTED_CLAIM_RATE. Xem tài liệu có liên quan về TASK-011H evaluation.

## Nguồn

- Bộ golden queries và kết quả eval nằm trong kho kiến thức và bộ đánh giá của
  dự án; chỉ số chính thức được công bố tại thời điểm foundation test.