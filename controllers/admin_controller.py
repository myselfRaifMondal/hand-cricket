"""Administrative workflows for creating or reconfiguring matches."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from controllers.match_controller import MatchController
from services.match_engine import MatchConfig, TeamConfig


class AdminController(QObject):
    """Creates matches from admin-supplied configuration."""

    match_created = Signal(dict)
    error_changed = Signal(str)

    def __init__(self, match_controller: MatchController) -> None:
        super().__init__()
        self.match_controller = match_controller

    def create_match(
        self,
        home_team_name: str,
        away_team_name: str,
        overs: int,
        innings_count: int,
        max_wickets: int,
        batting_first_team_id: int = 1,
        bowling_first_team_id: int = 2,
    ) -> None:
        try:
            # Use temporary team_ids 1/2 for the in-memory engine; DB mapping is
            # handled inside ScoringService using team names.
            state = self.match_controller.service.create_match(
                MatchConfig(
                    home_team=TeamConfig(team_id=1, name=home_team_name),
                    away_team=TeamConfig(team_id=2, name=away_team_name),
                    batting_first_team_id=batting_first_team_id,
                    bowling_first_team_id=bowling_first_team_id,
                    overs=overs,
                    innings_count=innings_count,
                    max_wickets=max_wickets,
                )
            )
            self.match_controller.team_name_by_id = {1: home_team_name, 2: away_team_name}
            snapshot = self.match_controller.service.engine.get_snapshot(state)
            self.match_controller.state_changed.emit(self.match_controller._decorate_snapshot(snapshot))
            self.match_created.emit(snapshot)
        except ValueError as error:
            self.error_changed.emit(str(error))
