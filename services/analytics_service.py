"""Analytics helpers for transforming ball history into dashboard-friendly datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from utils.constants import BALLS_PER_OVER


@dataclass(slots=True)
class AnalyticsBundle:
    """Aggregated analytics output for a single match snapshot."""

    ball_frame: pd.DataFrame
    over_summary: pd.DataFrame
    innings_summary: pd.DataFrame
    win_probability: float
    worm_data: pd.DataFrame
    manhattan_data: pd.DataFrame
    run_rate_data: pd.DataFrame


class AnalyticsService:
    """Generates analytics tables from live or completed match snapshots."""

    def ball_history_frame(self, snapshot: dict[str, Any]) -> pd.DataFrame:
        """Convert ball history into a typed DataFrame."""

        history = snapshot.get("history", [])
        if not history:
            return pd.DataFrame(
                columns=[
                    "innings_number",
                    "sequence_number",
                    "batting_input",
                    "bowling_input",
                    "runs_scored",
                    "is_wicket",
                    "total_score_after",
                    "wickets_after",
                    "over_notation",
                ]
            )
        frame = pd.DataFrame(history)
        frame["is_wicket"] = frame["is_wicket"].astype(bool)
        frame["runs_scored"] = frame["runs_scored"].astype(int)
        frame["over_number"] = frame["sequence_number"].sub(1).floordiv(BALLS_PER_OVER)
        return frame

    def over_by_over_summary(self, ball_frame: pd.DataFrame) -> pd.DataFrame:
        """Summarize runs and wickets per over."""

        if ball_frame.empty:
            return pd.DataFrame(columns=["over_number", "runs", "wickets", "run_rate"])
        grouped = (
            ball_frame.groupby("over_number", as_index=False)
            .agg(runs=("runs_scored", "sum"), wickets=("is_wicket", "sum"), balls=("sequence_number", "count"))
        )
        grouped["run_rate"] = grouped["runs"] / grouped["balls"] * BALLS_PER_OVER
        return grouped[["over_number", "runs", "wickets", "run_rate"]]

    def innings_summary(self, snapshot: dict[str, Any], ball_frame: pd.DataFrame) -> pd.DataFrame:
        """Build a simple innings summary table."""

        if ball_frame.empty:
            return pd.DataFrame(
                [{
                    "batting_team": snapshot.get("batting_team_name", "Unknown"),
                    "score": snapshot.get("score", 0),
                    "wickets": snapshot.get("wickets", 0),
                    "overs": snapshot.get("overs", "0.0"),
                    "current_run_rate": snapshot.get("current_run_rate", 0.0),
                }]
            )
        return pd.DataFrame(
            [{
                "batting_team": snapshot.get("batting_team_name", "Unknown"),
                "score": int(ball_frame["runs_scored"].sum()),
                "wickets": int(ball_frame["is_wicket"].sum()),
                "overs": snapshot.get("overs", "0.0"),
                "current_run_rate": snapshot.get("current_run_rate", 0.0),
            }]
        )

    def estimate_win_probability(self, snapshot: dict[str, Any]) -> float:
        """Estimate win probability with a simple chase-pressure heuristic."""

        target = int(snapshot.get("target") or 0)
        if target <= 0:
            return 50.0
        score = int(snapshot.get("score") or 0)
        wickets = int(snapshot.get("wickets") or 0)
        balls_remaining = int(snapshot.get("balls_remaining") or 0)
        required = max(target - score, 0)
        if required == 0:
            return 100.0
        pressure = 0.0 if balls_remaining == 0 else required / max(balls_remaining, 1)
        wicket_penalty = wickets * 6.5
        probability = 100.0 - (pressure * 12.0 + wicket_penalty)
        return max(0.0, min(100.0, round(probability, 2)))

    # ------------------------------------------------------------------
    # Chart-ready dataset builders
    # ------------------------------------------------------------------

    def worm_data(self, ball_frame: pd.DataFrame) -> pd.DataFrame:
        """Cumulative score per ball, grouped by innings number.

        Returns columns: innings_number, ball_index, cumulative_runs.
        Suitable for a multi-series line chart (worm graph).
        """

        if ball_frame.empty:
            return pd.DataFrame(columns=["innings_number", "ball_index", "cumulative_runs"])

        frames: list[pd.DataFrame] = []
        for innings_num, group in ball_frame.groupby("innings_number", sort=True):
            group = group.sort_values("sequence_number").reset_index(drop=True)
            group = group.copy()
            group["ball_index"] = group.index + 1
            group["cumulative_runs"] = group["runs_scored"].cumsum()
            frames.append(group[["innings_number", "ball_index", "cumulative_runs"]])
        return pd.concat(frames, ignore_index=True)

    def manhattan_data(self, over_summary: pd.DataFrame) -> pd.DataFrame:
        """Runs and wickets per over, ready for a bar/column chart.

        Returns columns: over_label, runs, wickets.
        """

        if over_summary.empty:
            return pd.DataFrame(columns=["over_label", "runs", "wickets"])
        result = over_summary[["over_number", "runs", "wickets"]].copy()
        result["over_label"] = (result["over_number"] + 1).astype(str)
        return result[["over_label", "runs", "wickets"]]

    def run_rate_data(self, over_summary: pd.DataFrame) -> pd.DataFrame:
        """Run rate per over for a line chart overlay.

        Returns columns: over_label, run_rate.
        """

        if over_summary.empty:
            return pd.DataFrame(columns=["over_label", "run_rate"])
        result = over_summary[["over_number", "run_rate"]].copy()
        result["over_label"] = (result["over_number"] + 1).astype(str)
        return result[["over_label", "run_rate"]]

    def build_bundle(self, snapshot: dict[str, Any]) -> AnalyticsBundle:
        """Return the full analytics bundle for a snapshot."""

        ball_frame = self.ball_history_frame(snapshot)
        over_summary = self.over_by_over_summary(ball_frame)
        innings_summary = self.innings_summary(snapshot, ball_frame)
        win_probability = self.estimate_win_probability(snapshot)
        worm = self.worm_data(ball_frame)
        manhattan = self.manhattan_data(over_summary)
        run_rate = self.run_rate_data(over_summary)
        return AnalyticsBundle(
            ball_frame=ball_frame,
            over_summary=over_summary,
            innings_summary=innings_summary,
            win_probability=win_probability,
            worm_data=worm,
            manhattan_data=manhattan,
            run_rate_data=run_rate,
        )
