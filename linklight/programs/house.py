"""House Lights — mover goes home and turns off, strobe and pars solid yellow."""

from fixture import Gobo, MovingHead, ParGroup, StrobeLight
from programs.base import ProgramOptions, ShowProgram

HOUSE_COLOR_RGB = (255, 100, 0)
HOUSE_BRIGHTNESS = 60


class HouseLightsProgram(ShowProgram):
    name = "House Lights"
    loop_beats = 1

    def update(self, head: MovingHead, strobe: StrobeLight, pars: ParGroup,
               beat: float, tempo: float):
        head.go_home()
        head.lamp_off()
        head.color = 0
        head.gobo = Gobo.PATTERN_1
        head.dimmer = 0

        strobe.strobe_off()
        strobe.set_rgb(*HOUSE_COLOR_RGB)
        strobe.brightness = HOUSE_BRIGHTNESS

        pars.strobe_off()
        pars.set_rgb(*HOUSE_COLOR_RGB)
        pars.set_dimmer(HOUSE_BRIGHTNESS)
