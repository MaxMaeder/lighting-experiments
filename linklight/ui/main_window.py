"""Main window: two-column layout combining BeatPanel and QueuePanel."""

from fixture import MovingHead, ParGroup, StrobeLight
from show_engine import ShowEngine
from ui.beat_panel import BeatPanel
from ui.manual_window import ManualWindow
from ui.queue_panel import QueuePanel

from PyQt6.QtWidgets import QHBoxLayout, QWidget


class MainWindow(QWidget):
    def __init__(self, engine: ShowEngine):
        super().__init__()
        self._engine = engine
        self._manual_window: ManualWindow | None = None
        self._head: MovingHead | None = None

        self.setWindowTitle("LinkLight")
        self.resize(900, 520)
        self.setStyleSheet("background-color: #111111; color: #dddddd;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.beat_panel = BeatPanel(self)
        self.queue_panel = QueuePanel(engine, self)

        layout.addWidget(self.beat_panel, stretch=1)
        layout.addWidget(self.queue_panel, stretch=1)

        self.queue_panel.manual_btn.clicked.connect(self._open_manual)

    def set_head(self, head: MovingHead):
        """Called from main.py once the head is created inside the async loop."""
        self._head = head
        self.queue_panel.set_head(head)

    def set_strobe(self, strobe: StrobeLight):
        """Called from main.py once the strobe is created inside the async loop."""
        self.queue_panel.set_strobe(strobe)

    def set_pars(self, pars: ParGroup):
        """Called from main.py once the par group is created inside the async loop."""
        self.queue_panel.set_pars(pars)

    def _open_manual(self):
        if self._head is None:
            return
        if self._manual_window is None or not self._manual_window.isVisible():
            self._manual_window = ManualWindow(self._head, self._engine)
        self._manual_window.show()
        self._manual_window.raise_()
        self._manual_window.activateWindow()
