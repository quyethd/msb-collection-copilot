# SYNTHETIC_DATA_SPEC --- MSB Collection Decision Copilot

**Version:** 1.0\
**Target:** \~3,000 synthetic CIF\
**Purpose:** demo + regression + benchmark. Không dùng real
PII/confidential data.

## 1. Principles

Deterministic seed; dữ liệu có tương quan nghiệp vụ; golden cases được
cài chủ đích; source fields tách derived features; mọi KPI từ dataset
phải ghi **SIMULATED**.

Default seed \[CONFIGURABLE\]: `20260828`.

## 2. Scale

-   3,000 CIF
-   \~4,500--5,500 loan accounts
-   \~50k--80k cashflow transactions
-   \~10k--15k payment events
-   \~5k--8k call events
-   \~2k--3k operation/PTP events
-   20 golden scenarios, 5 HERO

## 3. Tables

### customer

`cif PK, customer_name(synthetic), segment, heatmap, created_at`

### loan_account

`account_id PK, cif FK, product_type, outstanding_amount, overdue_amount, dpd, due_amount, due_date, status`

Derived: `SUM(outstanding_amount)` và `MAX(dpd)` theo CIF.

### collection_assignment

`id,cif,base_route,challenge_override_route,effective_route,assignment_date`

Challenge override là explicit synthetic input; không giả lập rằng đã
biết challenge rule thật.

### cashflow_transaction

`transaction_id,cif,transaction_date,direction(IN/OUT),amount,source_type,balance_after`
Synthetic source types: SALARY, BUSINESS_INCOME, TRANSFER, DEPOSIT,
OTHER.

### payment_event

`payment_id,cif,account_id,payment_date,amount,payment_type,linked_ptp_id`

### operation_result

Synthetic analogue của `rb_soft_collection.operation_result_etl`, gồm
tối thiểu:
`id,cif,operation_object,relation,detail_relation,operation_address,operation_result,payment_ptp_date,payment_ptp_number,payment_ptp_ability,overall_customer_assessment,overdue_reason,detail_overdue_reason,debt_solution,detail_operation_content,is_change_contact_info,is_current_address,is_current_phone_number,next_action_date,next_operation_channel,new_phone_number,need_investigation,work_status,income_status,affected_repayment_source,proposed_solution,created_at,created_by,updated_at,updated_by`.

### call_history

Synthetic analogue của `rb_soft_collection.call_history`:
`id,call_id,call_time,end_time,employee_name,extension,call_phone,relationship,cif,status,ring_duration,talk_duration,call_type,record_file,customer_name,created_at,created_by,updated_at,updated_by,request_code,start_at,pbx,end_at,destination_name,operation_status,operation_source`.

Không tạo recording URL/audio thật.

## 4. Derived feature view

`customer_recovery_features` gồm: total_outstanding_cif, max_dpd_cif,
route, inflow_3d/7d/30d, outflow_30d, net_cashflow_30d,
recent_large_inflow, salary_like_income, income_stability_90d,
current_due_amount, liquidity_to_due_ratio,
latest_ptp_status/amount/date, fulfillment_ratio, kept/partial/broken
counts, rtp_count, utc_ratio, successful_contact_ratio, failed streak,
avg_talk_duration, best_contact_window, next_action_date,
latest_operation_result, total score và 6 component scores.

## 5. Correlation rules

-   Stable salary → periodic inflow.
-   Strong cashflow tăng ability nhưng không bắt buộc willingness cao.
-   BROKEN → promise quá hạn không đủ payment.
-   PARTIAL → payment \>0 và \< promise.
-   KEPT → payment \>= promise.
-   High contactability → successful calls tập trung ở time windows.
-   NIN → không tiếp tục successful call trên cùng số trừ khi có
    new_phone_number.
-   Self-cure → lịch sử low-DPD rồi payment mà không phụ thuộc live
    call.

## 6. Archetypes \[PROTOTYPE\]\[CONFIGURABLE\]

High urgency/low opportunity; moderate urgency/high opportunity;
self-cure; PTP due; broken PTP; partial PTP; UTC streak; NIN; NA
callback; RTP; stable payer temporary lateness; low cashflow/low
willingness.

Không coi tỷ lệ synthetic là phân bố MSB thật.

## 7. Ground truth

Mỗi golden record:
`scenario_id, expected_route, expected_treatment, expected_channel, expected_timing_class, expected_priority_band, must_trigger_rule_ids, must_not_trigger_rule_ids, expected_score_constraints, rationale`.

Không train model trên generated labels rồi claim real-world accuracy.

## 8. Benchmark

Snapshots: `portfolio_baseline_snapshot`, `portfolio_copilot_snapshot`,
`golden_scenario_expected`.

Metrics: hard-policy violation rate; golden treatment agreement;
explanation coverage; Precision@TopN synthetic; expected contact
success/100 actions **SIMULATED**; expected recovery/100 actions
**SIMULATED**; prioritization runtime.

## 9. Privacy

Synthetic CIF/name/phone/email; no production records; no real
recordings; no secrets; addresses null/obviously synthetic.

## 10. Outputs

DB seed/CSV/SQL; `generation_manifest.json`; golden fixtures; derived
feature view; validation report.

## 11. Acceptance

20 golden CIF stable by seed; referential integrity; aggregates
reconcile; PTP statuses reconcile; no impossible monetary values; all
golden rules pass; synthetic labels distinguishable from MSB-confirmed
fields.

## 12. GreenNode development-data boundary

- Chỉ synthetic dataset được gửi vào AgentBase/MaaS trong hackathon.
- Không đưa production dump, PII, call recording thật hoặc secret vào prompt/tool context.
- Test fixtures cho AgentBase phải dùng golden CIF synthetic.
- Log/trace GreenNode không được chứa credential.
- Dataset phải có cờ `is_synthetic=true` hoặc metadata tương đương ở manifest.
