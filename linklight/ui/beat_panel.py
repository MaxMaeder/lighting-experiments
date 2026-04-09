"""Left column: beat flash indicator + BPM / phase / peers readout."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from link_sync import BeatInfo

DARK = "#111111"
FLASH_COLOR = "#ffffff"
FLASH_DURATION_MS = 80


class BeatPanel(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._set_bg(DARK)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.beat_label = QLabel("--")
        self.beat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.beat_label.setFont(QFont("monospace", 72, QFont.Weight.Bold))
        self.beat_label.setStyleSheet("color: #888888;")

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFont(QFont("monospace", 16))
        self.info_label.setStyleSheet("color: #666666;")

        layout.addWidget(self.beat_label)
        layout.addWidget(self.info_label)

        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._end_flash)

        self._last_beat_int: int | None = None

    def update_display(self, info: BeatInfo):
        beat_int = int(info.beat)
        self.beat_label.setText(str(beat_int))
        self.info_label.setText(
            f"{info.tempo:.1f} BPM  |  phase {info.phase:.2f}  |  "
            f"{info.num_peers} peer(s)  |  {'playing' if info.playing else 'stopped'}"
        )

        if self._last_beat_int is None or beat_int != self._last_beat_int:
            self._flash()
            self._last_beat_int = beat_int

    def _flash(self):
        self.beat_label.setStyleSheet("color: #ffffff;")
        self.info_label.setStyleSheet("color: #cccccc;")
        self._set_bg(FLASH_COLOR)
        self._flash_timer.start(FLASH_DURATION_MS)

    def _end_flash(self):
        self._set_bg(DARK)
        self.beat_label.setStyleSheet("color: #888888;")
        self.info_label.setStyleSheet("color: #666666;")

    def _set_bg(self, color: str):
        self.setStyleSheet(f"BeatPanel {{ background-color: {color}; }}")
