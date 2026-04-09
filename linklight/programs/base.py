from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from fixture import Color, MovingHead, SOLID_COLORS, StrobeLight


@dataclass
class ProgramOptions:
    theme_color: Color | None = None  # None = pick randomly at instantiation


class ShowProgram(ABC):
    name: str = "Unnamed"
    loop_beats: int = 32

    def __init__(self, options: ProgramOptions | None = None):
        self.options = options or ProgramOptions()
        if self.options.theme_color is None:
            self.options.theme_color = random.choice(SOLID_COLORS)

    @abstractmethod
    def update(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Called ~30x/sec.  *beat* is 0 .. loop_beats (fractional, continuous)."""
        ...

    def on_start(self):
        pass

    def on_stop(self):
        pass
