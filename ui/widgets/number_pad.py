"""Number pad widget used for batting and bowling input."""

from __future__ import annotations

from functools import partial

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget


class NumberPad(QWidget):
    """Reusable 1-6 keypad for match input."""

    number_selected = Signal(int)

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self._buttons: dict[int, QPushButton] = {}
        self.selected_number: int | None = None
        layout = QGridLayout(self)
        layout.setSpacing(10)
        for index, value in enumerate(range(1, 7)):
            button = QPushButton(str(value))
            button.setCheckable(True)
            button.setObjectName(f"{prefix}PadButton")
            button.clicked.connect(partial(self._on_selected, value))
            layout.addWidget(button, index // 3, index % 3)
            self._buttons[value] = button

    def clear_selection(self) -> None:
        self.selected_number = None
        for button in self._buttons.values():
            button.setChecked(False)

    def _on_selected(self, value: int) -> None:
        self.selected_number = value
        for number, button in self._buttons.items():
            button.setChecked(number == value)
        self.number_selected.emit(value)
