"""House Lights — mover goes home and turns off, strobe solid red."""

from fixture import Gobo, MovingHead, ParGroup, StrobeLight
from programs.base import ProgramOptions, ShowProgram


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
        strobe.set_rgb(255, 0, 0)
        strobe.brightness = 255

        pars.strobe_off()
        pars.set_rgb(255, 0, 0)
        pars.set_dimmer(255)
