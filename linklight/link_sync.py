"""Wraps aalink.Link with beat reading and BPM-change song detection."""

from __future__ import annotations

import time
from dataclasses import dataclass

from aalink import Link

from config import INITIAL_BPM, SONG_CHANGE_COOLDOWN_S


@dataclass
class BeatInfo:
    beat: float
    tempo: float
    phase: float
    num_peers: int
    playing: bool


class LinkSync:
    def __init__(self):
        self._link = Link(INITIAL_BPM)
        self._link.enabled = True
        self._link.start_stop_sync_enabled = True
        self._link.quantum = 4

        # Song-change detection state
        self._last_tempo: float | None = None
        self._armed = True
        self._song_changed_flag = False
        self._cooldown_deadline: float | None = None

        self._link.set_tempo_callback(self._on_tempo)

    # -- public API ------------------------------------------------------

    def read(self) -> BeatInfo:
        return BeatInfo(
            beat=self._link.beat,
            tempo=self._link.tempo,
            phase=self._link.phase,
            num_peers=self._link.num_peers,
            playing=self._link.playing,
        )

    async def sync(self, quantum: float = 1.0) -> BeatInfo:
        beat = await self._link.sync(quantum)
        return BeatInfo(
            beat=beat,
            tempo=self._link.tempo,
            phase=self._link.phase,
            num_peers=self._link.num_peers,
            playing=self._link.playing,
        )

    def poll_song_changed(self) -> bool:
        """Return True (once) when a song change has been detected.

        Also manages the cooldown timer: re-arms detection once the
        cooldown expires without further BPM changes.
        """
        now = time.monotonic()

        if self._cooldown_deadline is not None and now >= self._cooldown_deadline:
            self._cooldown_deadline = None
            self._armed = True

        if self._song_changed_flag:
            self._song_changed_flag = False
            return True
        return False

    # -- internal --------------------------------------------------------

    def _on_tempo(self, tempo: float):
        """Called from aalink's tempo-change callback (may be on any thread)."""
        if self._last_tempo is not None and tempo != self._last_tempo:
            if self._armed:
                self._song_changed_flag = True
                self._armed = False
            self._cooldown_deadline = time.monotonic() + SONG_CHANGE_COOLDOWN_S
        self._last_tempo = tempo
