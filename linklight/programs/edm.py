"""EDM — color pans, wall flash, effect mode accents, disco ball color cycle."""

import random

from config import DISCO_BALL_PAN, DISCO_BALL_TILT, SLOW_PAN_SPEED
from fixture import (
    Color, Effect, Gobo, MovingHead, NON_WHITE_COLORS, STATIC_GOBOS, StrobeLight,
)
from programs.base import ProgramOptions, ShowProgram
from programs.utils import Sequence, pulse, smooth_pan, step_cycle

_SETTLE = 1.0

_PAN_STARTS = [0.05, 0.95, 0.05, 0.95, 0.05, 0.95]
_PAN_ENDS   = [0.95, 0.05, 0.95, 0.05, 0.95, 0.05]

_FLASH_POSITIONS = [0.15, 0.85, 0.50, 0.70]

_EFFECT_PAN_STARTS = [0.05, 0.95, 0.05, 0.95]
_EFFECT_PAN_ENDS   = [0.95, 0.05, 0.95, 0.05]


class EdmProgram(ShowProgram):
    name = "EDM"
    loop_beats = 64

    def __init__(self, options: ProgramOptions | None = None):
        super().__init__(options)
        self._offsets: dict[str, int] = {}
        self._offset_beats: dict[str, float] = {}
        self.sections = Sequence([
            (13, self._color_pans),
            (17, self._wall_flash),
            (9,  self._effect_arrows_ball),
            (8,  self._beam_shake_sweep),
            (9,  self._effect_pan),
            (8,  self._ball_color_cycle),
        ])

    def update(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        handler, local = self.sections.resolve(beat)
        handler(head, strobe, local, tempo)

    def _rolling_offset(self, key: str, beat: float, max_offset: int) -> int:
        """Return a random offset that re-rolls each time the section restarts."""
        if beat < self._offset_beats.get(key, float('inf')):
            self._offsets[key] = random.randint(0, max_offset)
        self._offset_beats[key] = beat
        return self._offsets[key]

    # -- sections --------------------------------------------------------

    def _color_pans(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Alternating L-R / R-L smooth pans, color per pan, strobe white pulse.
        First beat is dark to let the color wheel settle on entry."""
        co = self._rolling_offset('color_pan', beat, len(NON_WHITE_COLORS) - 6)

        head.lamp_on()
        head.gobo = Gobo.BEAM
        head.set_tilt_relative(0.5)

        if beat < _SETTLE:
            head.color = step_cycle(0, 2, NON_WHITE_COLORS, co)
            head.speed = 0
            head.set_pan_relative(_PAN_STARTS[0])
            head.dimmer = 0
        else:
            local = beat - _SETTLE
            head.color = step_cycle(local, 2, NON_WHITE_COLORS, co)
            smooth_pan(head, local, 2.0, _PAN_STARTS, _PAN_ENDS)

        strobe.set_color(Color.WHITE)
        p = pulse(beat, round(beat), 0.15)
        strobe.brightness = int(50 + 150 * p)

    def _wall_flash(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """2 beats on / 2 beats off.  Mover illuminates a wall position with a
        color and gobo, then goes dark while repositioning.  Gobo and color
        change at the start of each dark phase so the wheels move while
        invisible.  First beat is dark settling."""
        co = self._rolling_offset('wf_color', beat, len(NON_WHITE_COLORS) - 5)
        go = self._rolling_offset('wf_gobo', beat, len(STATIC_GOBOS) - 5)

        head.lamp_on()
        head.speed = 0
        head.set_tilt_relative(0.5)

        if beat < _SETTLE:
            head.color = NON_WHITE_COLORS[co]
            head.gobo = STATIC_GOBOS[go]
            head.set_pan_relative(_FLASH_POSITIONS[0])
            head.dimmer = 0
            head.speed = 0
            strobe.set_color(Color.WHITE)
        else:
            local = beat - _SETTLE
            cycle = int(local / 4)
            phase = local % 4
            on = phase < 2.0

            color = NON_WHITE_COLORS[(cycle + co) % len(NON_WHITE_COLORS)]
            gobo = STATIC_GOBOS[(cycle + go) % len(STATIC_GOBOS)]
            pos = _FLASH_POSITIONS[cycle % len(_FLASH_POSITIONS)]

            next_cycle = cycle + 1
            next_color = NON_WHITE_COLORS[(next_cycle + co) % len(NON_WHITE_COLORS)]
            next_gobo = STATIC_GOBOS[(next_cycle + go) % len(STATIC_GOBOS)]
            next_pos = _FLASH_POSITIONS[next_cycle % len(_FLASH_POSITIONS)]

            if on:
                head.color = color
                head.gobo = gobo
                head.set_pan_relative(pos)
                p = pulse(beat, round(beat), 0.15)
                head.dimmer = int(80 + 175 * p)
                strobe.set_color(color)
            else:
                head.color = next_color
                head.gobo = next_gobo
                head.set_pan_relative(next_pos)
                head.dimmer = 0
                strobe.set_color(Color.WHITE)

        p = pulse(beat, round(beat), 0.15)
        strobe.brightness = int(50 + 150 * p)

    def _effect_arrows_ball(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Strobe runs arrows effect.  Mover on disco ball, white, open gobo,
        flashes every beat with a low baseline between hits.  First beat is
        dark settling."""
        strobe.set_effect(Effect.ARROWS)
        strobe.set_effect_speed(0.5)
        strobe.brightness = 255

        head.lamp_on()
        head.speed = 0
        head.set_pan_relative(DISCO_BALL_PAN)
        head.set_tilt_relative(DISCO_BALL_TILT)
        head.color = Color.WHITE

        if beat < _SETTLE:
            head.gobo = Gobo.BEAM
            head.dimmer = 0
            head.speed = 0
        else:
            local = beat - _SETTLE
            up = int(local) % 2 == 0
            head.gobo = Gobo.BEAM if up else Gobo.BEAM_SHAKE
            head.dimmer = 255 if up else 40

    def _beam_shake_sweep(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Slow single-direction sweep with beam shake, white.
        Strobe runs sine wave effect."""
        strobe.set_effect(Effect.SINE_WAVE)
        strobe.set_effect_speed(0.5)
        strobe.brightness = 255

        head.lamp_on()
        head.gobo = Gobo.BEAM_SHAKE
        head.set_tilt_relative(0.5)
        head.color = Color.WHITE

        if beat < 0.5:
            head.speed = 0
            head.set_pan_relative(0.05)
            head.dimmer = 0
        else:
            head.speed = SLOW_PAN_SPEED
            head.set_pan_relative(0.95)

            p = pulse(beat, round(beat), 0.15)
            head.dimmer = int(80 + 175 * p)

    def _effect_pan(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Strobe runs color-change-from-center effect.  Mover smooth pans
        independently with open gobo, cycling colors.  First beat is dark
        settling."""
        co = self._rolling_offset('effect_pan', beat, len(NON_WHITE_COLORS) - 4)

        strobe.set_effect(Effect.COLOR_CHANGE_CENTER)
        strobe.set_effect_speed(0.5)
        strobe.brightness = 255

        head.lamp_on()
        head.gobo = Gobo.BEAM
        head.set_tilt_relative(0.5)

        if beat < _SETTLE:
            head.color = NON_WHITE_COLORS[co]
            head.speed = 0
            head.set_pan_relative(_EFFECT_PAN_STARTS[0])
            head.dimmer = 0
        else:
            local = beat - _SETTLE
            head.color = step_cycle(local, 2, NON_WHITE_COLORS, co)
            smooth_pan(head, local, 2.0, _EFFECT_PAN_STARTS, _EFFECT_PAN_ENDS)

    def _ball_color_cycle(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Mover on disco ball, color changes every beat.  Strobe off.
        First beat is dark settling."""
        head.lamp_on()
        head.speed = 0
        head.set_pan_relative(DISCO_BALL_PAN)
        head.set_tilt_relative(DISCO_BALL_TILT)
        head.gobo = Gobo.BEAM

        if beat < _SETTLE:
            head.color = NON_WHITE_COLORS[0]
            head.dimmer = 0
        else:
            head.color = step_cycle(beat - _SETTLE, 1, NON_WHITE_COLORS)
            head.dimmer = 255

        strobe.off()
