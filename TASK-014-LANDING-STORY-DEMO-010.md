# TASK-014-LANDING-STORY-DEMO-010

## 1. Mục tiêu

Thiết kế lại landing page của **MSB Trợ lý Thu hồi Nợ** thành một câu chuyện sản phẩm hoàn chỉnh, phục vụ đồng thời:

1. Trình bày trực tiếp khi pitch tại MSB AI Hackathon 2026.
2. Cho Ban giám khảo xem lại sau pitch mà không cần mở file PowerPoint.
3. Cho người chưa nghe thuyết trình vẫn hiểu được bài toán, giải pháp, demo, Web + Zalo, cách hệ thống ra quyết định, vai trò GreenNode, tác động dự kiến và lộ trình.

Landing không được mang cảm giác “website SaaS generic”. Mục tiêu thị giác:

> **Một pitch deck tương tác trên web, gắn với một sản phẩm đang chạy thật.**

---

## 2. Baseline đã khóa

Các business canary phải giữ nguyên:

- `SYN002846`: Route `CALL`, Treatment `WAIT_SELF_CURE`, Channel `NONE`, Recovery Opportunity Score `47`.
- `SYN000746`: Score `69`.
- Business semantics drift: `0`.

Các claim công khai phải giữ đúng:

- Thuộc tuyến CALL **không có nghĩa hôm nay nhất thiết phải gọi**.
- Recovery Opportunity là **điểm ưu tiên tương đối**, không phải xác suất thanh toán.
- AI không tự quyết định nghiệp vụ.
- Decision Core giữ quyền xác định tuyến, điểm, hành động và kênh xử lý.
- GreenNode hỗ trợ hiểu câu hỏi, diễn giải, tra cứu kiến thức và năng lực điều phối AI đã được kiểm chứng.
- Demo dùng dữ liệu mô phỏng, không dùng dữ liệu khách hàng thật.
- Tác động tài chính chỉ là ước tính theo giả định của bản demo.

---

## 3. Nguyên tắc nội dung công khai

### 3.1. Ngôn ngữ

Ưu tiên tiếng Việt. Nếu bắt buộc dùng tiếng Anh hoặc tên công nghệ, lần đầu xuất hiện phải có giải thích tiếng Việt bên cạnh hoặc ngay dưới.

Ví dụ:

- `Decision Core — Bộ máy quyết định nghiệp vụ`
- `Recovery Opportunity — Điểm cơ hội thu hồi`
- `RAG — tra cứu tăng cường bằng dữ liệu`
- `Vector Database — kho dữ liệu véc-tơ phục vụ tìm kiếm theo ý nghĩa`
- `What-if Simulation — mô phỏng tình huống giả định`
- `Landing — trang giới thiệu`
- `Web — màn hình hệ thống`

### 3.2. Không xuất hiện trên UI công khai

Không để lộ: TASK-013, TASK-014, Codex, commit, merge, deploy, audit, regression, runtime, sidecar, internal port, service name, source filename, enum nội bộ, context leak, test label, tên module nội bộ như `msb_policy`, `msb_recovery`, `msb_nba`.

---

## 4. Định hướng thị giác

Phong cách đồng bộ với bộ slide MSB AI Hackathon đã duyệt:

- Navy MSB: màu cấu trúc/chữ chính.
- Cam MSB: hành động, điểm nhấn nghiệp vụ.
- Xanh lá: dữ liệu, tri thức, GreenNode.
- Nền trắng / xanh rất nhạt.
- Nhiều khoảng trắng.
- Card bo góc lớn, shadow nhẹ.
- Typography lớn, ít chữ.
- Infographic lớn thay vì card text dày.
- Mascot AI dùng có chọn lọc.
- Có thể dùng một số callout handwritten giống slide.
- Footer/CTA cuối có thể dùng mảng navy cong giống slide.

Không được biến toàn bộ trang thành các card giống nhau, dùng stock image, nhồi text kỹ thuật, hoặc làm mọi section có trọng lượng thị giác ngang nhau.

---

## 5. Asset hình ảnh

Thư mục:

`frontend/public/landing-story/`

### 5.1. Ảnh nên ưu tiên dùng

Các ảnh dùng làm điểm neo thị giác:

1. Ảnh bài toán hiện tại.
2. Ảnh tình huống demo SYN002846.
3. Ảnh minh bạch điểm 47/100.
4. Ảnh kiến trúc Web + Zalo + Decision Core + GreenNode.
5. Ảnh hành trình người dùng mới đã khóa.
6. Ảnh hai luồng trợ lý mới đã khóa.
7. Ảnh kết luận/chốt vấn đề nếu phù hợp.

Không cần đưa cả 17 ảnh lên landing.

### 5.2. Hai ảnh mới bắt buộc

#### A. `zalo-demo-live-context.png`

Tên hiển thị: **Demo Zalo thực tế**

Mục tiêu:
- chứng minh kênh Zalo,
- giữ đúng ngữ cảnh hồ sơ,
- giữ đúng ngữ cảnh mô phỏng,
- follow-up “thế giờ làm gì” phải bám after-state.

Nội dung bắt buộc:

1. `Tính điểm SYN002846` → trả lời score 47/100.
2. `Nếu nó không có tiền vào tuần này thì sao` → mô phỏng tiền vào 7 ngày = 0; hành động chuyển từ Chờ khách hàng tự thanh toán/Chưa cần liên hệ sang Liên hệ khách hàng/Gọi điện.
3. `Thế giờ làm gì` → trả lời theo trạng thái mô phỏng vừa tạo, không quay lại baseline.

Caption:

> Trợ lý Zalo giúp cán bộ hỏi tự nhiên, giữ đúng ngữ cảnh hồ sơ và mô phỏng, nhưng quyết định nghiệp vụ vẫn bám theo Bộ máy quyết định của hệ thống.

Không được thể hiện Zalo tự quyết định nghiệp vụ.

#### B. `greennode-in-product.png`

Tên hiển thị: **GreenNode trong sản phẩm**

Mục tiêu:
- giải thích GreenNode tạo giá trị ở đâu,
- phân biệt rõ GreenNode và Decision Core,
- local embedding nằm ngoài GreenNode.

Thành phần bắt buộc:

**Decision Core — Bộ máy quyết định nghiệp vụ**
- phân tuyến,
- điểm ưu tiên,
- hành động,
- kênh,
- chính sách nghiệp vụ.

**AgentBase**
- năng lực điều phối công cụ đã được kiểm chứng,
- không mô tả là nơi ra quyết định.

**GreenNode MaaS + GLM 5.2**
- hiểu câu hỏi tự nhiên,
- diễn giải kết quả,
- hỗ trợ giải thích/mô phỏng.

**Vector Database + Qwen Flash**
- tra cứu kiến thức có nguồn,
- tổng hợp câu trả lời từ tài liệu,
- không quyết định nghiệp vụ.

**Local multilingual embedding**
- nhúng đa ngôn ngữ chạy cục bộ,
- nằm ngoài GreenNode.

Câu chốt bắt buộc:

> **GreenNode mở rộng khả năng trợ lý; Decision Core vẫn giữ quyền quyết định nghiệp vụ.**

Không claim mọi request production đều qua AgentBase, local embedding do GreenNode host, Qwen/GLM quyết định CALL/CBS, hoặc Zalo transport chạy qua OpenClaw/AgentBase.

---

## 6. Cấu trúc landing

Landing được tổ chức thành các “chương” kể chuyện. Không bắt buộc mỗi chương là một section lớn ngang nhau.

### 01. Hero

Nhãn: `MSB AI Hackathon 2026 · AI for My Team — AI cho đội ngũ`

Headline:

> **Không tìm khách hàng nợ nhiều nhất.  
> Tìm cơ hội thu hồi tốt nhất tiếp theo.**

Mô tả:

> MSB Trợ lý Thu hồi Nợ giúp cán bộ ưu tiên đúng hồ sơ, hiểu vì sao hệ thống đề xuất hành động, mô phỏng thay đổi và hỏi nhanh trên Web hoặc Zalo.

Ba điểm nhấn: Đúng khách hàng · Đúng hành động · Đúng thời điểm.

CTA chính: `Trải nghiệm bản demo`  
CTA phụ: `Xem hành trình demo`

Notice:

> Bản demo dùng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật.

Hero nên dựng HTML responsive theo phong cách slide, không chèn nguyên cover slide nếu khiến chữ khó đọc trên mobile.

### 02. Bài toán

Nhãn: `BÀI TOÁN`

Headline:

> **Cán bộ không thiếu dữ liệu. Điểm khó là biến dữ liệu thành hành động hôm nay.**

Ba ý:
1. Dư nợ lớn chưa chắc nên gọi trước.
2. Ngày quá hạn chưa phản ánh hết khả năng tự thanh toán.
3. Cán bộ phải kết hợp dòng tiền, cam kết thanh toán, lịch sử liên hệ và thời điểm.

Câu chốt:

> **Bài toán không chỉ là ai nợ nhiều, mà là hôm nay nên ưu tiên ai, làm gì và vì sao.**

### 03. Giải pháp

Nhãn: `GIẢI PHÁP`

Headline:

> **Một Trợ lý giúp biến dữ liệu thành quyết định có căn cứ**

4 khả năng: Ưu tiên hồ sơ · Giải thích quyết định · Mô phỏng tình huống · Tra cứu kiến thức có nguồn.

### 04. Web + Zalo

Nhãn: `WEB + ZALO`

Headline:

> **Xem sâu trên Web. Hỏi nhanh qua Zalo.**

Web: danh sách ưu tiên, hồ sơ, bằng chứng, điểm, mô phỏng, Trợ lý.

Zalo ví dụ:
- `Tính điểm SYN002846`
- `Nếu nó không có tiền vào tuần này thì sao?`
- `Thế giờ làm gì`
- `Hôm nay nên ưu tiên ai?`

Câu chốt:

> **Hai kênh khác nhau, cùng một bộ máy quyết định.**

### 05. Hành trình người dùng

Nhãn: `HÀNH TRÌNH NGƯỜI DÙNG`

Headline:

> **Từ trang giới thiệu → bằng chứng → hành động**

Bắt buộc giữ bước đầu: `Trang giới thiệu (Landing — trang giới thiệu)`.

Flow:
1. Trang giới thiệu
2. Đăng nhập
3. Danh sách ưu tiên
4. Hồ sơ khách hàng
5. Hỏi Trợ lý trên Web/Zalo
6. Hành động / Mô phỏng / Tác động dự kiến

Dùng infographic hành trình đã duyệt. Không dựng lại 6 card HTML trùng nội dung.

### 06. Chương Demo

Nhãn: `TRÌNH DIỄN SẢN PHẨM`

Headline:

> **Theo một hồ sơ từ dữ liệu đến hành động**

Không chèn 14 ảnh khổng lồ nối tiếp. Thiết kế 5–6 cảnh nổi bật hiển thị trước, nút `Xem toàn bộ hành trình demo`, gallery/lightbox/modal nhẹ, previous/next, caption ngắn, mobile dùng được.

Khoảng 14 cảnh:

**Nhóm A — Hiểu bài toán**
1. Bài toán ưu tiên
2. Các tín hiệu dữ liệu
3. Từ dữ liệu đến hành động

**Nhóm B — Demo Web**
4. Danh sách ưu tiên
5. Hồ sơ SYN002846
6. Điểm cơ hội thu hồi
7. Bằng chứng dòng tiền/PTP/liên hệ
8. Hỏi “Tại sao hôm nay chưa nên gọi?”
9. Mô phỏng tiền vào = 0
10. Hành động thay đổi

**Nhóm C — Demo Zalo**
11. Tính điểm qua Zalo
12. Hỏi mô phỏng qua Zalo
13. `Thế giờ làm gì`

**Nhóm D — Kết quả**
14. Tác động / thông điệp cuối

Ảnh minh họa phải ghi rõ nếu không phải screenshot production thật.

### 07. Case SYN002846

Nhãn: `TÌNH HUỐNG DEMO`

Headline:

> **Thuộc tuyến gọi không có nghĩa hôm nay nhất thiết phải gọi**

Thông tin:
- Quá hạn: 11 ngày
- Tiền vào 7 ngày: 48 triệu đồng
- Dòng tiền ròng 30 ngày: 168 triệu đồng
- Cam kết thanh toán: Chưa có
- Tuyến: CALL — tuyến gọi
- Điểm cơ hội thu hồi: 47/100
- Hành động: Chờ khách hàng tự thanh toán
- Kênh: Chưa cần liên hệ

Không đưa `WAIT_SELF_CURE` / `NONE` lên UI chính.

### 08. Minh bạch điểm 47/100

Nhãn: `MINH BẠCH`

Headline:

> **Không chỉ trả lời “làm gì”, hệ thống còn cho biết “vì sao”**

Breakdown:
- Mức khẩn cấp nghiệp vụ: 8/20
- Khả năng thanh toán: 20/25
- Mức sẵn sàng thanh toán: 4/20
- Khả năng liên hệ: 11/15
- Cơ hội theo thời điểm: 4/15
- Điều chỉnh chiến lược: 0/5

Tổng: `47/100`

Chú thích bắt buộc:

> Điểm cơ hội thu hồi là điểm ưu tiên tương đối, không phải xác suất khách hàng sẽ thanh toán.

Nếu dùng PTP: `PTP — cam kết thanh toán`.

### 09. Mô phỏng tình huống

Nhãn: `MÔ PHỎNG TÌNH HUỐNG`

Headline:

> **Cùng một chính sách, bối cảnh thay đổi thì hành động có thể thay đổi**

Before:
- Tiền vào 7 ngày: 48 triệu đồng
- Chờ khách hàng tự thanh toán
- Chưa cần liên hệ

Giả định:
- Tiền vào 7 ngày: 0
- Dòng tiền ròng 30 ngày: 0

After:
- Liên hệ khách hàng
- Gọi điện

Chú thích:

> Mô phỏng không thay đổi dữ liệu thật.

### 10. Demo Zalo thực tế

Dùng: `zalo-demo-live-context.png`

Nhãn: `TRỢ LÝ QUA ZALO`

Headline:

> **Hỏi như đang nói chuyện, nhưng kết quả vẫn theo cùng logic nghiệp vụ**

Proof points:
- Hiểu câu hỏi tự nhiên
- Giữ đúng hồ sơ đang hỏi
- Giữ đúng ngữ cảnh mô phỏng
- Gợi ý bước tiếp theo

Không claim live roundtrip nếu evidence chưa được xác nhận.

### 11. Hai luồng Trợ lý

Nhãn: `HAI LUỒNG TRỢ LÝ`

Headline:

> **Đúng luồng cho đúng câu hỏi**

Dùng infographic đã duyệt.

Dưới ảnh chỉ có 2 câu:

> **Câu hỏi nghiệp vụ:** Bộ máy quyết định giữ quyền xác định kết quả.

> **Câu hỏi kiến thức:** RAG — tra cứu tăng cường bằng dữ liệu — cung cấp kiến thức có nguồn.

### 12. Kiến trúc hệ thống

Nhãn: `CÁCH HỆ THỐNG HOẠT ĐỘNG`

Headline:

> **Web và Zalo dùng chung một bộ máy quyết định**

Dùng infographic kiến trúc đã duyệt.

Chú thích ngắn:
- Web / Zalo: kênh tương tác.
- Decision Core: Bộ máy quyết định nghiệp vụ.
- GreenNode AI: hiểu, tra cứu, diễn giải.
- Local embedding: nhúng ngôn ngữ đa ngôn ngữ chạy cục bộ.

Không đưa port, service name, worker internals, OpenClaw, task/commit names.

### 13. GreenNode trong sản phẩm

Dùng: `greennode-in-product.png`

Nhãn: `GREENNODE TRONG SẢN PHẨM`

Headline:

> **GreenNode giúp Trợ lý hiểu, tra cứu và giải thích**

Thông điệp:

> GreenNode cung cấp các năng lực AI để cán bộ tương tác tự nhiên với hệ thống, trong khi quyết định nghiệp vụ vẫn được Bộ máy quyết định kiểm soát.

Ba nhóm:
1. GreenNode MaaS + GLM 5.2 — hiểu câu hỏi, diễn giải kết quả.
2. Vector Database + Qwen Flash — tra cứu kiến thức có nguồn.
3. AgentBase — năng lực điều phối công cụ đã được kiểm chứng.

Local embedding phải nằm ngoài GreenNode.

Câu chốt:

> **Bộ máy quyết định giúp hệ thống quyết định đúng. GreenNode giúp cán bộ hiểu và khai thác quyết định đó bằng AI.**

### 14. AI có kiểm soát

Nhãn: `AI CÓ KIỂM SOÁT`

Headline:

> **AI hỗ trợ cán bộ, không thay thế quyền quyết định nghiệp vụ**

AI hỗ trợ: hiểu câu hỏi, giải thích, tóm tắt, tra cứu, giao tiếp Web/Zalo.

Bộ máy quyết định: phân tuyến, tính điểm, xác định hành động, xác định kênh, mô phỏng theo cùng chính sách.

Câu chốt:

> AI hỗ trợ hiểu, giải thích và tra cứu; Bộ máy quyết định giữ quyền xác định kết quả nghiệp vụ.

### 15. Tác động dự kiến

Nhãn: `TÁC ĐỘNG DỰ KIẾN`

Headline:

> **Ưu tiên tốt hơn có thể giảm thao tác không cần thiết**

Các số đã khóa:
- 3.000 hồ sơ demo
- 1.740 thuộc tuyến gọi
- 32 thuộc tuyến gọi nhưng hiện chưa cần gọi ngay
- ~1.065 giờ/năm
- ~106,5 triệu đồng/năm

Bắt buộc:

> **Ước tính theo giả định của bản demo, không phải ROI đã đạt.**

> **32 hồ sơ không đồng nghĩa đã giảm được 32 cuộc gọi.**

### 16. Tóm tắt cho Ban giám khảo

Nhãn: `TÓM TẮT CHO BAN GIÁM KHẢO`

Headline:

> **Nếu chỉ có một phút để xem lại sản phẩm**

- Bài toán: khó xác định hồ sơ nào nên ưu tiên hôm nay.
- Giải pháp: Trợ lý Thu hồi Nợ trên Web và Zalo.
- Khác biệt: ưu tiên theo cơ hội thu hồi, không chỉ dư nợ/DPD.
- AI: hỗ trợ hiểu, giải thích, tra cứu.
- Kiểm soát: Decision Core giữ quyền nghiệp vụ.
- Demo: dữ liệu mô phỏng, không dùng dữ liệu khách hàng thật.

Section này phải rất dễ tìm.

### 17. FAQ

Khoảng 6 câu:
1. Quy tắc đã quyết định rồi, AI để làm gì?
2. Đây có phải chatbot gắn quy tắc không?
3. Tại sao không để mô hình ngôn ngữ tự quyết định?
4. GreenNode được dùng thật ở đâu?
5. Điểm 47 có phải xác suất thanh toán 47% không?
6. 32 hồ sơ có nghĩa là giảm 32 cuộc gọi không?

Trả lời business trước, kỹ thuật sau.

### 18. Lộ trình

Nhãn: `LỘ TRÌNH`

Hiện tại:
- Web
- Zalo
- Decision Core
- Mô phỏng
- Knowledge RAG
- Synthetic demo

Tiếp theo:
- T24
- DigiLenO
- Contact Center
- đo lường hiệu quả
- mở rộng kênh
- AI hỗ trợ gọi điện trong tương lai

Mọi nội dung tương lai phải ghi rõ là tương lai. Không claim autonomous calling.

### 19. CTA cuối

Nền navy.

Headline:

> **Từ dữ liệu hôm nay đến hành động hiệu quả hơn**

Mô tả:

> MSB Trợ lý Thu hồi Nợ giúp cán bộ ưu tiên đúng hồ sơ, hiểu rõ lý do và hành động có căn cứ.

CTA: `Bắt đầu trải nghiệm`

Footer:
- MSB AI Hackathon 2026
- Debt Radar
- Powered by GreenNode AI — vận hành cùng nền tảng AI GreenNode

---

## 7. Điều hướng landing

Navigation gợi ý:
- Bài toán
- Giải pháp
- Demo
- Web + Zalo
- Cách hoạt động
- Tác động
- Câu hỏi thường gặp
- Trải nghiệm

Không đưa RAG, AgentBase, MaaS, Architecture ra menu chính.

---

## 8. Trải nghiệm cho Ban giám khảo

Gần đầu trang nên có 2 lựa chọn:

> **Muốn xem nhanh?** Xem hành trình demo trong khoảng 3 phút.

> **Muốn xem kỹ?** Khám phá cách hệ thống hoạt động, vai trò GreenNode và bằng chứng.

Dùng anchor, không tạo app mới.

---

## 9. Responsive

Test tối thiểu:
- 1366×768
- 1440×900
- 1920×1080
- 390×844

Bắt buộc:
- không overflow ngang,
- không cắt infographic,
- text mobile đọc được,
- ảnh lớn cho phép mở phóng to nếu cần,
- demo gallery usable,
- CTA rõ,
- không shrink infographic đến mức chữ không đọc được.

---

## 10. Accessibility

- Heading semantic.
- Alt text có nghĩa.
- Button có label.
- Focus state rõ.
- Gallery keyboard usable nếu hợp lý.
- Không để thông tin quan trọng chỉ nằm trong ảnh.
- Mỗi infographic cần có một đoạn summary text bên cạnh hoặc dưới ảnh.

---

## 11. Performance

- Lazy-load ảnh dưới fold.
- Không dùng ảnh quá nặng.
- Không thêm thư viện gallery nặng nếu không cần.
- Ưu tiên stack frontend hiện tại.

---

## 12. Test và acceptance criteria

### Frontend
- Landing render đủ section bắt buộc.
- Web + Zalo copy tồn tại.
- GreenNode section tồn tại.
- Judge summary tồn tại.
- Demo gallery hoạt động.
- FAQ hoạt động.
- Roadmap hiển thị đúng.
- Synthetic data disclaimer tồn tại.
- Impact disclaimer tồn tại.
- Recovery score disclaimer tồn tại.
- Hai ảnh mới load đúng.
- Không có internal labels.

### Business truth
- SYN002846 score = 47.
- Breakdown = 8 / 20 / 4 / 11 / 4 / 0.
- SYN000746 score = 69.
- Recovery Opportunity không bị mô tả như probability.
- CALL không bị mô tả như bắt buộc phải gọi ngay.

### GreenNode truth
- GLM 5.2 role đúng.
- Qwen Flash role đúng.
- Vector Database role đúng.
- Local embedding được mô tả là local.
- AgentBase wording bounded.
- Decision Core authority explicit.
- Không claim mọi production request chạy qua AgentBase.

### Zalo truth
- Zalo là một kênh của cùng Trợ lý.
- Không claim autonomous customer bot.
- Không claim autonomous calling.
- Không claim live roundtrip nếu chưa có evidence.

### Production smoke
Sau deploy:
- `/`
- `/login`
- `/app`
- `/app/priority`
- `/app/customer`
- `/app/impact`
- `/app/zalo`

phải tiếp tục hoạt động.

---

## 13. Scope code

TASK-014 chỉ được phép thay đổi:
- landing frontend,
- landing styles,
- landing tests,
- landing assets,
- task report.

Không thay đổi:
- backend business rules,
- Decision Core,
- Zalo worker,
- Zalo conversation engine,
- tool server auth,
- RAG authority,
- GreenNode runtime/config,
- synthetic business data.

---

## 14. Git / deploy workflow

Workflow:

`master sạch` → inspect assets → implement landing → frontend tests → production build → desktop/mobile visual QA → independent Very Audit → commit → build từ committed HEAD → backup docroot → deploy frontend only → public TLS QA → production visual QA → app smoke → truth audit → final report → close task

Production docroot:

`/www/wwwroot/msb-collection-copilot.duckdns.org`

Public QA nếu DNS bị intercept:

```bash
curl --resolve \
'msb-collection-copilot.duckdns.org:443:103.233.48.100' \
https://msb-collection-copilot.duckdns.org/
```

Không dùng `-k`, `--insecure`, `verify=False`, `/etc/hosts`.

---

## 15. File report

Kết quả TASK-014 phải ghi vào:

`task-results/TASK-014-LANDING-STORY-DEMO-010-FINAL.md`

Các gate cuối tối thiểu:

```text
TASK_ID=TASK-014-LANDING-STORY-DEMO-010

LANDING_STORY=PASS
DEMO_CHAPTER=PASS
WEB_ZALO_SECTION=PASS
USER_JOURNEY_VISUAL=PASS
SYSTEM_ARCHITECTURE_VISUAL=PASS
TWO_ASSISTANT_FLOWS_VISUAL=PASS
ZALO_DEMO_VISUAL=PASS
GREENNODE_SECTION=PASS
AI_CONTROL_SECTION=PASS
JUDGE_SUMMARY=PASS
FAQ=PASS
ROADMAP=PASS

FRONTEND_TESTS=PASS
BUILD=PASS

PUBLIC_LANGUAGE_POLICY=PASS
PUBLIC_INTERNAL_LABEL_SCAN=PASS

RECOVERY_SCORE_TRUTH=PASS
GREENNODE_PRODUCTION_TRUTH=PASS
ZALO_PUBLIC_TRUTH=PASS
BUSINESS_SEMANTICS_DRIFT=0

LOCAL_DESKTOP_VISUAL_QA=PASS
LOCAL_MOBILE_VISUAL_QA=PASS
VISUAL_STORY_CONTINUITY=PASS

VERY_AUDIT=PASS

FRONTEND_DEPLOY=PASS
DEPLOYED_BUILD_MATCH=PASS
BACKEND_RESTARTED=NO
ZALO_WORKER_RESTARTED=NO

PUBLIC_TLS=PASS
PUBLIC_LANDING_HTTP=PASS

PRODUCTION_DESKTOP_QA=PASS
PRODUCTION_MOBILE_QA=PASS
PRODUCTION_NO_OVERFLOW=PASS
PRODUCTION_NO_BROKEN_ASSETS=PASS
PRODUCTION_STORY_CONTINUITY=PASS

PRODUCTION_DEMO_GALLERY=PASS

APPLICATION_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS

RECOVERY_SCORE_PRODUCTION_TRUTH=PASS
GREENNODE_PRODUCTION_TRUTH=PASS
ZALO_PRODUCTION_COPY_TRUTH=PASS
IMPACT_PRODUCTION_TRUTH=PASS
ROADMAP_FUTURE_BOUNDARY=PASS

TASK_014_CLOSED=YES/NO
PUSH=NO
```

---

## 16. Stop condition

Nếu thiếu hai ảnh bắt buộc:

- `zalo-demo-live-context.png`
- `greennode-in-product.png`

thì không được tự tạo layout khác để thay thế mà không báo.

Nếu ảnh chưa có:
- report `ASSET_INPUT_MISSING=YES`,
- dừng trước khi code final layout liên quan đến hai section đó.

Nếu tất cả asset có đủ và task pass:
- đóng TASK-014,
- không tự mở task tiếp theo.
