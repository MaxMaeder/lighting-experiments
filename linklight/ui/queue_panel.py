"""Right column: program queue, add controls, house-lights toggle, manual control."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import DEFAULT_HEAD_BRIGHTNESS, DEFAULT_PAR_BRIGHTNESS, DEFAULT_STROBE_BRIGHTNESS
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from fixture import Color, COLOR_NAMES, MovingHead, ParGroup, StrobeLight
from programs import PROGRAM_REGISTRY
from programs.base import ProgramOptions
from show_engine import ShowEngine


class QueuePanel(QWidget):
    def __init__(self, engine: ShowEngine, parent: QWidget | None = None):
        super().__init__(parent)
        self._engine = engine
        self._strobe: StrobeLight | None = None
        self._head: MovingHead | None = None
        self._pars: ParGroup | None = None
        engine.on_queue_changed.append(self._refresh_queue)
        engine.on_program_changed.append(self._refresh_now_playing)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # -- House lights button -----------------------------------------
        self._house_btn = QPushButton("House Lights: OFF")
        self._house_btn.setCheckable(True)
        self._house_btn.setFont(QFont("monospace", 14, QFont.Weight.Bold))
        self._house_btn.setMinimumHeight(48)
        self._house_btn.clicked.connect(self._toggle_house)
        layout.addWidget(self._house_btn)

        layout.addSpacing(8)

        # -- Strobe brightness slider ------------------------------------
        strobe_row = QHBoxLayout()
        strobe_label = QLabel("Strobe Brightness:")
        strobe_label.setFont(QFont("monospace", 11))
        strobe_label.setStyleSheet("color: #cccccc;")
        strobe_row.addWidget(strobe_label)

        self._strobe_slider = QSlider(Qt.Orientation.Horizontal)
        self._strobe_slider.setRange(0, 100)
        self._strobe_slider.setValue(DEFAULT_STROBE_BRIGHTNESS)
        self._strobe_slider.valueChanged.connect(self._set_strobe_brightness)
        strobe_row.addWidget(self._strobe_slider, stretch=1)

        self._strobe_val = QLabel(f"{DEFAULT_STROBE_BRIGHTNESS}%")
        self._strobe_val.setFont(QFont("monospace", 11))
        self._strobe_val.setMinimumWidth(44)
        strobe_row.addWidget(self._strobe_val)

        layout.addLayout(strobe_row)

        # -- Mover brightness slider -------------------------------------
        mover_row = QHBoxLayout()
        mover_label = QLabel("Mover Brightness:")
        mover_label.setFont(QFont("monospace", 11))
        mover_label.setStyleSheet("color: #cccccc;")
        mover_row.addWidget(mover_label)

        self._mover_slider = QSlider(Qt.Orientation.Horizontal)
        self._mover_slider.setRange(0, 100)
        self._mover_slider.setValue(DEFAULT_HEAD_BRIGHTNESS)
        self._mover_slider.valueChanged.connect(self._set_mover_brightness)
        mover_row.addWidget(self._mover_slider, stretch=1)

        self._mover_val = QLabel(f"{DEFAULT_HEAD_BRIGHTNESS}%")
        self._mover_val.setFont(QFont("monospace", 11))
        self._mover_val.setMinimumWidth(44)
        mover_row.addWidget(self._mover_val)

        layout.addLayout(mover_row)

        # -- Par brightness slider ------------------------------------------
        par_row = QHBoxLayout()
        par_label = QLabel("Par Brightness:")
        par_label.setFont(QFont("monospace", 11))
        par_label.setStyleSheet("color: #cccccc;")
        par_row.addWidget(par_label)

        self._par_slider = QSlider(Qt.Orientation.Horizontal)
        self._par_slider.setRange(0, 100)
        self._par_slider.setValue(DEFAULT_PAR_BRIGHTNESS)
        self._par_slider.valueChanged.connect(self._set_par_brightness)
        par_row.addWidget(self._par_slider, stretch=1)

        self._par_val = QLabel(f"{DEFAULT_PAR_BRIGHTNESS}%")
        self._par_val.setFont(QFont("monospace", 11))
        self._par_val.setMinimumWidth(44)
        par_row.addWidget(self._par_val)

        layout.addLayout(par_row)

        layout.addSpacing(8)

        # -- Manual control button ----------------------------------------
        self._manual_btn = QPushButton("Manual Control")
        self._manual_btn.setFont(QFont("monospace", 12))
        self._manual_btn.setMinimumHeight(36)
        layout.addWidget(self._manual_btn)

        layout.addSpacing(12)

        # -- Now playing -------------------------------------------------
        self._now_label = QLabel("Now playing: (none)")
        self._now_label.setFont(QFont("monospace", 13))
        self._now_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self._now_label)

        layout.addSpacing(8)

        # -- Queue list --------------------------------------------------
        queue_header = QLabel("Queue")
        queue_header.setFont(QFont("monospace", 12, QFont.Weight.Bold))
        queue_header.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(queue_header)

        self._queue_list = QListWidget()
        self._queue_list.setFont(QFont("monospace", 12))
        layout.addWidget(self._queue_list, stretch=1)

        # -- Remove button -----------------------------------------------
        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.clicked.connect(self._remove_selected)
        layout.addWidget(self._remove_btn)

        layout.addSpacing(12)

        # -- Add to queue controls ---------------------------------------
        add_header = QLabel("Add to Queue")
        add_header.setFont(QFont("monospace", 12, QFont.Weight.Bold))
        add_header.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(add_header)

        add_row = QHBoxLayout()

        self._program_combo = QComboBox()
        for name in PROGRAM_REGISTRY:
            self._program_combo.addItem(name)
        add_row.addWidget(self._program_combo, stretch=1)

        color_label = QLabel("Color:")
        color_label.setStyleSheet("color: #cccccc;")
        add_row.addWidget(color_label)

        self._color_combo = QComboBox()
        self._color_combo.addItem("Random", None)
        for color, name in COLOR_NAMES.items():
            self._color_combo.addItem(name, color)
        add_row.addWidget(self._color_combo)

        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._add_to_queue)
        add_row.addWidget(self._add_btn)

        layout.addLayout(add_row)

        # -- Skip button --------------------------------------------------
        self._skip_btn = QPushButton("Skip / Next")
        self._skip_btn.clicked.connect(self._skip)
        layout.addWidget(self._skip_btn)

        self._refresh_queue()
        self._refresh_now_playing()

    # -- public -----------------------------------------------------------

    @property
    def manual_btn(self) -> QPushButton:
        return self._manual_btn

    def set_strobe(self, strobe: StrobeLight):
        """Store the strobe reference so the slider can control master_brightness."""
        self._strobe = strobe
        self._strobe.master_brightness = self._strobe_slider.value() / 100.0

    def set_head(self, head: MovingHead):
        """Store the head reference so the slider can control master_brightness."""
        self._head = head
        self._head.master_brightness = self._mover_slider.value() / 100.0

    def set_pars(self, pars: ParGroup):
        """Store the par group reference so the slider can control master_brightness."""
        self._pars = pars
        self._pars.master_brightness = self._par_slider.value() / 100.0

    # -- slots -----------------------------------------------------------

    def _toggle_house(self):
        on = self._house_btn.isChecked()
        self._house_btn.setText(f"House Lights: {'ON' if on else 'OFF'}")
        self._engine.set_house_lights(on)

    def _set_strobe_brightness(self, val: int):
        self._strobe_val.setText(f"{val}%")
        if self._strobe is not None:
            self._strobe.master_brightness = val / 100.0

    def _set_mover_brightness(self, val: int):
        self._mover_val.setText(f"{val}%")
        if self._head is not None:
            self._head.master_brightness = val / 100.0

    def _set_par_brightness(self, val: int):
        self._par_val.setText(f"{val}%")
        if self._pars is not None:
            self._pars.master_brightness = val / 100.0

    def _add_to_queue(self):
        name = self._program_combo.currentText()
        cls = PROGRAM_REGISTRY.get(name)
        if cls is None:
            return
        color_data = self._color_combo.currentData()
        opts = ProgramOptions(theme_color=color_data)
        self._engine.enqueue(cls, opts)

    def _remove_selected(self):
        row = self._queue_list.currentRow()
        if row >= 0:
            self._engine.remove_at(row)

    def _skip(self):
        self._engine.advance()

    # -- refresh helpers -------------------------------------------------

    def _refresh_queue(self):
        self._queue_list.clear()
        for cls, opts in self._engine.queue:
            if opts.theme_color is not None:
                color_str = COLOR_NAMES.get(opts.theme_color, str(opts.theme_color))
            else:
                color_str = "Random"
            self._queue_list.addItem(f"{cls.name}  ({color_str})")

    def _refresh_now_playing(self):
        self._now_label.setText(f"Now playing: {self._engine.active_program_name}")
