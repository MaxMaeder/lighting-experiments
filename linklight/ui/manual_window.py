"""Pop-out manual control window for pan/tilt exploration and limit-finding."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import PAN_MIN, PAN_MAX, TILT_MIN, TILT_MAX
from fixture import (
    COLOR_NAMES,
    GOBO_NAMES,
    Color,
    Gobo,
    MovingHead,
)
from show_engine import ShowEngine


STEP_ABS = 5
STEP_REL = 0.05


class ManualWindow(QWidget):
    def __init__(self, head: MovingHead, engine: ShowEngine):
        super().__init__()
        self._head = head
        self._engine = engine
        self._relative_mode = False

        self.setWindowTitle("Manual Control")
        self.resize(420, 480)
        self.setStyleSheet("background-color: #1a1a1a; color: #dddddd;")

        mono = QFont("monospace", 12)
        mono_bold = QFont("monospace", 12, QFont.Weight.Bold)

        root = QVBoxLayout(self)

        # -- mode toggle -------------------------------------------------
        mode_row = QHBoxLayout()
        self._mode_btn = QPushButton("Mode: Absolute (0-255)")
        self._mode_btn.setFont(mono)
        self._mode_btn.setCheckable(True)
        self._mode_btn.clicked.connect(self._toggle_mode)
        mode_row.addWidget(self._mode_btn)
        root.addLayout(mode_row)

        root.addSpacing(8)

        # -- pan / tilt controls -----------------------------------------
        grid = QGridLayout()
        grid.setSpacing(6)

        grid.addWidget(self._header("Pan"), 0, 0, 1, 4)
        self._pan_label = QLabel("0")
        self._pan_label.setFont(mono_bold)
        self._pan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self._pan_label, 1, 0)

        pan_minus = QPushButton("-")
        pan_minus.setFont(mono_bold)
        pan_minus.setAutoRepeat(True)
        pan_minus.setAutoRepeatInterval(80)
        pan_minus.clicked.connect(lambda: self._step_pan(-1))
        grid.addWidget(pan_minus, 1, 1)

        pan_plus = QPushButton("+")
        pan_plus.setFont(mono_bold)
        pan_plus.setAutoRepeat(True)
        pan_plus.setAutoRepeatInterval(80)
        pan_plus.clicked.connect(lambda: self._step_pan(1))
        grid.addWidget(pan_plus, 1, 2)

        self._pan_abs_label = QLabel("abs: 0")
        self._pan_abs_label.setFont(mono)
        self._pan_abs_label.setStyleSheet("color: #888888;")
        grid.addWidget(self._pan_abs_label, 1, 3)

        grid.addWidget(self._header("Tilt"), 2, 0, 1, 4)
        self._tilt_label = QLabel("0")
        self._tilt_label.setFont(mono_bold)
        self._tilt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self._tilt_label, 3, 0)

        tilt_minus = QPushButton("-")
        tilt_minus.setFont(mono_bold)
        tilt_minus.setAutoRepeat(True)
        tilt_minus.setAutoRepeatInterval(80)
        tilt_minus.clicked.connect(lambda: self._step_tilt(-1))
        grid.addWidget(tilt_minus, 3, 1)

        tilt_plus = QPushButton("+")
        tilt_plus.setFont(mono_bold)
        tilt_plus.setAutoRepeat(True)
        tilt_plus.setAutoRepeatInterval(80)
        tilt_plus.clicked.connect(lambda: self._step_tilt(1))
        grid.addWidget(tilt_plus, 3, 2)

        self._tilt_abs_label = QLabel("abs: 0")
        self._tilt_abs_label.setFont(mono)
        self._tilt_abs_label.setStyleSheet("color: #888888;")
        grid.addWidget(self._tilt_abs_label, 3, 3)

        root.addLayout(grid)
        root.addSpacing(12)

        # -- lamp toggle -------------------------------------------------
        self._lamp_btn = QPushButton("Lamp: OFF")
        self._lamp_btn.setFont(mono)
        self._lamp_btn.setCheckable(True)
        self._lamp_btn.clicked.connect(self._toggle_lamp)
        root.addWidget(self._lamp_btn)

        # -- dimmer slider -----------------------------------------------
        dim_row = QHBoxLayout()
        dim_row.addWidget(QLabel("Dimmer:"))
        self._dimmer_slider = QSlider(Qt.Orientation.Horizontal)
        self._dimmer_slider.setRange(0, 255)
        self._dimmer_slider.setValue(255)
        self._dimmer_slider.valueChanged.connect(self._set_dimmer)
        dim_row.addWidget(self._dimmer_slider, stretch=1)
        self._dimmer_val = QLabel("255")
        self._dimmer_val.setFont(mono)
        self._dimmer_val.setMinimumWidth(36)
        dim_row.addWidget(self._dimmer_val)
        root.addLayout(dim_row)

        # -- color dropdown -----------------------------------------------
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self._color_combo = QComboBox()
        for color, name in COLOR_NAMES.items():
            self._color_combo.addItem(name, int(color))
        self._color_combo.currentIndexChanged.connect(self._set_color)
        color_row.addWidget(self._color_combo, stretch=1)
        root.addLayout(color_row)

        # -- gobo dropdown ------------------------------------------------
        gobo_row = QHBoxLayout()
        gobo_row.addWidget(QLabel("Gobo:"))
        self._gobo_combo = QComboBox()
        for gobo, name in GOBO_NAMES.items():
            self._gobo_combo.addItem(name, int(gobo))
        self._gobo_combo.currentIndexChanged.connect(self._set_gobo)
        gobo_row.addWidget(self._gobo_combo, stretch=1)
        root.addLayout(gobo_row)

        root.addStretch()

        # -- resume button ------------------------------------------------
        resume = QPushButton("Resume Show")
        resume.setFont(QFont("monospace", 13, QFont.Weight.Bold))
        resume.setMinimumHeight(40)
        resume.clicked.connect(self.close)
        root.addWidget(resume)

        # Periodic readout refresh
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_readouts)
        self._timer.start(100)

    # -- lifecycle -------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._engine.manual_override = True
        self._head.lamp_on()
        self._head.dimmer = 255
        self._lamp_btn.setChecked(True)
        self._lamp_btn.setText("Lamp: ON")
        self._refresh_readouts()

    def closeEvent(self, event):
        self._engine.manual_override = False
        super().closeEvent(event)

    # -- helpers ---------------------------------------------------------

    def _header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("monospace", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #aaaaaa;")
        return lbl

    def _toggle_mode(self):
        self._relative_mode = self._mode_btn.isChecked()
        if self._relative_mode:
            self._mode_btn.setText("Mode: Relative (0.0-1.0)")
        else:
            self._mode_btn.setText("Mode: Absolute (0-255)")
        self._refresh_readouts()

    # -- pan/tilt stepping -----------------------------------------------

    def _step_pan(self, direction: int):
        if self._relative_mode:
            current_rel = (self._head.pan - PAN_MIN) / max(1, PAN_MAX - PAN_MIN)
            new_rel = max(0.0, min(1.0, current_rel + direction * STEP_REL))
            self._head.set_pan_relative(new_rel)
        else:
            self._head.pan = self._head.pan + direction * STEP_ABS
        self._refresh_readouts()

    def _step_tilt(self, direction: int):
        if self._relative_mode:
            current_rel = (self._head.tilt - TILT_MIN) / max(1, TILT_MAX - TILT_MIN)
            new_rel = max(0.0, min(1.0, current_rel + direction * STEP_REL))
            self._head.set_tilt_relative(new_rel)
        else:
            self._head.tilt = self._head.tilt + direction * STEP_ABS
        self._refresh_readouts()

    # -- other controls --------------------------------------------------

    def _toggle_lamp(self):
        if self._lamp_btn.isChecked():
            self._head.lamp_on()
            self._lamp_btn.setText("Lamp: ON")
        else:
            self._head.lamp_off()
            self._lamp_btn.setText("Lamp: OFF")

    def _set_dimmer(self, val: int):
        self._head.dimmer = val
        self._dimmer_val.setText(str(val))

    def _set_color(self):
        data = self._color_combo.currentData()
        if data is not None:
            self._head.color = data

    def _set_gobo(self):
        data = self._gobo_combo.currentData()
        if data is not None:
            self._head.gobo = data

    # -- readout refresh -------------------------------------------------

    def _refresh_readouts(self):
        pan_abs = self._head.pan
        tilt_abs = self._head.tilt

        if self._relative_mode:
            pan_rel = (pan_abs - PAN_MIN) / max(1, PAN_MAX - PAN_MIN)
            tilt_rel = (tilt_abs - TILT_MIN) / max(1, TILT_MAX - TILT_MIN)
            self._pan_label.setText(f"{pan_rel:.2f}")
            self._tilt_label.setText(f"{tilt_rel:.2f}")
        else:
            self._pan_label.setText(str(pan_abs))
            self._tilt_label.setText(str(tilt_abs))

        self._pan_abs_label.setText(f"abs: {pan_abs}")
        self._tilt_abs_label.setText(f"abs: {tilt_abs}")
