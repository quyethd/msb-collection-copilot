# GOLDEN_SCENARIOS_V1 --- MSB Collection Decision Copilot

**Version:** 1.0\
**20 scenarios; G01--G05 = HERO**

Exact numeric score chưa khóa; weights/thresholds configurable. Tests
khóa precedence, route, treatment, relative behavior và evidence.

## G01 HERO --- High debt/high DPD nhưng opportunity thấp

Input: CALL; outstanding cao nhất hero set; DPD65; no meaningful
inflow30d; 3 broken PTP; 5 UTC/fail. Expected: route CALL; baseline trên
G02; Copilot không được #1 chỉ vì debt/DPD; willingness/contactability
thấp; explanation nêu high urgency nhưng low opportunity.

## G02 HERO --- Moderate debt + recent inflow + PTP due

Input: CALL; outstanding150M; DPD18; inflow40M; PTP15M due today; best
contact 15--17. Expected: PTP_FOLLOW_UP/PTP_RECOVERY theo due-state
config; CALL; 15--17; ability/timing cao; dưới demo config Copilot rank
\> G01; reasons = inflow + PTP + contact window.

## G03 HERO --- CALL route nhưng self-cure

Input: CALL; DPD5; stable/good cashflow; prior low-DPD quick cures; no
broken PTP. Expected: route vẫn CALL; WAIT_SELF_CURE; NONE/digital
configurable; trigger SELF-001/002; không đổi route CBS.

## G04 HERO --- Broken PTP + recent inflow

Input: CALL; PTP20M expired beyond grace; paid0; inflow35M;
contactability tốt. Expected: BROKEN; PTP_RECOVERY; CALL; timing high;
explain broken commitment + ability + contactability.

## G05 HERO --- What-if

Original: CALL, moderate opportunity, no recent inflow. Override: +30M
inflow today. Expected: source unchanged; ability tăng; timing có thể
tăng; total score tăng; recommendation/rank có thể tăng theo demo
config; trả before/after deltas.

## G06 --- CBS reminder

RED + YELLOW + DPD2; no challenge override; due soon. Expected: CBS;
REMIND; digital channel configurable.

## G07 --- Challenge CBS→CALL

Base CBS + explicit synthetic override CALL. Expected: base/effective
route đều trace; effective CALL; không claim challenge logic thật.

## G08 --- Challenge CALL→CBS

Base CALL + explicit override CBS. Expected: effective CBS; trace source
override.

## G09 --- PTP KEPT

Promise20M, actual\>=20M. Expected: KEPT; không PARTIAL/BROKEN;
willingness positive.

## G10 --- PTP PARTIAL

Promise20M, actual10M. Expected: PARTIAL; ratio0.5; không KEPT;
PARTIAL_PAYMENT/PTP_FOLLOW_UP.

## G11 --- PTP BROKEN

Promise20M, actual0, beyond grace. Expected: BROKEN; negative
willingness + follow-up urgency.

## G12 --- PTP OPEN

Promise date future, actual0. Expected: OPEN; không BROKEN.

## G13 --- NIN

Latest operation=NIN. Expected: VERIFY_CONTACT; không blind-call cùng
known-invalid number; explanation dựa NIN.

## G14 --- NA callback

Latest operation=NA; next_action_date tomorrow; next channel CALL.
Expected: CALLBACK; CALL; explicit next action override generic
best-time.

## G15 --- UTC streak

5 recent UTC; low contact ratio. Expected: contactability thấp; không
suy diễn unwillingness chỉ từ UTC.

## G16 --- RTP

Recent RTP; cashflow tốt; technical contact success. Expected: ability
có thể cao nhưng willingness giảm; chứng minh ability ≠ willingness.

## G17 --- High DPD + strong cashflow

CALL; DPD35; recent strong inflow; contactability tốt. Expected: không
self-cure chỉ vì cashflow; urgency + ability/timing high; CONTACT/PTP
treatment tùy PTP.

## G18 --- Boundary self-cure

CALL-eligible low DPD; prior quick cures; stable income; no broken
PTP/RTP. Expected: WAIT_SELF_CURE; explain historical pattern.

## G19 --- Technical Success ≠ PTP

call_history.status=Success; không có operation PTP; talk\>0. Expected:
technical connection evidence only; tuyệt đối không infer PTP.

## G20 --- Multi-loan aggregation

Accounts: 100M/DPD4; 250M/DPD12; 50M/DPD7. Expected: total
outstanding=400M; MAX DPD=12; AGG-001/002 pass exact.

## Live demo order

G01 vs G02 → G03 → G04 → G05 → automated summary 20 scenarios.

## Global gates

20/20 aggregation/PTP/precondition assertions; 0 hard-policy violations;
0 simulation mutations; 0 technical-status-as-business-outcome; mọi
recommendation có rule IDs + evidence; mọi synthetic KPI ghi
synthetic/simulated.

## GreenNode Agent acceptance scenarios

Ngoài deterministic assertions, 5 HERO scenarios phải chạy qua AgentBase:

- **GA-01 / G01:** Agent giải thích được vì sao baseline cao nhưng opportunity thấp, không invent thêm facts.
- **GA-02 / G02:** Agent gọi đúng tools để lấy cashflow + PTP + contact window trước khi khuyến nghị.
- **GA-03 / G03:** Agent không đổi CALL route khi treatment là WAIT_SELF_CURE.
- **GA-04 / G04:** Agent không suy luận `BROKEN` nếu deterministic PTP tool chưa trả BROKEN.
- **GA-05 / G05:** SIMULATE dùng Decision Simulator tool và trả before/after delta; source snapshot unchanged.

**Gate:** 5/5 Agent HERO flows pass trước demo freeze.
