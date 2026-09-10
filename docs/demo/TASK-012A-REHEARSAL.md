# Kế hoạch Rehearsal

## Vòng 1 — Đúng kịch bản

- **Mục tiêu:** Không sai facts, ranh giới AI và wording tác động.
- **Thời lượng:** 4 phút 40 giây mục tiêu; 5 phút 00 giây tối đa.
- **Đạt:** Đủ hero, decision, simulation, RAG, close; không nói dữ liệu thật.
- **Lỗi thường gặp:** Gọi score là xác suất; gọi 32 là cuộc gọi giảm; nói RAG quyết định.
- **Sửa:** Đọc lại cheat sheet và thay bằng “ước tính theo giả định demo”.

## Vòng 2 — Đúng thời gian

- **Mục tiêu:** Demo chính ≤4m40s; opening ≤30s; hero ≤45s; simulation ≤35s; RAG ≤30s nói; closing ≤20s.
- **Đạt:** Không vượt mốc; có thể bỏ Impact nếu thiếu thời gian.
- **Lỗi:** Nói quá sâu về implementation.
- **Sửa:** Business value trước, công nghệ sau.

## Vòng 3 — Không đọc kịch bản

- **Mục tiêu:** Nói tự nhiên theo ba mốc: vấn đề, bằng chứng, giá trị.
- **Thời lượng:** 4 phút 40 giây mục tiêu.
- **Đạt:** Không nhìn màn hình chữ quá lâu; vẫn nói đúng SYN002846.
- **Lỗi:** Quên câu “CALL không có nghĩa phải gọi ngay”.
- **Sửa:** Dùng 7 mốc: 11 ngày, 48M, 168M, NONE, CALL, chờ tự thanh toán, điểm 47.

## Vòng 4 — Bị ngắt bởi giám khảo

- **Mục tiêu:** Trả lời câu hỏi rồi quay lại timeline.
- **Đạt:** Trả lời trong 15–25 giây, không mất ranh giới Decision Core.
- **Lỗi:** Tranh luận model hoặc hứa ROI.
- **Sửa:** Dùng Judge QA; kết thúc bằng “Tôi quay lại bằng chứng trên màn hình”.

## Vòng 5 — Mô phỏng lỗi

- **Mục tiêu:** Thực hành website, login, backend, RAG, VDB, simulation lỗi.
- **Đạt:** Nói thật, không bịa live result, chuyển fallback trong 10 giây.
- **Lỗi:** Chờ im lặng hoặc nói “AI đang suy nghĩ”.
- **Sửa:** Nói “Hệ thống đang tìm tài liệu liên quan trong kho kiến thức GreenNode và tổng hợp câu trả lời có nguồn.”

## Vòng 6 — Chung kết

- **Mục tiêu:** Một lần chạy như thi thật.
- **Đạt:** ≤4m40s mục tiêu, không secret, không terminal, facts đúng, closing rõ.
- **Lỗi:** Mở quá nhiều tab hoặc thay đổi dữ liệu ngoài supported reset.
- **Sửa:** Dùng đúng tab list và checklist T-30/T-10/T-2.

## Bảng mốc thời gian

| Phần | Mục tiêu |
|---|---:|
| Opening | ≤30s |
| Hero explanation | ≤45s |
| Simulation | ≤35s |
| RAG speaking | ≤45s, model wait xử lý bằng lời thoại |
| Closing | ≤25s |
| Tổng demo | ≤4m40s mục tiêu; ≤5m00s tối đa |

## Checklist trước giờ trình bày

### T-30 phút

- Backend health và frontend public đều tải.
- GreenNode VDB V2, Qwen Flash, login, SYN002846, simulation reset, RAG query và Impact đã được kiểm tra.

### T-10 phút

- Mở sẵn các tab: `/`, `/login` hoặc `/app`, `/app/priority`, `/app/customer`, `/app/impact`.
- Kiểm tra zoom, độ phân giải và thông báo hệ điều hành.
- Ẩn password; đóng terminal, log và cửa sổ chứa secret.
- Giữ một bộ screenshot dự phòng offline.

### T-2 phút

- Landing/hero đã tải.
- Assistant đang đóng.
- Scenario đã reset về SYN002846 và 48M/168M.
- Timer sẵn sàng; presenter mở cheat sheet và không mở thêm tab.
