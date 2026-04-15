"""Colors — solid color pulses with contrasting mover, cycling color beats."""

import random

from config import DISCO_BALL_PAN, DISCO_BALL_TILT, SLOW_PAN_SPEED
from fixture import Color, Gobo, MovingHead, NON_WHITE_COLORS, ParGroup, SHAKE_GOBOS, StrobeLight
from programs.base import ProgramOptions, ShowProgram
from programs.utils import Sequence, oscillate, pulse, smooth_pan, step_cycle

CONTRASTING_COLORS: dict[Color, Color] = {
    Color.RED:        Color.GREEN,
    Color.LIGHT_BLUE: Color.ORANGE,
    Color.ORANGE:     Color.DARK_BLUE,
    Color.DARK_BLUE:  Color.YELLOW,
    Color.YELLOW:     Color.PURPLE,
    Color.GREEN:      Color.RED,
    Color.PURPLE:     Color.YELLOW,
}

_SLOW_PAN_STARTS = [0.30, 0.90]
_SLOW_PAN_ENDS = [0.90, 0.30]

_FAST_PAN_STARTS = [0.05, 0.95, 0.05, 0.95, 0.05, 0.95, 0.05, 0.95]
_FAST_PAN_ENDS = [0.95, 0.05, 0.95, 0.05, 0.95, 0.05, 0.95, 0.05]


class ColorsProgram(ShowProgram):
    name = "Colors"
    loop_beats = 62

    def __init__(self, options: ProgramOptions | None = None):
        super().__init__(options)
        self._section_colors: tuple[Color, Color] = (NON_WHITE_COLORS[0], NON_WHITE_COLORS[1])
        self._section_beat: float = float('inf')
        self.sections = Sequence([
            (16, self._solid_pulse),
            (16, self._color_cycle),
            (16, self._rainbow_ball),
            (14, self._color_step),
        ])

    def update(self, head: MovingHead, strobe: StrobeLight, pars: ParGroup,
               beat: float, tempo: float):
        handler, local = self.sections.resolve(beat)
        handler(head, strobe, pars, local, tempo)

    def _pick_section_colors(self, beat: float):
        """Pick two distinct random non-white colors when the section restarts."""
        if beat < self._section_beat:
            a = random.choice(NON_WHITE_COLORS)
            remaining = [c for c in NON_WHITE_COLORS if c != a]
            b = random.choice(remaining)
            self._section_colors = (a, b)
        self._section_beat = beat

    @staticmethod
    def _beat_brightness(beat: float) -> int:
        p = pulse(beat, round(beat), 0.15)
        return int(80 + 175 * p)

    # -- sections --------------------------------------------------------

    def _solid_pulse(self, head: MovingHead, strobe: StrobeLight, pars: ParGroup,
                     beat: float, tempo: float):
        """Two 8-beat slow pans, each with its own color.  Pars pulse the
        color on beat; mover and strobe use the contrasting color."""
        self._pick_section_colors(beat)
        color = self._section_colors[0 if beat < 8 else 1]
        contrast = CONTRASTING_COLORS.get(color, Color.RED)

        bri = self._beat_brightness(beat)

        pars.strobe_off()
        pars.set_color(color)
        pars.set_dimmer(bri)

        strobe.set_color(contrast)
        strobe.brightness = bri

        head.lamp_on()
        head.gobo = Gobo.BEAM
        head.set_tilt_relative(0.5)
        head.color = contrast
        smooth_pan(head, beat, 8.0, _SLOW_PAN_STARTS, _SLOW_PAN_ENDS,
                   speed=SLOW_PAN_SPEED)

    def _color_cycle(self, head: MovingHead, strobe: StrobeLight, pars: ParGroup,
                     beat: float, tempo: float):
        """Pars cycle through colors one per beat.  Mover and strobe pulse
        white; mover does faster pans."""
        color = step_cycle(beat, 1, NON_WHITE_COLORS)
        bri = self._beat_brightness(beat)

        pars.strobe_off()
        pars.set_color(color)
        pars.set_dimmer(bri)

        strobe.set_color(Color.WHITE)
        strobe.brightness = bri

        head.lamp_on()
        head.gobo = step_cycle(beat, 2, SHAKE_GOBOS)
        head.set_tilt_relative(0.5)
        head.color = Color.WHITE
        smooth_pan(head, beat, 2.0, _FAST_PAN_STARTS, _FAST_PAN_ENDS)

    def _color_step(self, head: MovingHead, strobe: StrobeLight, pars: ParGroup,
                    beat: float, tempo: float):
        """Each fixture steps through NON_WHITE_COLORS one per beat.
        Mover and strobe share a color; mover does fast pans with shake gobos.
        Colors start at RED on the mover so the wheel only moves forward."""
        n = len(NON_WHITE_COLORS)
        step = int(beat)

        color = NON_WHITE_COLORS[step % n]

        bri = self._beat_brightness(beat)

        strobe.set_color(color)
        strobe.brightness = bri

        head.lamp_on()
        head.gobo = step_cycle(beat, 2, SHAKE_GOBOS)
        head.set_tilt_relative(0.5)
        head.color = color
        smooth_pan(head, beat, 2.0, _FAST_PAN_STARTS, _FAST_PAN_ENDS)

        pars.strobe_off()
        par_list = list(pars)
        for i, par in enumerate(par_list):
            par.set_color(NON_WHITE_COLORS[(step + i + 1) % n])
            par.dimmer = bri

    def _rainbow_ball(self, head: MovingHead, strobe: StrobeLight, pars: ParGroup,
                      beat: float, tempo: float):
        """Pars and strobe do a smooth RGB rainbow with beat pulsing.
        Mover sits on the disco ball, white, open gobo shake, pulsing."""
        r = int(oscillate(beat, 3.0, 0, 255))
        g = int(oscillate(beat + 1.0, 3.0, 0, 255))
        b = int(oscillate(beat + 2.0, 3.0, 0, 255))
        bri = self._beat_brightness(beat)

        pars.strobe_off()
        pars.set_rgb(r, g, b)
        pars.set_dimmer(bri)

        strobe.set_rgb(r, g, b)
        strobe.brightness = bri

        head.lamp_on()
        head.gobo = Gobo.BEAM_SHAKE
        head.speed = 0
        head.set_pan_relative(DISCO_BALL_PAN)
        head.set_tilt_relative(DISCO_BALL_TILT)
        head.color = Color.WHITE
        head.dimmer = bri
