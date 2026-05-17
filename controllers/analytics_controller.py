"""Analytics controller for view-friendly summaries."""

from __future__ import annotations

from typing import Any

from services.analytics_service import AnalyticsService


class AnalyticsController:
    """Coordinates analytics generation for UI screens and exports."""

    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self.analytics_service = analytics_service or AnalyticsService()

    def build_summary(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        bundle = self.analytics_service.build_bundle(snapshot)
        return {
            "win_probability": bundle.win_probability,
            "over_summary": bundle.over_summary.to_dict(orient="records"),
            "innings_summary": bundle.innings_summary.to_dict(orient="records"),
            "total_balls": len(bundle.ball_frame.index),
        }
