"""SQLite-backed player management controller."""

from __future__ import annotations

from typing import Any

from database.db import session_scope
from database.models import Player
from utils.constants import PlayerRole
from utils.helpers import AppSettings


class PlayerController:
    """CRUD controller for roster management."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def list_players(self) -> list[dict[str, Any]]:
        with session_scope(self.settings) as session:
            players = session.query(Player).order_by(Player.name.asc()).all()
            return [self._to_dict(player) for player in players]

    def create_player(self, team_id: int, name: str, jersey_number: int, role: PlayerRole) -> dict[str, Any]:
        with session_scope(self.settings) as session:
            player = Player(team_id=team_id, name=name, jersey_number=jersey_number, role=role)
            session.add(player)
            session.flush()
            return self._to_dict(player)

    def delete_player(self, player_id: int) -> None:
        with session_scope(self.settings) as session:
            player = session.get(Player, player_id)
            if player is None:
                raise ValueError(f"Player {player_id} not found.")
            session.delete(player)

    def _to_dict(self, player: Player) -> dict[str, Any]:
        return {
            "id": player.id,
            "team_id": player.team_id,
            "name": player.name,
            "jersey_number": player.jersey_number,
            "role": player.role.value,
            "batting_runs": player.batting_runs,
            "wickets_taken": player.wickets_taken,
            "total_matches": player.total_matches,
        }
