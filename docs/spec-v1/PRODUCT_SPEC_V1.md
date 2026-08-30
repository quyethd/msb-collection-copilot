# PRODUCT_SPEC_V1 --- MSB Collection Decision Copilot

**Version:** 1.0\
**Status:** LOCKED FOR V1 BUILD\
**Track:** AI FOR MY TEAM\
**Primary user:** Collection Officer\
**Secondary user:** Team Leader / Collection Manager

## 0. Quy ước

-   **\[MSB-CONFIRMED\]**: nghiệp vụ đã được xác nhận từ thông tin dự
    án.
-   **\[PROTOTYPE-RULE\]**: quy tắc thiết kế cho prototype/hackathon,
    chưa phải chính sách MSB.
-   **\[ASSUMPTION\]**: giả định cần kiểm chứng nếu triển khai thật.
-   **\[CONFIGURABLE\]**: phải cấu hình được.
-   **\[OUT-OF-SCOPE\]**: không làm trong V1.

> **Implementation contract:** Codex MUST implement this specification.
> Codex MUST NOT invent, modify, optimize, reinterpret, or add
> collection business rules without explicit approval.

## 1. Bài toán

\[MSB-CONFIRMED\] Baseline ưu tiên hiện tại dùng **tổng dư nợ theo CIF**
và **MAX DPD theo CIF**. Một CIF có thể có nhiều khoản vay/sản phẩm.

Hypothesis cần kiểm chứng: dư nợ lớn + DPD cao phản ánh business urgency
nhưng chưa trực tiếp phản ánh recovery opportunity tại thời điểm hiện
tại.

## 2. Định vị

Collection Decision Copilot là AI Agent hỗ trợ Collection Officer/Team
Leader kết hợp policy hiện hữu với dư nợ, DPD, cashflow, PTP, payment
behavior và contact history để đề xuất ưu tiên tác nghiệp.

> **Từ "ai nợ nhiều và quá hạn lâu?" sang "đâu là cơ hội thu hồi tốt
> nhất ngay lúc này?"**

Agent khuyến nghị; con người quyết định.

## 3. Decision contract

Thông điệp demo: - **WHO** --- CIF nào? - **WHY** --- Vì sao? - **WHAT**
--- Treatment/mục tiêu nào? - **WHEN** --- Khi nào?

Implementation của WHAT gồm `treatment + channel + objective`.

## 4. Core flows

### PLAN

Lập danh sách ưu tiên hôm nay: baseline rank, copilot rank, score,
route, treatment, channel, when, reasons.

### INVESTIGATE

Customer 360: khoản vay, SUM outstanding, MAX DPD, cashflow, PTP,
call/operation history, score breakdown.

### EXPLAIN

Giải thích chỉ từ facts + rule IDs + evidence do tools trả về.

### SIMULATE

What-if: clone snapshot trong memory → override biến → chạy lại cùng
engine → before/after. Không sửa dữ liệu gốc.

## 5. V1 scope

### MUST

Synthetic portfolio; routing/policy layer; baseline; Recovery
Opportunity Score; priority queue; Customer 360; Decision Card;
PLAN/INVESTIGATE/EXPLAIN/SIMULATE; baseline-vs-Copilot;
Accept/Adjust/Skip; golden tests; GreenNode MaaS + AgentBase; benchmark
synthetic; AEV simulator.

### SHOULD

Agent trace; configurable thresholds/weights; team summary.

### LATER

ML challenger với dữ liệu phù hợp; real integrations; dialer/messages;
relationship opportunity/cross-sell.

### \[OUT-OF-SCOPE\]

Full collection system; production credit decisioning; autonomous
customer contact; real customer PII; ML training as core V1; complex
multi-agent; Kafka/Kubernetes; cross-sell trong core demo.

## 6. Human-in-the-loop

Agent MUST NOT tự thay official routing, sửa source data, liên hệ khách,
mark PTP fulfilled, hoặc override hard policy.

UI feedback: **Accept / Adjust / Skip**.

## 7. GreenNode contract

-   Intelligence: GreenNode MaaS.
-   Capabilities: tools/skills, MCP khi hữu ích.
-   Runtime: GreenNode AgentBase.
-   Deterministic policy/scoring là tools; LLM không thay rule engine.

7 business tools: Portfolio; Customer 360; Collection History; Cashflow
Intelligence; Collection Policy; Recovery Opportunity; Decision
Simulator.

## 8. Demo

1.  Baseline Total Outstanding + MAX DPD.
2.  Agent "lập kế hoạch hôm nay".
3.  Ranking thay đổi.
4.  Investigate CIF.
5.  Rule/score explanation.
6.  What-if.
7.  Policy compliance + benchmark.
8.  AEV simulator.
9.  GreenNode Agent trace.

## 9. Acceptance

-   100% golden hard-policy/routing expectations pass.
-   0 hard-policy violations.
-   Mọi recommendation có score breakdown + evidence-backed reason.
-   What-if không mutate source.
-   SUM outstanding/MAX DPD đúng tuyệt đối.
-   Agent không bịa reason ngoài tool evidence.
-   Demo end-to-end không dùng real customer data.
-   Deterministic engine test độc lập khi LLM lỗi.

## 10. Non-claims

Không claim proven uplift tại MSB, production recovery probability,
financial benefit từ dữ liệu thật, hoặc coi prototype weights là
official MSB policy.

## 11. GREENNODE_SKILLS_CONTRACT

**Status:** REQUIRED FOR V1 IMPLEMENTATION

Bộ skill chính thức của GreenNode phải được dùng như workflow triển khai Agent, không chỉ ghi tên trong slide.

### 11.1 Skill mapping

| Mục đích | Skill / module GreenNode | V1 |
|---|---|---|
| Khởi tạo / hướng dẫn project AgentBase | `/agentbase-wizard` | REQUIRED |
| AgentBase core/runtime workflow | `/agentbase` | REQUIRED |
| Tạo/cấu hình MaaS API key/model | `/agentbase-llm` | REQUIRED |
| Deploy Agent | `/agentbase-deploy` | REQUIRED |
| Runtime logs / monitoring | `/agentbase-monitor` | REQUIRED |
| Identity / secret access | `/agentbase-identity` | RECOMMENDED |
| Memory | `/agentbase-memory` | OPTIONAL |
| Gateway/API exposure | `/agentbase-gateway` | OPTIONAL/WHEN NEEDED |
| Runtime/platform policy | `/agentbase-policy` | OPTIONAL |
| Cleanup | `/agentbase-teardown` | REQUIRED FOR CLEANUP RUNBOOK |

`/agentbase-policy` là policy của runtime/platform; **không được thay thế Collection Policy Engine nghiệp vụ**.

### 11.2 GreenNode implementation gates

- **GN-01:** Collection Agent chạy thật trên GreenNode AgentBase Runtime.
- **GN-02:** Agent reasoning gọi model qua GreenNode MaaS.
- **GN-03:** Agent gọi được deterministic business tools.
- **GN-04:** Deploy được bằng AgentBase workflow/skills.
- **GN-05:** Runtime logs/trace có thể quan sát khi demo.
- **GN-06:** Không commit/expose `GREENNODE_CLIENT_SECRET`, MaaS API keys hoặc credentials.
- **GN-07:** Demo phân biệt rõ `LLM reasoning` và `Collection business rules`.
- **GN-08:** Agent failure không làm deterministic rule engine mất khả năng test/chạy độc lập.
- **GN-09:** GreenNode usage được mô tả trong README/repo để giám khảo reproduce được.
- **GN-10:** Các thư viện/framework/open-source được dùng phải ghi nguồn.

### 11.3 Model use

[CONFIGURABLE] Model cụ thể chọn từ GreenNode MaaS theo availability của tài khoản hackathon.

Ưu tiên:
1. một reasoning model cho PLAN/INVESTIGATE/EXPLAIN/SIMULATE;
2. không multi-model nếu chưa chứng minh cần thiết;
3. coding model có thể dùng trong quá trình development nhưng **không thay đổi business contract**.

### 11.4 Coding responsibility

GreenNode MaaS/AgentBase có thể hỗ trợ sinh/chạy code, nhưng source of truth vẫn là:
`PRODUCT_SPEC_V1 + RULE_BASE_V1 + SYNTHETIC_DATA_SPEC + GOLDEN_SCENARIOS_V1`.

Bất kỳ coding agent nào (Codex, GreenNode coding model, OpenClaw, Aider hoặc công cụ khác) đều:
- chỉ implement theo spec;
- phải chạy automated tests;
- không tự sửa rule nghiệp vụ;
- không tự tạo assumption mới mà không đánh dấu.
