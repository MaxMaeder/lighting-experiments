"""Stateless animation helpers and the Sequence class for multi-section choreography."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from fixture import MovingHead
    from fixture.par import ParGroup


# ---------------------------------------------------------------------------
# Interpolation
# ---------------------------------------------------------------------------

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


# ---------------------------------------------------------------------------
# Waveforms  (all take a continuous *beat* position)
# ---------------------------------------------------------------------------

def oscillate(beat: float, period_beats: float, low: float = 0.0, high: float = 1.0) -> float:
    """Sinusoidal oscillation: low..high over *period_beats*."""
    t = 0.5 * (1.0 + math.sin(2.0 * math.pi * beat / period_beats))
    return lerp(low, high, t)


def ramp(beat: float, start_beat: float, end_beat: float,
         start_val: float = 0.0, end_val: float = 1.0) -> float:
    """Linear ramp from start_val to end_val between start_beat..end_beat, clamped outside."""
    if beat <= start_beat:
        return start_val
    if beat >= end_beat:
        return end_val
    t = (beat - start_beat) / (end_beat - start_beat)
    return lerp(start_val, end_val, t)


def pulse(beat: float, beat_target: float, width: float = 0.15) -> float:
    """Returns ~1.0 when *beat* is near *beat_target*, tapering to 0.0 outside *width* beats."""
    dist = abs(beat - beat_target)
    if dist > width:
        return 0.0
    return 1.0 - (dist / width)


# ---------------------------------------------------------------------------
# Hardware smooth-pan helper
# ---------------------------------------------------------------------------

def smooth_pan(head: MovingHead, beat: float, glide_beats: float,
               starts: list[float], ends: list[float],
               speed: int | None = None):
    """Drive a pan cycle using the hardware speed channel.

    Lit window (20-80% of each cycle): sets pan target to the end position
    with a slow hardware speed for a physically smooth glide.
    Dark windows (0-20% and 80-100%): snaps pan to the reset position at
    full motor speed while the dimmer is zero, giving the motor time to
    reach the start before the light comes back on.

    *speed* defaults to ``config.PAN_SPEED`` when not supplied.
    """
    from config import PAN_SPEED
    if speed is None:
        speed = PAN_SPEED

    cycle = int(beat / glide_beats)
    phase = (beat % glide_beats) / glide_beats
    start = starts[cycle % len(starts)]
    end = ends[cycle % len(ends)]

    if phase < 0.20:
        head.speed = 0
        head.set_pan_relative(start)
        head.dimmer = 0
    elif phase <= 0.80:
        head.speed = speed
        head.set_pan_relative(end)
        head.dimmer = 255
    else:
        next_start = starts[(cycle + 1) % len(starts)]
        head.speed = 0
        head.set_pan_relative(next_start)
        head.dimmer = 0


# ---------------------------------------------------------------------------
# Discrete helpers
# ---------------------------------------------------------------------------

def floor_light(pars: ParGroup):
    """Set pars to dim white using the group's floor_brightness level."""
    pars.strobe_off()
    pars.set_rgb(255, 255, 255)
    pars.set_dimmer(int(255 * pars.floor_brightness))


def step_cycle(beat: float, period_beats: float, values: list[Any],
               offset: int = 0) -> Any:
    """Cycle through *values*, advancing one step every *period_beats*."""
    idx = (int(beat / period_beats) + offset) % len(values)
    return values[idx]


# ---------------------------------------------------------------------------
# Sequence — multi-section choreography
# ---------------------------------------------------------------------------

class Sequence:
    """Define a program as a list of (duration_beats, handler) sections.

    ``resolve(beat)`` returns ``(handler, local_beat)`` for the section
    that *beat* falls in.  The total loop length equals the sum of all
    section durations.
    """

    def __init__(self, sections: list[tuple[int, Callable]]):
        self.sections = sections
        self.total_beats = sum(dur for dur, _ in sections)
        self._offsets: list[int] = []
        acc = 0
        for dur, _ in sections:
            self._offsets.append(acc)
            acc += dur

    def resolve(self, beat: float) -> tuple[Callable, float]:
        b = beat % self.total_beats
        for i in range(len(self.sections) - 1, -1, -1):
            if b >= self._offsets[i]:
                handler = self.sections[i][1]
                local_beat = b - self._offsets[i]
                return handler, local_beat
        return self.sections[0][1], b
