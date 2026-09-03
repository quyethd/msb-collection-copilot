from __future__ import annotations

from dataclasses import dataclass

AUTHORIZED_CONTACT_WINDOWS = ("08-10", "10-12", "13-15", "15-17", "17-19")


@dataclass(frozen=True)
class NBAConfig:
    broken_ptp_recent_inflow_threshold_vnd: int = 5_000_000
    self_cure_max_dpd: int = 14
    self_cure_min_inflow_7d_vnd: int = 15_000_000
    best_contact_lookback_days: int = 30
    best_contact_fallback_window: str = "10-12"
    authorized_contact_windows: tuple[str, ...] = AUTHORIZED_CONTACT_WINDOWS

    def __post_init__(self) -> None:
        if self.best_contact_lookback_days < 1:
            raise ValueError("best_contact_lookback_days must be positive")
        if self.best_contact_fallback_window not in self.authorized_contact_windows:
            raise ValueError("fallback must be an authorized window")
        if tuple(self.authorized_contact_windows) != AUTHORIZED_CONTACT_WINDOWS:
            raise ValueError("authorized contact windows are contract-fixed")


DEFAULT_CONFIG = NBAConfig()
