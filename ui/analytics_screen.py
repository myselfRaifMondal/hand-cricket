"""Analytics screen with embedded matplotlib charts."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

try:
    import matplotlib  # noqa: F401
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure

    _MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MATPLOTLIB_AVAILABLE = False


def _dark_style() -> dict[str, Any]:
    return {
        "axes.facecolor": "#0d1b2a",
        "figure.facecolor": "#07111f",
        "axes.edgecolor": "#334155",
        "axes.labelcolor": "#cbd5e1",
        "xtick.color": "#94a3b8",
        "ytick.color": "#94a3b8",
        "text.color": "#e2e8f0",
        "grid.color": "#1e293b",
        "grid.linestyle": "--",
        "grid.alpha": 0.5,
    }


class _ChartCanvas(QWidget):
    """Wraps a matplotlib figure in a Qt widget with a dark frame."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        box = QGroupBox(title)
        box.setObjectName("analyticsChart")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 8, 8, 8)

        if _MATPLOTLIB_AVAILABLE:
            with plt.rc_context(_dark_style()):
                self._fig = Figure(figsize=(5, 2.8), dpi=96, tight_layout=True)
                self._ax = self._fig.add_subplot(111)
            self._canvas = FigureCanvasQTAgg(self._fig)
            self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            inner.addWidget(self._canvas)
        else:
            inner.addWidget(QLabel("matplotlib not installed — pip install matplotlib"))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(box)

    def ax(self):  # noqa: ANN201
        return getattr(self, "_ax", None)

    def redraw(self) -> None:
        if _MATPLOTLIB_AVAILABLE:
            self._canvas.draw_idle()


class AnalyticsScreen(QWidget):
    """Analytics view with worm graph, Manhattan chart, run-rate line, and win probability."""

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        title = QLabel("Analytics Workspace")
        title.setObjectName("screenTitle")
        root.addWidget(title)

        self._win_label = QLabel("Win probability: —")
        self._win_label.setObjectName("screenSubtitle")
        root.addWidget(self._win_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("analyticsScroll")
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(16)

        self._worm = _ChartCanvas("Worm Graph — Cumulative Runs")
        self._manhattan = _ChartCanvas("Manhattan Chart — Runs per Over")
        self._run_rate = _ChartCanvas("Run Rate per Over")

        grid.addWidget(self._worm, 0, 0)
        grid.addWidget(self._manhattan, 0, 1)
        grid.addWidget(self._run_rate, 1, 0, 1, 2)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def update_charts(self, chart_data: dict[str, Any]) -> None:
        """Refresh all charts from the *chart_data* dict produced by AnalyticsController."""

        self._win_label.setText(f"Win probability: {chart_data.get('win_probability', 0):.1f}%")
        self._draw_worm(chart_data.get("worm_data", []))
        self._draw_manhattan(chart_data.get("manhattan_data", []))
        self._draw_run_rate(chart_data.get("run_rate_data", []))

    # ------------------------------------------------------------------
    # Private chart renderers
    # ------------------------------------------------------------------

    def _draw_worm(self, worm_data: list[dict[str, Any]]) -> None:
        ax = self._worm.ax()
        if ax is None or not worm_data:
            return
        ax.clear()
        ax.set_xlabel("Ball")
        ax.set_ylabel("Cumulative Runs")
        ax.set_title("Worm", color="#e2e8f0", fontsize=9)
        ax.grid(True)

        innings_map: dict[int, tuple[list[int], list[int]]] = {}
        for row in worm_data:
            num = int(row["innings_number"])
            if num not in innings_map:
                innings_map[num] = ([], [])
            innings_map[num][0].append(int(row["ball_index"]))
            innings_map[num][1].append(int(row["cumulative_runs"]))

        colors = ["#38bdf8", "#f97316", "#a3e635", "#e879f9"]
        for i, (innings_num, (balls, runs)) in enumerate(sorted(innings_map.items())):
            color = colors[i % len(colors)]
            ax.plot(balls, runs, marker=".", linewidth=1.5, color=color, label=f"Innings {innings_num}")
        if len(innings_map) > 1:
            ax.legend(fontsize=7)
        self._worm.redraw()

    def _draw_manhattan(self, manhattan_data: list[dict[str, Any]]) -> None:
        ax = self._manhattan.ax()
        if ax is None or not manhattan_data:
            return
        ax.clear()
        ax.set_xlabel("Over")
        ax.set_ylabel("Runs")
        ax.set_title("Runs per Over", color="#e2e8f0", fontsize=9)
        ax.grid(True, axis="y")

        labels = [str(row["over_label"]) for row in manhattan_data]
        runs = [int(row["runs"]) for row in manhattan_data]
        wickets = [int(row["wickets"]) for row in manhattan_data]
        x = range(len(labels))
        ax.bar(x, runs, color="#38bdf8", alpha=0.85, label="Runs")
        for xi, w in zip(x, wickets):
            if w:
                ax.text(xi, runs[xi] + 0.1, f"W×{w}", ha="center", va="bottom", fontsize=6, color="#f87171")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=7)
        self._manhattan.redraw()

    def _draw_run_rate(self, run_rate_data: list[dict[str, Any]]) -> None:
        ax = self._run_rate.ax()
        if ax is None or not run_rate_data:
            return
        ax.clear()
        ax.set_xlabel("Over")
        ax.set_ylabel("Run Rate")
        ax.set_title("Run Rate per Over", color="#e2e8f0", fontsize=9)
        ax.grid(True)

        labels = [str(row["over_label"]) for row in run_rate_data]
        rates = [float(row["run_rate"]) for row in run_rate_data]
        ax.plot(labels, rates, marker="o", linewidth=2, color="#f97316")
        ax.fill_between(labels, rates, alpha=0.15, color="#f97316")
        self._run_rate.redraw()

