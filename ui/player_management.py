"""Team and player management screen backed by SQLite via PlayerController."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from controllers.player_controller import PlayerController


class _AddPlayerDialog(QDialog):
    """Simple modal form for creating a new player."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Player")
        self.setMinimumWidth(320)

        form = QFormLayout()
        self.team_id_spin = QSpinBox()
        self.team_id_spin.setRange(1, 9999)
        self.name_edit = QLineEdit()
        self.jersey_spin = QSpinBox()
        self.jersey_spin.setRange(1, 999)
        self.role_edit = QLineEdit("all_rounder")

        form.addRow("Team ID", self.team_id_spin)
        form.addRow("Name", self.name_edit)
        form.addRow("Jersey #", self.jersey_spin)
        form.addRow("Role", self.role_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "team_id": self.team_id_spin.value(),
            "name": self.name_edit.text().strip(),
            "jersey_number": self.jersey_spin.value(),
            "role": self.role_edit.text().strip() or "all_rounder",
        }


class PlayerManagementScreen(QWidget):
    """Roster table connected to a live SQLite-backed PlayerController."""

    _HEADERS = ["ID", "Team ID", "Player", "Role", "Jersey", "Runs", "Wickets"]

    def __init__(self, player_controller: "PlayerController | None" = None) -> None:
        super().__init__()
        self._controller = player_controller
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("Team And Player Management")
        title.setObjectName("screenTitle")

        subtitle = QLabel("Roster is loaded from the live SQLite database.")
        subtitle.setObjectName("screenSubtitle")

        self.table = QTableWidget(0, len(self._HEADERS))
        self.table.setHorizontalHeaderLabels(self._HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add Player")
        self._delete_btn = QPushButton("Delete Selected")
        self._refresh_btn = QPushButton("Refresh")
        self._add_btn.clicked.connect(self._on_add)
        self._delete_btn.clicked.connect(self._on_delete)
        self._refresh_btn.clicked.connect(self.refresh)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._refresh_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(btn_row)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        """Reload the roster from the database."""

        self.table.setRowCount(0)
        if self._controller is None:
            return
        try:
            players = self._controller.list_players()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Database error", str(exc))
            return

        self.table.setRowCount(len(players))
        for row, player in enumerate(players):
            self.table.setItem(row, 0, QTableWidgetItem(str(player["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(player["team_id"])))
            self.table.setItem(row, 2, QTableWidgetItem(player["name"]))
            self.table.setItem(row, 3, QTableWidgetItem(player["role"]))
            self.table.setItem(row, 4, QTableWidgetItem(str(player["jersey_number"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(player["batting_runs"])))
            self.table.setItem(row, 6, QTableWidgetItem(str(player["wickets_taken"])))

    def _on_add(self) -> None:
        if self._controller is None:
            QMessageBox.warning(self, "Not connected", "Player controller not available.")
            return
        dialog = _AddPlayerDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if not values["name"]:
            QMessageBox.warning(self, "Validation", "Player name cannot be empty.")
            return
        try:
            from utils.constants import PlayerRole  # noqa: PLC0415
            role = PlayerRole(values["role"])
            self._controller.create_player(
                team_id=values["team_id"],
                name=values["name"],
                jersey_number=values["jersey_number"],
                role=role,
            )
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))

    def _on_delete(self) -> None:
        if self._controller is None:
            QMessageBox.warning(self, "Not connected", "Player controller not available.")
            return
        selected = self.table.selectedItems()
        if not selected:
            return
        row = self.table.currentRow()
        player_id_item = self.table.item(row, 0)
        if player_id_item is None:
            return
        player_id = int(player_id_item.text())
        confirm = QMessageBox.question(
            self,
            "Confirm delete",
            f"Delete player ID {player_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self._controller.delete_player(player_id)
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))

