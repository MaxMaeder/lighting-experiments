"""Show engine: manages program queue, active program, house-lights override."""

from __future__ import annotations

import random

from fixture import MovingHead, StrobeLight
from programs import HOUSE_PROGRAM_CLASS, PROGRAM_REGISTRY
from programs.base import ProgramOptions, ShowProgram


class ShowEngine:
    def __init__(self):
        self.queue: list[tuple[type[ShowProgram], ProgramOptions]] = []
        self._active: ShowProgram | None = None
        self._active_is_default = False
        self._house_lights = HOUSE_PROGRAM_CLASS(ProgramOptions())
        self._house_active = False
        self.manual_override = False

        self.on_queue_changed: list[callable] = []
        self.on_program_changed: list[callable] = []

    # -- active program --------------------------------------------------

    @property
    def active_program(self) -> ShowProgram | None:
        if self._house_active:
            return self._house_lights
        return self._active

    @property
    def active_program_name(self) -> str:
        prog = self.active_program
        if prog is None:
            return "(none)"
        suffix = " (default)" if (not self._house_active and self._active_is_default) else ""
        return prog.name + suffix

    @property
    def house_active(self) -> bool:
        return self._house_active

    # -- queue management ------------------------------------------------

    def enqueue(self, program_cls: type[ShowProgram], options: ProgramOptions):
        self.queue.append((program_cls, options))
        self._notify_queue()

    def remove_at(self, index: int):
        if 0 <= index < len(self.queue):
            self.queue.pop(index)
            self._notify_queue()

    def advance(self):
        """Pop the next program from the queue and activate it.

        If the queue is empty, pick a random default from the registry.
        """
        if self._active:
            self._active.on_stop()

        if self.queue:
            cls, opts = self.queue.pop(0)
            self._active = cls(opts)
            self._active_is_default = False
            self._active.on_start()
        else:
            self._activate_default()

        self._notify_queue()
        self._notify_program()

    # -- default program -------------------------------------------------

    def _activate_default(self):
        pool = list(PROGRAM_REGISTRY.values())
        if not pool:
            self._active = None
            self._active_is_default = False
            return
        cls = random.choice(pool)
        self._active = cls(ProgramOptions())
        self._active_is_default = True
        self._active.on_start()

    # -- house lights ----------------------------------------------------

    def set_house_lights(self, on: bool, options: ProgramOptions | None = None):
        self._house_active = on
        if options is not None:
            self._house_lights = HOUSE_PROGRAM_CLASS(options)
        self._notify_program()

    # -- tick (called every frame) ---------------------------------------

    def tick(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        if self.manual_override:
            return
        prog = self.active_program
        if prog is None:
            return
        loop_beat = beat % prog.loop_beats
        prog.update(head, strobe, loop_beat, tempo)

    # -- notifications ---------------------------------------------------

    def _notify_queue(self):
        for cb in self.on_queue_changed:
            cb()

    def _notify_program(self):
        for cb in self.on_program_changed:
            cb()
