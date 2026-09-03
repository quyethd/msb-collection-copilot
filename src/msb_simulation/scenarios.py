from __future__ import annotations

from typing import Any

from .engine import SimulationEngine
from .models import SimulationResult

HERO_SCENARIO_A = {
    "label": "SCENARIO_A_CASHFLOW_CHANGE",
    "cif": "GOLDEN_G03",
    "changes": {"inflow_7d": 20_000_000, "net_cashflow_30d": 50_000_000},
    "description": "Tăng dòng tiền vào gần đây → khách hàng đáp ứng điều kiện chờ tự thanh toán",
}

HERO_SCENARIO_B = {
    "label": "SCENARIO_B_BROKEN_PROMISE",
    "cif": "SYN000141",
    "changes": {"ptp_state": "BROKEN"},
    "description": "Khách hàng không thực hiện cam kết thanh toán → cần xử lý thu hồi",
}

HERO_SCENARIO_C = {
    "label": "SCENARIO_C_OPEN_PROMISE",
    "cif": "GOLDEN_G03",
    "changes": {"ptp_state": "OPEN", "promise_date": "2026-09-15"},
    "description": "Khách hàng cam kết thanh toán vào ngày cụ thể → theo dõi cam kết",
}

SYN002846_SCENARIO = {
    "label": "SYN002846_REVERSE_SELF_CURE",
    "cif": "SYN002846",
    "changes": {"inflow_7d": 0, "net_cashflow_30d": 0},
    "description": "Giảm dòng tiền → khách hàng không còn đáp ứng điều kiện chờ tự thanh toán",
}

ALL_SCENARIOS = (HERO_SCENARIO_A, HERO_SCENARIO_B, HERO_SCENARIO_C, SYN002846_SCENARIO)


def run_scenario(engine: SimulationEngine, scenario: dict[str, Any]) -> SimulationResult:
    return engine.simulate(scenario["cif"], scenario["changes"])
