# TASK-016-LANDING-PITCH-AI-CASE-BRIEF-REFINEMENT

## 0. Task identity

**Task ID:** `TASK-016-LANDING-PITCH-AI-CASE-BRIEF-REFINEMENT`  
**Project:** MSB Trợ Lý Thu Hồi Nợ  
**Repository:** `/opt/msb-collection-copilot`  
**Branch:** `master`

**Baseline:** TASK-013, TASK-014 và TASK-015 đã đóng production.

TASK-016 là một **landing refinement task**, không phải redesign toàn bộ ứng dụng.

Mục tiêu cuối:

> Biến landing hiện tại thành một **pitch deck tương tác trên web** có phong cách thống nhất với bộ slide MSB AI Hackathon, đồng thời phản ánh đầy đủ capability mới nhất: **AI Case Brief + GreenNode AgentBase bounded orchestration**.

---

# 1. North-star visual concept

Landing phải lấy cảm hứng trực tiếp từ phong cách của slide cover MSB AI Hackathon đã duyệt:

- nền trắng / xanh rất nhạt;
- headline navy lớn;
- các từ khóa quan trọng tô cam MSB;
- xanh lá dùng cho GreenNode, knowledge và data;
- mascot AI dạng 3D thân thiện;
- các card nghiệp vụ như đang “bay” quanh một câu chuyện chính;
- đường cong / con đường navy ở phần dưới để tạo cảm giác “từ dữ liệu đến hành động”;
- city / horizon / future imagery dùng tiết chế;
- các callout viết tay hoặc handwritten accent chỉ dùng ở vài điểm;
- khoảng trắng lớn;
- ít text nhưng hierarchy rất rõ;
- hình ảnh / infographic làm trọng tâm hơn card text;
- phong cách “corporate innovation / hackathon pitch”, không phải generic SaaS landing.

Concept cần tái hiện cảm giác:

> **MSB AI Hackathon slide deck → chuyển thành trải nghiệm web responsive**

Không copy nguyên slide 1:1.  
Phải chuyển visual language đó thành một landing responsive, có scroll rhythm và interaction.

---

# 2. Visual system bắt buộc

## 2.1. Màu sắc

Ưu tiên palette:

```text
MSB Navy:
dùng cho headline, nền section mạnh, footer, đường cong

MSB Orange:
dùng cho từ khóa, CTA, điểm nhấn hành động

Green:
dùng cho GreenNode, knowledge, data, trust/success

Light Blue / Off-white:
dùng cho background và section separation

White:
card / content surfaces
```

Không dùng quá nhiều gradient màu lạ.

---

## 2.2. Typography

Headline:

- rất lớn;
- navy;
- highlight 1–2 cụm từ bằng cam;
- line-height chặt;
- có thể xuống dòng chủ động như slide.

Ví dụ:

> Không tìm khách hàng nợ nhiều nhất.  
> **Tìm cơ hội thu hồi tốt nhất tiếp theo.**

Body:

- ngắn;
- dễ đọc;
- 2–3 dòng / block;
- không tạo “text wall”.

---

## 2.3. Shape language

Ưu tiên:

- card bo góc lớn;
- border nhạt;
- shadow nhẹ;
- card nổi / layered;
- infographic-panel;
- floating evidence cards;
- chips ngắn;
- circular icon badge;
- curved navy section divider / road motif.

Không biến mọi section thành:

```text
4 card giống nhau
→ 4 card giống nhau
→ 4 card giống nhau
```

---

## 2.4. Mascot

Mascot AI là visual anchor, không dùng ở mọi section.

Nên xuất hiện tại:

- Hero;
- AI Case Brief / Demo;
- GreenNode;
- Final CTA.

Không dùng mascot quá nhiều làm mất tính corporate.

---

# 3. Bugs bắt buộc sửa trước

## 3.1. Horizontal alignment defect

Hiện landing có cảm giác bị lệch quá nhiều sang phải.

Phải tìm root cause thực tế:

- container width;
- nested padding;
- grid sizing;
- absolute positioning;
- transform;
- wrapper offset;
- illustration positioning.

Không chữa bằng negative margin tùy tiện.

### Chuẩn container

Landing nên có một shared container concept:

```text
width: 100%
max-width: ~1180–1280px
margin-inline: auto
padding-inline: responsive
```

Hero có thể full-bleed background nhưng content phải nằm trong shared centered container.

Required:

```text
LANDING_HORIZONTAL_ALIGNMENT=PASS
HERO_VISUAL_BALANCE=PASS
NO_HORIZONTAL_OVERFLOW=PASS
```

---

## 3.2. Mojibake / icon defect

Hiện có lỗi kiểu:

```text
âœ“
```

Không dùng raw Unicode checkmark nếu pipeline hiện tại render không ổn.

Thay bằng:

- existing icon component;
- hoặc inline SVG.

Scan toàn landing cho:

```text
âœ“
â†’
â€¢
â€“
â€”
â€œ
â€
```

Required:

```text
MOJIBAKE_COUNT=0
PUBLIC_ICON_RENDERING=PASS
```

---

## 3.3. Team identity

Landing phải hiển thị rõ:

> **Nhóm thực hiện: Debt Radar**

Canonical team members nếu source/slide hiện tại đã xác nhận:

- Hà Đức Quyết — DigiLenO — Trưởng nhóm
- Phạm Huy Khánh — DigiLenO
- Nguyễn Thị Phương — DC

Nếu source hiện tại không xác nhận được đầy đủ, chỉ hiển thị:

> Nhóm thực hiện: Debt Radar

Không tự bịa thông tin.

Team block nên xuất hiện:

- hero / near-hero dưới CTA hoặc ở footer hero;
- final CTA/footer.

Required:

```text
DEBT_RADAR_VISIBLE=PASS
```

---

# 4. Landing final structure

TASK-014 có nhiều section đúng nhưng hơi dài.

TASK-016 rút lại thành 13 section chính:

```text
01. Hero
02. Bài toán
03. Giải pháp
04. Hành trình người dùng
05. AI Case Brief
06. Tình huống SYN002846
07. Mô phỏng What-if
08. Web + Zalo
09. Cách AI hoạt động
10. GreenNode trong sản phẩm
11. Tác động + Bằng chứng
12. Lộ trình + FAQ
13. Final CTA + Debt Radar
```

Mục tiêu:

> gọn hơn TASK-014 nhưng mạnh hơn về narrative.

---

# 5. Section 01 — HERO

## Giữ

Core thesis:

> **Không tìm khách hàng nợ nhiều nhất.  
> Tìm cơ hội thu hồi tốt nhất tiếp theo.**

Supporting copy:

> MSB Trợ lý Thu hồi Nợ giúp cán bộ ưu tiên đúng hồ sơ, hiểu vì sao hệ thống đề xuất hành động, mô phỏng thay đổi và hỏi nhanh trên Web hoặc Zalo.

Value chips:

- Đúng khách hàng
- Đúng hành động
- Đúng thời điểm

CTA:

- `Trải nghiệm bản demo`
- `Xem hành trình demo`

Notice:

> Bản demo dùng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật.

## Thêm

Một dòng về AI Case Brief:

> **AI Case Brief giúp cán bộ nắm nhanh tình trạng, bằng chứng quan trọng và lý do của quyết định trên từng hồ sơ.**

Team identity:

> **Nhóm thực hiện: Debt Radar**

## Visual concept

Hero nên có:

### Left
- product name;
- thesis;
- subcopy;
- GreenNode badge;
- 3 value chips;
- CTA;
- team identity.

### Right
Một composition kiểu slide:
- customer card;
- score 47;
- action card;
- mini knowledge search;
- mascot;
- orange arrow / flow;
- green data block.

Hero visual có thể dùng existing approved asset làm visual reference hoặc một số sub-assets, nhưng HTML content phải responsive.

Không đặt text quá xa về giữa/phải như hiện tại.

---

# 6. Section 02 — BÀI TOÁN

## Headline

> **Cán bộ không thiếu dữ liệu.  
> Điểm khó là biến dữ liệu thành hành động hôm nay.**

## Nội dung

Giữ 4 pain point:

1. Danh sách dài nhưng thứ tự chưa phản ánh đầy đủ cơ hội thu hồi.
2. Biết khách thuộc CALL/CBS nhưng chưa chắc biết hôm nay nên làm gì.
3. Dữ liệu và bằng chứng nằm rời rạc.
4. Khó giải thích quyết định, đào tạo và kiểm soát chất lượng.

## Close

> **Bài toán không chỉ là ai nợ nhiều, mà là hôm nay nên ưu tiên ai, làm gì và vì sao.**

## Visual

Ưu tiên dùng approved infographic “Bài toán hiện tại”.

Không dựng thêm 4 card trùng infographic nếu ảnh đã thể hiện đủ.

---

# 7. Section 03 — GIẢI PHÁP

## Headline

> **Một Trợ lý giúp biến dữ liệu thành quyết định có căn cứ**

5 capability:

### 1. Danh sách ưu tiên
Xác định hồ sơ nên xử lý trước.

### 2. Giải thích quyết định
Cho cán bộ biết vì sao hệ thống đề xuất như vậy.

### 3. Mô phỏng tình huống
Thử thay đổi bối cảnh mà không ảnh hưởng dữ liệu thật.

### 4. Kiến thức có nguồn
Tra cứu quy trình và kiến thức nghiệp vụ.

### 5. AI Case Brief
Tóm tắt nhanh từng hồ sơ:
- tình trạng;
- bằng chứng;
- lý do;
- điều cần chú ý.

## Visual

Không dùng 5 card cùng trọng lượng.

Có thể:

- 4 capability nhỏ;
- AI Case Brief làm capability lớn / highlighted feature.

---

# 8. Section 04 — HÀNH TRÌNH NGƯỜI DÙNG

## Conceptual journey

```text
Trang giới thiệu
→ Đăng nhập
→ Danh sách ưu tiên
→ Hồ sơ khách hàng
→ AI Case Brief
→ Hỏi Trợ lý / Mô phỏng
→ Cán bộ chốt hành động
```

Giữ infographic user journey đã duyệt nếu vẫn phù hợp.

Không regenerate ảnh chỉ để thêm một bước nếu làm giảm chất lượng.

Nếu infographic cũ chưa có AI Case Brief:

thêm HTML strip dưới ảnh:

> **Mới: AI Case Brief giúp cán bộ hiểu nhanh hồ sơ trước khi hỏi sâu hoặc mô phỏng.**

---

# 9. Section 05 — AI CASE BRIEF

Đây là section mới quan trọng nhất của TASK-016.

## Label

`TÓM TẮT AI CHO HỒ SƠ`

## Headline

> **Hiểu một hồ sơ trong vài chục giây**

## Story

AI Case Brief tổng hợp:

- thông tin khách hàng;
- current decision;
- Recovery Opportunity score;
- dòng tiền;
- PTP;
- lịch sử liên hệ;
- relevant knowledge khi cần.

## UI concept

Dựng một large product card:

```text
┌────────────────────────────────────────────┐
│ Tóm tắt AI cho hồ sơ            Làm mới  │
│ SYN002846                                  │
│                                            │
│ CALL        47/100      Chờ tự thanh toán │
│                                            │
│ TÌNH TRẠNG HIỆN TẠI                       │
│ ...                                        │
│                                            │
│ VÌ SAO?                                    │
│ • ...                                      │
│ • ...                                      │
│                                            │
│ BẰNG CHỨNG QUAN TRỌNG                      │
│ • ...                                      │
│                                            │
│ CÁN BỘ NÊN CHÚ Ý                           │
│ • ...                                      │
│                                            │
│ [Xem bằng chứng] [Hỏi thêm]                │
└────────────────────────────────────────────┘
```

## Public wording AgentBase trong section này

> **AgentBase giúp Trợ lý xác định đúng dữ liệu và công cụ cần dùng cho từng câu hỏi, thay vì phụ thuộc vào một kịch bản cố định.**

Không public:
- tool names;
- planner rounds;
- fallback level;
- raw JSON;
- validator internals.

---

# 10. Section 06 — TÌNH HUỐNG SYN002846

## Headline

> **Thuộc tuyến gọi không có nghĩa hôm nay nhất thiết phải gọi**

Canonical facts:

```text
DPD: 11 ngày
Tiền vào 7 ngày: 48 triệu đồng
Dòng tiền ròng 30 ngày: 168 triệu đồng
PTP: chưa có
Route: CALL
Score: 47/100
Action: Chờ khách hàng tự thanh toán
Channel: Chưa cần liên hệ
```

Giữ approved demo visual.

## Required disclaimer

> **Điểm cơ hội thu hồi là điểm ưu tiên tương đối, không phải xác suất khách hàng sẽ thanh toán.**

Không public:

```text
WAIT_SELF_CURE
NONE
NBA-300
```

---

# 11. Section 07 — MÔ PHỎNG WHAT-IF

## Headline

> **Cùng một chính sách, bối cảnh thay đổi thì hành động có thể thay đổi**

### Before

```text
Tiền vào 7 ngày: 48 triệu
Action: Chờ khách hàng tự thanh toán
Channel: Chưa cần liên hệ
```

### Giả định

```text
Tiền vào 7 ngày: 0
Dòng tiền ròng 30 ngày: 0
```

### After

```text
Action: Liên hệ khách hàng
Channel: Gọi điện
```

## Chốt

> **Decision Core tính lại kết quả; AI chỉ giải thích trạng thái mới.**

Notice:

> Mô phỏng không thay đổi dữ liệu thật.

---

# 12. Section 08 — WEB + ZALO

## Headline

> **Xem sâu trên Web. Hỏi nhanh qua Zalo.**

### Web

- danh sách ưu tiên;
- hồ sơ khách hàng;
- AI Case Brief;
- score/evidence;
- simulation;
- assistant.

### Zalo

Ví dụ:

```text
tính điểm SYN002846

nếu nó không có tiền vào tuần này thì sao

thế giờ làm gì
```

Chốt:

> **Hai kênh khác nhau, cùng một Bộ máy quyết định.**

Không claim:
- autonomous customer messaging;
- OpenClaw;
- AgentBase điều khiển Zalo transport.

---

# 13. Section 09 — CÁCH AI HOẠT ĐỘNG

TASK-014 từng có nhiều section kỹ thuật bị trùng.

TASK-016 gộp narrative thành section này.

## Headline

> **AI hiểu câu hỏi. Bộ máy nghiệp vụ quyết định.**

## Public diagram

```text
Cán bộ
↓
GreenNode AgentBase
↓
Chọn đúng dữ liệu / công cụ
↓
Dữ liệu khách hàng ─┐
Dòng tiền           │
PTP                 │
Lịch sử liên hệ     ├→ Canonical context
Decision Core       │
Simulation          │
Knowledge           ┘
↓
GLM 5.2
↓
Tóm tắt / giải thích
↓
Cán bộ
```

Không public validator implementation chi tiết.

## AI làm

- hiểu câu hỏi;
- điều phối nguồn dữ liệu;
- tra cứu;
- tổng hợp;
- giải thích.

## AI không làm

- không đổi route;
- không đổi score;
- không thay policy;
- không tự gọi khách;
- không tự tạo PTP;
- không tự thực hiện outbound action.

---

# 14. Section 10 — GREENNODE TRONG SẢN PHẨM

Đây là section phục vụ Best GreenNode.

## Headline

> **GreenNode giúp Trợ lý hiểu đúng câu hỏi và dùng đúng công cụ**

## 1. AgentBase

Copy:

> **Điều phối đúng công cụ và nguồn dữ liệu theo từng câu hỏi trong phạm vi được cho phép.**

Được phép claim:

> **AgentBase đang được sử dụng trong AI Case Brief để lựa chọn công cụ phù hợp cho từng câu hỏi.**

Không được claim:
- AgentBase quyết định nghiệp vụ;
- mọi production request đều chạy AgentBase.

## 2. GreenNode MaaS + GLM 5.2

> **Tổng hợp và diễn giải dữ liệu, kết quả nghiệp vụ thành ngôn ngữ dễ hiểu cho cán bộ.**

## 3. GreenNode Vector Database + Qwen Flash

> **Tra cứu kiến thức nghiệp vụ có nguồn.**

## 4. Local multilingual embedding

> **Nhúng ngôn ngữ đa ngôn ngữ chạy cục bộ, nằm ngoài GreenNode-hosted boundary.**

## Strong close

> **Decision Core quyết định đúng. GreenNode giúp cán bộ hiểu và khai thác quyết định đó nhanh hơn.**

---

# 15. Section 11 — TÁC ĐỘNG + BẰNG CHỨNG

## Impact

Giữ:

```text
3.000 hồ sơ demo
1.740 thuộc tuyến CALL
32 thuộc CALL nhưng hiện chưa cần gọi ngay
~1.065 giờ/năm
~106,5 triệu đồng/năm
```

## Disclaimer

> **Ước tính theo giả định của bản demo, không phải ROI đã đạt.**

> **32 hồ sơ không đồng nghĩa đã giảm được 32 cuộc gọi.**

## Production AI assurance

Không show developer metrics kiểu test count/commit.

Show business-safe evidence:

- Decision parity: **100%**
- Score parity: **100%**
- Wrong CIF: **0**
- Cross-CIF context leak: **0**
- Simulation context leak: **0**
- Unsupported decision claim: **0**

Copy:

> **AI Case Brief được kiểm soát để giữ nguyên kết quả Decision Core và không trộn dữ liệu giữa các hồ sơ.**

---

# 16. Section 12 — ROADMAP + FAQ

## Roadmap

### Hiện tại

- Web
- Zalo
- Decision Core
- Simulation
- RAG
- AI Case Brief
- AgentBase bounded orchestration

### Tiếp theo

- T24
- DigiLenO
- Contact Center
- real-data shadow pilot
- outcome measurement
- officer feedback loop
- AI-assisted call preparation

## Shadow Mode Pilot

```text
Vận hành hiện tại
+
Copilot chạy song song
↓
So sánh recommendation với actual outcome
↓
Đo hiệu quả trước khi rollout
```

Đây là bridge từ Hackathon → production MSB.

## FAQ cập nhật

1. Rule đã quyết định rồi thì AI để làm gì?
2. Đây có phải chatbot gắn rule không?
3. Tại sao không để LLM tự quyết định?
4. GreenNode được dùng ở đâu?
5. Điểm 47 có phải 47% không?
6. 32 hồ sơ có nghĩa giảm 32 cuộc gọi không?

---

# 17. Section 13 — FINAL CTA + TEAM

## Visual concept

Phần cuối nên lấy cảm hứng mạnh từ slide:

- nền navy;
- đường cong / road;
- sunset / city motif nếu existing asset support;
- orange CTA;
- mascot nhỏ;
- typography lớn.

Headline:

> **Từ dữ liệu hôm nay đến hành động hiệu quả hơn**

Supporting:

> MSB Trợ lý Thu hồi Nợ giúp cán bộ ưu tiên đúng hồ sơ, hiểu rõ lý do và hành động có căn cứ.

CTA:

> **Bắt đầu trải nghiệm**

Team:

> **Nhóm thực hiện: Debt Radar**

Footer:

```text
MSB AI Hackathon 2026
Debt Radar
Powered by GreenNode AI
```

---

# 18. What to KEEP / REMOVE / ADD

| Thành phần | Quyết định |
|---|---|
| Core hero thesis | GIỮ |
| 3 value chips | GIỮ + sửa icon |
| Problem | GIỮ |
| Solution | GIỮ + AI Case Brief |
| User Journey | GIỮ + update narrative |
| Demo gallery | GIỮ, không mở rộng |
| SYN002846 | GIỮ |
| Score 47 | GIỮ |
| Simulation | GIỮ |
| Zalo demo | GIỮ |
| Two assistant flows image | GIỮ ảnh |
| System architecture image | GIỮ ảnh |
| Separate AI-control section | BỎ / GỘP |
| GreenNode | GIỮ + update AgentBase |
| AI Case Brief | THÊM section |
| Production AI evidence | THÊM |
| Impact | GIỮ |
| Judge summary standalone | GIẢM/GỘP |
| FAQ | GIỮ + update |
| Roadmap | GIỮ + Shadow Mode |
| Final CTA | GIỮ |
| Debt Radar | THÊM rõ ràng |

---

# 19. Responsive concept

Test:

```text
1366x768
1440x900
1920x1080
390x844
```

Desktop:
- giữ slide-like composition.

Mobile:
- chuyển từ “slide composition” sang vertical story;
- mascot / floating cards không overlap text;
- infographic có thể mở phóng to;
- CTA luôn rõ;
- typography không bị shrink quá nhỏ.

Không cố giữ bố cục 16:9 nguyên xi trên mobile.

---

# 20. Accessibility

- semantic headings;
- meaningful alt;
- buttons có label;
- focus state rõ;
- contrast đủ;
- gallery keyboard accessible;
- critical information không chỉ nằm trong ảnh.

---

# 21. Performance

- lazy-load ảnh below-the-fold;
- không dùng ảnh raw quá nặng nếu có thể optimize;
- không thêm library nặng;
- reuse current frontend stack;
- Hero visual cần ưu tiên load hợp lý.

---

# 22. Acceptance gates — UI

```text
LANDING_HORIZONTAL_ALIGNMENT=PASS
HERO_VISUAL_BALANCE=PASS
NO_HORIZONTAL_OVERFLOW=PASS

MOJIBAKE_COUNT=0
PUBLIC_ICON_RENDERING=PASS

DEBT_RADAR_VISIBLE=PASS

DESKTOP_1366_QA=PASS
DESKTOP_1440_QA=PASS
DESKTOP_1920_QA=PASS
MOBILE_390_QA=PASS

VISUAL_STYLE_MATCHES_MSB_HACKATHON_CONCEPT=PASS
SLIDE_TO_WEB_VISUAL_CONTINUITY=PASS
```

---

# 23. Acceptance gates — Story

```text
HERO_THESIS=PASS
PROBLEM_STORY=PASS
SOLUTION_STORY=PASS

AI_CASE_BRIEF_VISIBLE=PASS
AI_CASE_BRIEF_POSITIONING=PASS

USER_JOURNEY_UPDATED=PASS

SYN002846_STORY=PASS
RECOVERY_SCORE_TRUTH=PASS
SIMULATION_STORY=PASS

WEB_ZALO_STORY=PASS

AGENTBASE_ROLE_VISIBLE=PASS
DECISION_CORE_AUTHORITY_VISIBLE=PASS

GREENNODE_STORY=PASS

IMPACT_STORY=PASS
ROADMAP_STORY=PASS
FAQ_UPDATED=PASS
```

---

# 24. Acceptance gates — AI / GreenNode truth

```text
AGENTBASE_PUBLIC_TRUTH=PASS

GLM_ROLE_TRUTH=PASS
QWEN_ROLE_TRUTH=PASS
VECTOR_DB_ROLE_TRUTH=PASS
LOCAL_EMBEDDING_TRUTH=PASS

DECISION_CORE_CHANGED=NO
BUSINESS_SEMANTICS_DRIFT=0
```

Required public truth:

> AgentBase chọn công cụ / nguồn dữ liệu.

Forbidden public claim:

> AgentBase quyết định treatment / route / score.

---

# 25. Acceptance gates — AI Case Brief

```text
AI_CASE_BRIEF_DESCRIPTION=PASS
AI_CASE_BRIEF_DOES_NOT_CLAIM_DECISION_AUTHORITY=PASS

PRODUCTION_DECISION_PARITY_DISPLAYED_CORRECTLY=PASS
PRODUCTION_SCORE_PARITY_DISPLAYED_CORRECTLY=PASS

WRONG_CIF_CLAIM=0
UNSUPPORTED_AI_CLAIM=0
```

---

# 26. Acceptance gates — Public copy

```text
PUBLIC_INTERNAL_LABEL_SCAN=PASS

TASK_ID_LEAK=0
COMMIT_LEAK=0
RAW_ENUM_LEAK=0
INTERNAL_TOOL_NAME_LEAK=0

PUBLIC_LANGUAGE_POLICY=PASS
```

Allowed technical names:

- AgentBase
- GLM 5.2
- Qwen Flash
- Vector Database
- Decision Core

Forbidden implementation labels:

```text
get_current_decision
MAX_TOOL_CALLS
fallback level 2
task id
commit sha
internal module names
```

---

# 27. Acceptance gates — Regression

TASK-016 là frontend landing task.

Required:

```text
FRONTEND_TESTS=PASS
FRONTEND_BUILD=PASS

APPLICATION_SMOKE=PASS
APP_ZALO_SMOKE=PASS
SESSION_SMOKE=PASS

BACKEND_CHANGED=NO
AGENTBASE_RUNTIME_CHANGED=NO
ZALO_RUNTIME_CHANGED=NO

BUSINESS_SEMANTICS_DRIFT=0
```

Không rerun giant backend suites nếu backend không đổi.

---

# 28. Acceptance gates — Production

```text
PUBLIC_TLS=PASS
PUBLIC_LANDING_HTTP=PASS

PRODUCTION_DESKTOP_QA=PASS
PRODUCTION_MOBILE_QA=PASS

PRODUCTION_NO_OVERFLOW=PASS
PRODUCTION_MOJIBAKE_COUNT=0
PRODUCTION_DEBT_RADAR_VISIBLE=PASS

PRODUCTION_AI_CASE_BRIEF_STORY=PASS
PRODUCTION_AGENTBASE_STORY=PASS
PRODUCTION_GREENNODE_STORY=PASS

PRODUCTION_APPLICATION_SMOKE=PASS
```

Nếu server DNS vẫn bị intercept:

- dùng hostname-preserving resolver pinning;
- không disable TLS verification.

---

# 29. 60–90 second judge comprehension gate

TASK-016 chỉ PASS nếu một BGK mới vào landing và trong 60–90 giây có thể trả lời:

1. Bài toán sản phẩm đang giải quyết là gì?
2. Sản phẩm dành cho ai?
3. Vì sao không chỉ ưu tiên theo dư nợ / DPD?
4. AI thực sự làm gì?
5. AgentBase làm gì?
6. Decision Core làm gì?
7. GreenNode tạo giá trị gì?
8. Web và Zalo liên quan với nhau thế nào?
9. AI Case Brief mang lại lợi ích gì?
10. Từ demo lên pilot MSB sẽ đi theo hướng nào?

Required:

```text
JUDGE_90_SECOND_COMPREHENSION=PASS
```

---

# 30. Source scope

TASK-016 chỉ được sửa:

- landing components;
- landing CSS/styles;
- landing copy;
- landing tests;
- landing asset references;
- TASK-016 task/report files.

Không sửa:

- backend;
- Decision Core;
- AgentBase;
- Zalo;
- RAG runtime;
- simulation logic;
- auth;
- service config.

Required:

```text
SOURCE_SCOPE=PASS
BACKEND_CHANGED=NO
AGENTBASE_RUNTIME_CHANGED=NO
BUSINESS_RULE_CHANGED=NO
```

---

# 31. Workflow

```text
INSPECT
→ MAP CURRENT SECTIONS
→ DESIGN REFINEMENT
→ IMPLEMENT
→ FRONTEND TEST
→ BUILD
→ DESKTOP/MOBILE VISUAL QA
→ COPY/TRUTH AUDIT
→ VERY AUDIT
→ COMMIT
→ BACKUP
→ DEPLOY FRONTEND ONLY
→ PUBLIC QA
→ APP SMOKE
→ CLOSEOUT
```

---

# 32. Task report

Create:

`task-results/TASK-016-LANDING-PITCH-AI-CASE-BRIEF-REFINEMENT-FINAL.md`

Record:

```text
TASK_ID=TASK-016-LANDING-PITCH-AI-CASE-BRIEF-REFINEMENT

LANDING_HORIZONTAL_ALIGNMENT=PASS
HERO_VISUAL_BALANCE=PASS
MOJIBAKE_COUNT=0
DEBT_RADAR_VISIBLE=PASS

VISUAL_STYLE_MATCHES_MSB_HACKATHON_CONCEPT=PASS
SLIDE_TO_WEB_VISUAL_CONTINUITY=PASS

AI_CASE_BRIEF_VISIBLE=PASS
AGENTBASE_ROLE_VISIBLE=PASS
DECISION_CORE_AUTHORITY_VISIBLE=PASS
GREENNODE_STORY=PASS

RECOVERY_SCORE_TRUTH=PASS
BUSINESS_SEMANTICS_DRIFT=0

FRONTEND_TESTS=PASS
FRONTEND_BUILD=PASS

DESKTOP_1366_QA=PASS
DESKTOP_1440_QA=PASS
DESKTOP_1920_QA=PASS
MOBILE_390_QA=PASS

PUBLIC_INTERNAL_LABEL_SCAN=PASS
PUBLIC_LANGUAGE_POLICY=PASS

JUDGE_90_SECOND_COMPREHENSION=PASS

VERY_AUDIT=PASS

READY_TO_COMMIT=YES/NO
```

---

# 33. Final design principle

> **Giữ tinh thần của slide MSB AI Hackathon, nhưng biến nó thành một landing responsive, mạch lạc và có thể tự kể câu chuyện sản phẩm.**

> **AI Case Brief là capability mới nổi bật. AgentBase là lớp điều phối thông minh. Decision Core vẫn là nguồn quyết định nghiệp vụ. GreenNode là lớp AI giúp cán bộ hiểu, tra cứu và khai thác quyết định nhanh hơn.**
