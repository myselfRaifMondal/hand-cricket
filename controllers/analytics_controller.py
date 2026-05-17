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

    def build_chart_data(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Return serializable chart datasets suitable for chart widgets.

        Keys
        ----
        worm_data
            List of ``{innings_number, ball_index, cumulative_runs}`` dicts.
        manhattan_data
            List of ``{over_label, runs, wickets}`` dicts.
        run_rate_data
            List of ``{over_label, run_rate}`` dicts.
        win_probability
            Float 0-100.
        """

        bundle = self.analytics_service.build_bundle(snapshot)
        return {
            "worm_data": bundle.worm_data.to_dict(orient="records"),
            "manhattan_data": bundle.manhattan_data.to_dict(orient="records"),
            "run_rate_data": bundle.run_rate_data.to_dict(orient="records"),
            "win_probability": bundle.win_probability,
            "total_balls": len(bundle.ball_frame.index),
        }
