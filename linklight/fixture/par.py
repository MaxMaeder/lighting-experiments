"""Par light fixture — 7-channel RGBW par cans with strobe."""

from __future__ import annotations

from fixture.moving_head import Color
from fixture.strobe import COLOR_TO_RGB

NUM_CHANNELS = 7

CH_DIMMER = 0
CH_RED = 1
CH_GREEN = 2
CH_BLUE = 3
CH_UNUSED = 4
CH_FEATURE = 5
CH_STROBE = 6

PAR_NAMES = ["main-left", "main-right", "side-left", "side-right"]


class ParLight:
    def __init__(self, base_addr: int, name: str = ""):
        self.base_addr = base_addr
        self.name = name
        self._channels = [0] * NUM_CHANNELS

    @property
    def dimmer(self) -> int:
        return self._channels[CH_DIMMER]

    @dimmer.setter
    def dimmer(self, value: int):
        self._channels[CH_DIMMER] = max(0, min(255, value))

    @property
    def red(self) -> int:
        return self._channels[CH_RED]

    @red.setter
    def red(self, value: int):
        self._channels[CH_RED] = max(0, min(255, value))

    @property
    def green(self) -> int:
        return self._channels[CH_GREEN]

    @green.setter
    def green(self, value: int):
        self._channels[CH_GREEN] = max(0, min(255, value))

    @property
    def blue(self) -> int:
        return self._channels[CH_BLUE]

    @blue.setter
    def blue(self, value: int):
        self._channels[CH_BLUE] = max(0, min(255, value))

    @property
    def strobe_speed(self) -> int:
        return self._channels[CH_STROBE]

    @strobe_speed.setter
    def strobe_speed(self, value: int):
        self._channels[CH_STROBE] = max(0, min(255, value))

    def set_rgb(self, r: int, g: int, b: int):
        self.red = r
        self.green = g
        self.blue = b

    def set_color(self, color: Color):
        r, g, b = COLOR_TO_RGB.get(color, (255, 255, 255))
        self.set_rgb(r, g, b)

    def strobe(self, speed: float = 0.5):
        """Set strobe speed. 0.0 (slow) to 1.0 (fastest), mapped to 1-255."""
        speed = max(0.0, min(1.0, speed))
        self.strobe_speed = int(1 + speed * 254)

    def strobe_off(self):
        self.strobe_speed = 0

    def off(self):
        self._channels = [0] * NUM_CHANNELS

    def get_channel_values(self) -> dict[int, int]:
        out = {}
        for i, v in enumerate(self._channels):
            out[self.base_addr + i] = v
        return out


class ParGroup:
    """A group of par lights sharing a master brightness control."""

    def __init__(self, base_addr: int, names: list[str] = PAR_NAMES):
        self.master_brightness: float = 1.0
        self.floor_brightness: float = 0.3
        self.pars: dict[str, ParLight] = {}
        for i, name in enumerate(names):
            self.pars[name] = ParLight(base_addr + i * NUM_CHANNELS, name)

    def __getitem__(self, name: str) -> ParLight:
        return self.pars[name]

    def __iter__(self):
        return iter(self.pars.values())

    def set_rgb(self, r: int, g: int, b: int):
        for par in self:
            par.set_rgb(r, g, b)

    def set_color(self, color: Color):
        for par in self:
            par.set_color(color)

    def set_dimmer(self, value: int):
        for par in self:
            par.dimmer = value

    def set_strobe(self, speed: float):
        for par in self:
            par.strobe(speed)

    def strobe_off(self):
        for par in self:
            par.strobe_off()

    def off(self):
        for par in self:
            par.off()

    def get_channel_values(self) -> dict[int, int]:
        out = {}
        mb = max(0.0, min(1.0, self.master_brightness))
        for par in self:
            for addr, val in par.get_channel_values().items():
                if (addr - par.base_addr) == CH_DIMMER:
                    val = int(val * mb)
                out[addr] = val
        return out
