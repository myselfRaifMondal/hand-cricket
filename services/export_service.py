"""Export helpers for match snapshots and analytics tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class ExportService:
    """Export match and analytics data to common interchange formats."""

    def export_match_json(self, snapshot: dict[str, Any], output_path: Path) -> Path:
        """Serialize a match snapshot to JSON."""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
        return output_path

    def export_statistics_csv(self, frame: pd.DataFrame, output_path: Path) -> Path:
        """Write an analytics DataFrame to CSV."""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output_path, index=False)
        return output_path
