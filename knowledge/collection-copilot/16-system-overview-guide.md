---
document_id: 16-system-overview-guide
title: Hướng dẫn trang giới thiệu sản phẩm (landing)
section: user_guide
topic: PRODUCT
audience: ALL
content_type: product_guide
knowledge_version: TASK-011H-V2
source_commit: 617a1ed84e6001155ae87b467bffbf962d3ce3cc
source_type: curated
prototype_status: PROTOTYPE
implementation_status: IMPLEMENTED
updated_at: 2026-09-06
---

# Hướng dẫn trang giới thiệu sản phẩm (landing)

## Vị trí và mục đích

Trang giới thiệu sản phẩm (landing) là trang web **công khai** đặt ở đường dẫn
gốc `/` của hệ thống, hiển thị **trước khi người dùng đăng nhập**. Người dùng
chưa đăng nhập vẫn đọc được toàn bộ nội dung landing: bài toán, giải pháp,
kiến trúc, độ tin cậy, lộ trình — phù hợp cho cán bộ, quản lý, kiến trúc và
ban giám khảo.

Thương hiệu trên landing: **MSB Trợ lý Thu hồi Nợ — Powered by GreenNode AI**,
bao gồm mục "Nền Tảng AI GreenNode". Nút CTA chính là **Đăng nhập hệ thống**
(đưa người dùng tới trang đăng nhập demo) cùng nút **Khám phá giải pháp**.

## Nội dung chính trên landing

1. **BÀI TOÁN** — bốn điểm khó khăn của cán bộ thu hồi.
2. **GIÁ TRỊ** — bốn nhóm người dùng và lợi ích.
3. **LUỒNG QUYẾT ĐỊNH** — WHO / WHY / WHAT / WHEN.
4. **VÍ DỤ TÁC NGHIỆP** — SYN002846: tuyến CALL, hành động Chờ khách hàng tự thanh toán.
5. **TÌNH HUỐNG THỬ** — what-if: thay đổi tín hiệu → đổi hành động.
6. **ĐƯỜNG ỐNG QUYẾT ĐỊNH** — dữ liệu → hard policy → routing → score → NBA →
   channel/timing → GreenNode Agent.
7. **VẬN HÀNH QUY TẮC** — sáu lớp quyết định.
8. **KIẾN TRÚC** — frontend, API, Decision Core, GreenNode Agent, dữ liệu/ngữ cảnh.
9. **CẤU TRÚC CODE** — các module chính.
10. **VAI TRÒ AI** — AI làm gì / AI không làm gì.
11. **KIỂM CHỨNG** — các bằng chứng trust/safety.
12. **TÁC NGHIỆP** — một ngày làm việc với Trợ lý.
13. **HỎI TRỢ LÝ** — câu hỏi mẫu.
14. **HỎI ĐÁP** — FAQ.
15. **LỘ TRÌNH** — đã có trong bản demo / hướng phát triển tiếp theo.

Landing là trang **public full-width**, không có sidebar tác nghiệp, không nằm
trong menu khu vực ứng dụng (khu vực sau đăng nhập).

## Thông điệp cốt lõi

- "Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo."
- "Bộ máy quyết định (Decision Core) theo quy tắc xác định là nguồn quyết định
  nghiệp vụ; GreenNode Agent là lớp tương tác, điều phối công cụ và giải thích."
- "Bản demo sử dụng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật."

## Luồng truy cập sản phẩm

Người dùng đọc landing ở `/`, nhấn **Đăng nhập hệ thống** để vào trang đăng
nhập demo `/login`, đăng nhập bằng tài khoản demo do team cung cấp, rồi vào
khu vực ứng dụng tại `/app`. Khu vực ứng dụng gồm các trang: Tổng quan, Danh
sách ưu tiên, Khách hàng, Tác động dự kiến và Trợ lý (sidebar).

## Hiện trạng kiểm chứng

Lớp kiến thức RAG đã được kiểm chứng chạy thật trên GreenNode vDB OpenSearch
(TASK-011H live proof): ingest và truy xuất live, Qwen Flash tổng hợp câu trả
lời có nguồn. Phiên bản kiến thức hiện tại là **TASK-011H-V2**, lưu trong index
`msb-collection-knowledge-v2` trên GreenNode vDB. Việc tích hợp RAG vào giao
diện Trợ lý production chưa thực hiện (COPILOT_INTEGRATION=NO).