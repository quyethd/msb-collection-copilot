from __future__ import annotations

from typing import Any

FIELD_LABELS: dict[str, str] = {
    "inflow_7d": "Tiền vào 7 ngày gần nhất",
    "net_cashflow_30d": "Dòng tiền ròng 30 ngày",
    "ptp_state": "Trạng thái cam kết thanh toán",
    "promise_date": "Ngày cam kết thanh toán",
    "source_next_action_date": "Ngày dự kiến xử lý tiếp theo",
    "latest_business_outcome": "Kết quả tương tác gần nhất",
    "treatment": "Hành động đề xuất",
    "channel": "Kênh xử lý",
    "when": "Thời điểm xử lý",
    "recovery_opportunity_score": "Điểm cơ hội thu hồi",
    "reason_code": "Lý do quyết định",
    "final_route": "Tuyến xử lý",
    "rule_id": "Mã quy tắc",
    "objective": "Mục tiêu",
}

TREATMENT_LABELS: dict[str, str] = {
    "WAIT": "Chờ theo dõi",
    "WAIT_SELF_CURE": "Chờ khách hàng tự thanh toán",
    "REMIND": "Nhắc thanh toán",
    "CONTACT": "Liên hệ khách hàng",
    "PTP_FOLLOW_UP": "Theo dõi cam kết thanh toán",
    "PTP_RECOVERY": "Xử lý cam kết thanh toán không thực hiện",
    "PARTIAL_PAYMENT": "Theo dõi khoản thanh toán một phần",
    "CALLBACK": "Gọi lại theo lịch hẹn",
    "VERIFY_CONTACT": "Xác minh thông tin liên hệ",
    "ESCALATE": "Chuyển mức xử lý cao hơn",
}

CHANNEL_LABELS: dict[str, str] = {
    "CALL": "Gọi điện",
    "SMS": "Tin nhắn SMS",
    "ZALO": "Zalo",
    "EMAIL": "Email",
    "FIELD": "Lực lượng hiện trường",
    "NONE": "Chưa cần liên hệ",
}

PTP_STATE_LABELS: dict[str, str] = {
    "NONE": "Chưa có cam kết",
    "OPEN": "Đang cam kết",
    "KEPT": "Đã thực hiện cam kết",
    "PARTIAL": "Thanh toán một phần",
    "BROKEN": "Không thực hiện cam kết",
}

REASON_CODE_LABELS: dict[str, str] = {
    "HARD_SUPPRESSED": "Bị hạn chế xử lý",
    "CALLBACK_DUE": "Đến lịch gọi lại",
    "INVALID_CONTACT": "Thông tin liên hệ không hợp lệ",
    "PARTIAL_PTP": "Cam kết thanh toán một phần",
    "BROKEN_PTP_RECENT_INFLOW": "Cam kết không thực hiện, có dòng tiền gần đây",
    "BROKEN_PTP": "Cam kết không thực hiện",
    "OPEN_PTP": "Đang cam kết thanh toán",
    "KEPT_PTP": "Đã thực hiện cam kết",
    "CALL_SELF_CURE": "Đáp ứng điều kiện chờ tự thanh toán",
    "CBS_SELF_CURE": "Đáp ứng điều kiện chờ tự thanh toán (CBS)",
    "RTP_ESCALATION": "Đã thanh toán lại, cần theo dõi",
    "CALL_DEFAULT": "Xử lý mặc định (gọi điện)",
    "CBS_DEFAULT": "Xử lý mặc định (CBS)",
    "OTHER_DEFAULT": "Xử lý mặc định (khác)",
}


def label_for_field(field: str) -> str:
    return FIELD_LABELS.get(field, field)


def label_for_value(field: str, value: Any) -> str:
    if value is None:
        return "—"
    if field == "treatment":
        return TREATMENT_LABELS.get(str(value), str(value))
    if field == "channel":
        return CHANNEL_LABELS.get(str(value), str(value))
    if field == "ptp_state":
        return PTP_STATE_LABELS.get(str(value), str(value))
    if field == "reason_code":
        return REASON_CODE_LABELS.get(str(value), str(value))
    return str(value)


def label_for_when(when: dict[str, Any]) -> str:
    wtype = when.get("type", "NONE")
    if wtype == "NONE":
        return "Chưa cần xử lý ngay"
    if wtype == "BEST_WINDOW":
        return f"Khung giờ tốt nhất {when.get('window')} ngày {when.get('date')}"
    if wtype == "SOURCE_DATETIME":
        return f"Theo lịch nguồn: {when.get('datetime')}"
    if wtype == "SOURCE_DATE":
        return f"Theo ngày cam kết: {when.get('date')}"
    if wtype == "TODAY":
        return f"Hôm nay ({when.get('date')})"
    return wtype
