---
document_id: 26-glossary
title: Bảng thuật ngữ
section: glossary
topic: PRODUCT
audience: ALL
content_type: reference
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Bảng thuật ngữ

## Thuật ngữ nghiệp vụ

- **CIF** — Customer Information File, mã khách hàng. Trong bản demo dạng
  SYN###### hoặc GOLDEN_G##
- **DPD** — Days Past Due, số ngày quá hạn (theo CIF = MAX DPD của các khoản).
- **Tổng dư nợ** — tổng dư nợ các khoản vay theo CIF.
- **CALL** — tuyến xử lý qua gọi điện cho các trường hợp cần tương tác thu hồi.
- **CBS** — tuyến nhắc thanh toán và theo dõi cam kết.
- **Treatment** — hành động xử lý cụ thể.
- **Channel** — kênh liên hệ thực hiện hành động.
- **Objective** — mục tiêu của hành động.
- **PTP** — Promise to Pay, cam kết thanh toán: OPEN / KEPT / PARTIAL / BROKEN
  / NONE.
- **PTP ability** — đánh giá của nhân viên về khả năng khách thực hiện cam kết.
- **RTP** — Request to Pay hạng nặng.
- **NIN** — No Intent to Pay.
- **Self-cure** — khách tự thanh toán mà không cần tương tác.
- **Next Best Action (NBA)** — cơ chế chọn hành động tiếp theo theo mức ưu tiên.
- **Hard suppression** — hạn chế xử lý ở mức cứng (không được liên hệ).
- **Next action (source)** — ngày hành động tiếp theo từ nguồn.

## Thuật ngữ kỹ thuật

- **Decision Core** — lõi quyết định deterministic (policy + score + NBA +
  simulation).
- **Recovery Opportunity** — điểm cơ hội thu hồi 0-100.
- **GreenNode Agent** — lớp tác nhân GreenNode (AgentBase + MaaS).
- **AgentBase** — runtime tác nhân của GreenNode.
- **MaaS** — Model-as-a-Service của GreenNode (GLM-5.2, Qwen Flash, Gemma).
- **Vector Database (vDB)** — dịch vụ database vector của GreenNode vDB
  (OpenSearch + kNN, PostgreSQL + pgvector).
- **RAG** — Retrieval-Augmented Generation: tìm kiếm ngữ cảnh từ kho kiến thức,
  tạo câu trả lời dựa trên nguồn.
- **Chunk** — đơn vị nội dung được lưu trong RAG, có ID ổn định.
- **Embedding** — vector hóa văn bản để tìm kiếm theo độ tương đồng.
- **Grounding** — câu trả lời bám đúng nguồn tài liệu được truy xuất.

## Quy ước dữ liệu

- **3.000 khách hàng mô phỏng**, seed 20260828, ngày tham chiếu 2026-08-28.
- **Knowledge version**: TASK-011H-V1.
- **Source commit**: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277.
- **Bộ golden questions RAG**: ~20-25 câu, bốn nhóm A/B/C/D.