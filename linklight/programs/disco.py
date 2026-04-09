"""Disco — 80s color pans, directional sweeps, disco ball focus, rainbow drift."""

from config import DISCO_BALL_PAN, DISCO_BALL_TILT, SLOW_PAN_SPEED
from fixture import Color, Gobo, MovingHead, NON_WHITE_COLORS, STATIC_GOBOS, StrobeLight
from programs.base import ProgramOptions, ShowProgram
from programs.utils import Sequence, oscillate, pulse, ramp, smooth_pan, step_cycle

_COLOR_PAN_STARTS = [0.05, 0.95, 0.05, 0.95, 0.05, 0.95, 0.05, 0.95]
_COLOR_PAN_ENDS   = [0.95, 0.05, 0.95, 0.05, 0.95, 0.05, 0.95, 0.05]

_SWEEP_STARTS = [0.05] * 3 + [0.95] * 3
_SWEEP_ENDS   = [0.95] * 3 + [0.05] * 3

_RAINBOW_STARTS = [0.95, 0.05, 0.95, 0.05, 0.95, 0.05]
_RAINBOW_ENDS   = [0.05, 0.95, 0.05, 0.95, 0.05, 0.95]

_BUILDUP_STARTS = [0.05, 0.95, 0.05, 0.95]
_BUILDUP_ENDS   = [0.95, 0.05, 0.95, 0.05]


class DiscoProgram(ShowProgram):
    name = "Disco"
    loop_beats = 72

    def __init__(self, options: ProgramOptions | None = None):
        super().__init__(options)
        self.sections = Sequence([
            (16, self._color_pans),
            (12, self._directional_sweep),
            (16, self._ball_focus),
            (8,  self._slow_color_pan),
            (12, self._rainbow_pans),
            (8,  self._theme_buildup),
        ])

    def update(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        handler, local = self.sections.resolve(beat)
        handler(head, strobe, local, tempo)

    # -- sections --------------------------------------------------------

    def _color_pans(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Wide alternating L-R pans, one color per pan, open gobo."""
        head.lamp_on()
        head.gobo = Gobo.BEAM
        head.set_tilt_relative(0.5)
        head.color = step_cycle(beat, 2, NON_WHITE_COLORS)
        smooth_pan(head, beat, 2.0, _COLOR_PAN_STARTS, _COLOR_PAN_ENDS)

        strobe.set_color(Color.WHITE)
        p = pulse(beat, round(beat), 0.15)
        strobe.brightness = int(50 + 150 * p)

    def _directional_sweep(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """3 pans L-R then 3 pans R-L, one color per pan, dark on reset."""

        # shift colors by one to the right
        color = step_cycle(beat, 2, NON_WHITE_COLORS[1:] + NON_WHITE_COLORS[:1])

        head.lamp_on()
        head.gobo = Gobo.BEAM_SHAKE
        head.set_tilt_relative(0.5)
        head.color = color
        smooth_pan(head, beat, 2.0, _SWEEP_STARTS, _SWEEP_ENDS)

        strobe.set_color(color)
        p = pulse(beat, round(beat), 0.15)
        strobe.brightness = int(50 + 150 * p)

    def _ball_focus(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Stationary on disco ball, white open gobo, gentle intensity breathing."""
        head.lamp_on()
        head.speed = 0
        head.set_pan_relative(DISCO_BALL_PAN)
        head.set_tilt_relative(DISCO_BALL_TILT)
        head.color = Color.WHITE
        head.gobo = Gobo.BEAM
        p = pulse(beat, round(beat), 0.25)
        head.dimmer = int(80 + 175 * p)

        strobe.off()

    def _slow_color_pan(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Single slow L-R sweep over 8 beats, color changes every beat."""

        color = step_cycle(beat, 1, NON_WHITE_COLORS)

        head.lamp_on()
        head.gobo = Gobo.BEAM
        head.set_tilt_relative(0.5)
        head.color = color

        if beat < 0.5:
            head.speed = 0
            head.set_pan_relative(0.05)
            head.dimmer = 0
        else:
            head.speed = SLOW_PAN_SPEED
            head.set_pan_relative(0.95)
            head.dimmer = 255

        strobe.set_color(color)
        p = pulse(beat, round(beat), 0.15)
        strobe.brightness = int(50 + 150 * p)

    def _rainbow_pans(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Wide pans with one color and gobo per pan, strobe does smooth RGB rainbow."""
        head.lamp_on()
        head.gobo = step_cycle(beat, 2, STATIC_GOBOS)
        head.set_tilt_relative(0.5)
        head.color = step_cycle(beat, 2, NON_WHITE_COLORS)
        smooth_pan(head, beat, 2.0, _RAINBOW_STARTS, _RAINBOW_ENDS)

        r = int(oscillate(beat, 3.0, 0, 255))
        g = int(oscillate(beat + 1.0, 3.0, 0, 255))
        b = int(oscillate(beat + 2.0, 3.0, 0, 255))
        strobe.set_rgb(r, g, b)
        strobe.brightness = 255

    def _theme_buildup(self, head: MovingHead, strobe: StrobeLight, beat: float, tempo: float):
        """Wide alternating pans, theme/white per pan, strobe breathes with rising baseline."""
        color = step_cycle(beat, 2, [self.options.theme_color, Color.WHITE])
        
        head.lamp_on()
        head.gobo = Gobo.BEAM
        head.set_tilt_relative(0.5)
        head.color = color
        smooth_pan(head, beat, 2.0, _BUILDUP_STARTS, _BUILDUP_ENDS)

        strobe.set_color(color)
        p = pulse(beat, round(beat), 0.15)
        base = int(ramp(beat, 0, 8, 50, 100))
        strobe.brightness = int(base + 150 * p)
