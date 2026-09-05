---
document_id: 16-system-overview-guide
title: Hướng dẫn trang Giới thiệu hệ thống
section: user_guide
topic: ARCHITECTURE
audience: ALL
content_type: product_guide
knowledge_version: TASK-011H-V1
source_commit: 44d24e3c3d2c6277ef2a172e5d8548a1a0402277
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-05
---

# Hướng dẫn trang Giới thiệu hệ thống

## Mục đích

Trang Giới thiệu hệ thống (đường dẫn /gioi-thieu) là trang landing giải thích
toàn bộ dự án: bài toán, giải pháp, kiến trúc, độ tin cậy, lộ trình — phù hợp
cho cán bộ, quản lý, kiến trúc và ban giám khảo.

## Bố cục chính

1. **BÀI TOÁN** — bốn điểm khó khăn của cán bộ thu hồi.
2. **GIÁ TRỊ** — bốn nhóm người dùng và lợi ích.
3. **LUỒNG QUYẾT ĐỊNH** — WHO / WHY / WHAT / WHEN.
4. **VÍ DỤ TÁC NGHIỆP** — SYN002846: tuyến CALL, hành động Chờ tự thanh toán.
5. **TÌNH HUỐNG THỬ** — what-if: thay đổi tín hiệu → đổi hành động.
6. **ĐƯỜNG ỐNG QUYẾT ĐỊNH** — dữ liệu → hard policy → routing → score → NBA →
   channel/timing → Agent.
7. **VẬN HÀNH QUY TẮC** — sáu lớp quyết định.
8. **KIẾN TRÚC** — frontend, API, Decision Core, GreenNode Agent, dữ liệu.
9. **CẤU TRÚC CODE** — các module chính.
10. **VAI TRÒ AI** — AI làm gì / AI không làm gì.
11. **KIỂM CHỨNG** — các bằng chứng trust/safety.
12. **TÁC NGHIỆP** — một ngày làm việc với Trợ lý.
13. **HỎI TRỢ LÝ** — câu hỏi mẫu.
14. **HỎI ĐÁP** — FAQ.
15. **LỘ TRÌNH** — đã có trong bản demo / hướng phát triển tiếp theo.

## Thông điệp cốt lõi

- "Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo."
- "Decision Core deterministic là nguồn quyết định nghiệp vụ; GreenNode Agent
  là lớp tương tác, điều phối tool và giải thích."
- "Bản demo sử dụng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật."

## Bản demo hiện tại

Trang này đang mô tả hệ thống gồm AgentBase + MaaS GLM 5.2 + Decision Core.
Lớp kiến thức GreenNode Vector Database + Qwen Flash sẽ được trình bày trên
trang này **chỉ sau khi** được kiểm chứng chạy thật (TASK-011H live proof).