from __future__ import annotations

from enum import IntEnum

from config import PAN_MIN, PAN_MAX, TILT_MIN, TILT_MAX, HOME_PAN, HOME_TILT


# ---------------------------------------------------------------------------
# Color wheel (16 positions, DMX 0-120 in steps of 8)
# ---------------------------------------------------------------------------

class Color(IntEnum):
    WHITE = 0
    RED = 8
    LIGHT_BLUE = 16
    ORANGE = 24
    DARK_BLUE = 32
    YELLOW = 40
    GREEN = 48
    PURPLE = 56
    RED_WHITE = 64
    # RED_LIGHT_BLUE = 64
    # 72 = duplicate of Red / Light Blue
    ORANGE_LIGHT_BLUE = 80
    ORANGE_DARK_BLUE = 88
    #YELLOW_DARK_BLUE = 96
    YELLOW_GREEN = 104
    # 112 = duplicate of Yellow / Green
    PURPLE_GREEN = 120


def _enum_display_name(member_name: str) -> str:
    return member_name.replace("_", " ").title()


COLOR_NAMES: dict[Color, str] = {c: _enum_display_name(c.name) for c in Color}

ALL_COLORS: list[Color] = list(Color)

# Convenience subset: the 7 solid (non-split) colors
SOLID_COLORS: list[Color] = [
    Color.WHITE, Color.RED, Color.LIGHT_BLUE, Color.ORANGE,
    Color.DARK_BLUE, Color.YELLOW, Color.GREEN, Color.PURPLE,
]

NON_WHITE_COLORS: list[Color] = [c for c in SOLID_COLORS if c != Color.WHITE]


# ---------------------------------------------------------------------------
# Gobo wheel (8 patterns + 8 shake variants, DMX 0-120 in steps of 8)
# ---------------------------------------------------------------------------

class Gobo(IntEnum):
    PATTERN_1 = 0
    PATTERN_2 = 8
    BEAM = 16
    PATTERN_4 = 24
    PATTERN_5 = 32
    PATTERN_6 = 40
    PATTERN_7 = 48
    PATTERN_8 = 56
    PATTERN_1_SHAKE = 64
    PATTERN_2_SHAKE = 72
    BEAM_SHAKE = 80
    PATTERN_4_SHAKE = 88
    PATTERN_5_SHAKE = 96
    PATTERN_6_SHAKE = 104
    PATTERN_7_SHAKE = 112
    PATTERN_8_SHAKE = 120


GOBO_NAMES: dict[Gobo, str] = {g: _enum_display_name(g.name) for g in Gobo}

STATIC_GOBOS: list[Gobo] = [
    Gobo.PATTERN_1, Gobo.PATTERN_2, Gobo.PATTERN_4,
    Gobo.PATTERN_5, Gobo.PATTERN_6, Gobo.PATTERN_7, Gobo.PATTERN_8,
]

SHAKE_GOBOS: list[Gobo] = [
    Gobo.PATTERN_1_SHAKE, Gobo.PATTERN_2_SHAKE,
    Gobo.PATTERN_4_SHAKE, Gobo.PATTERN_5_SHAKE, Gobo.PATTERN_6_SHAKE,
    Gobo.PATTERN_7_SHAKE, Gobo.PATTERN_8_SHAKE,
]


# ---------------------------------------------------------------------------
# DMX channel layout
# ---------------------------------------------------------------------------

NUM_CHANNELS = 9

CH_PAN = 0
CH_TILT = 1
CH_COLOR = 2
CH_GOBO = 3
CH_LAMP = 4
CH_DIMMER = 5
CH_SPEED = 6


class MovingHead:
    def __init__(self, base_addr: int):
        self.base_addr = base_addr
        self._channels = [0] * NUM_CHANNELS
        self.master_brightness: float = 1.0

    # -- pan / tilt ------------------------------------------------------

    @property
    def pan(self) -> int:
        return self._channels[CH_PAN]

    @pan.setter
    def pan(self, value: int):
        self._channels[CH_PAN] = max(0, min(255, value))

    @property
    def tilt(self) -> int:
        return self._channels[CH_TILT]

    @tilt.setter
    def tilt(self, value: int):
        self._channels[CH_TILT] = max(0, min(255, value))

    def set_pan_relative(self, t: float):
        """t in [0, 1] mapped to configured PAN_MIN..PAN_MAX."""
        t = max(0.0, min(1.0, t))
        self.pan = int(PAN_MIN + t * (PAN_MAX - PAN_MIN))

    def set_tilt_relative(self, t: float):
        """t in [0, 1] mapped to configured TILT_MIN..TILT_MAX."""
        t = max(0.0, min(1.0, t))
        self.tilt = int(TILT_MIN + t * (TILT_MAX - TILT_MIN))

    def set_pan_relative_smooth(self, target: float, rate: float = 0.25):
        """Exponentially ease toward *target* (0-1). Call every frame."""
        current_rel = (self.pan - PAN_MIN) / max(1, PAN_MAX - PAN_MIN)
        target = max(0.0, min(1.0, target))
        smoothed = current_rel + (target - current_rel) * max(0.0, min(1.0, rate))
        self.set_pan_relative(smoothed)

    def set_tilt_relative_smooth(self, target: float, rate: float = 0.25):
        """Exponentially ease toward *target* (0-1). Call every frame."""
        current_rel = (self.tilt - TILT_MIN) / max(1, TILT_MAX - TILT_MIN)
        target = max(0.0, min(1.0, target))
        smoothed = current_rel + (target - current_rel) * max(0.0, min(1.0, rate))
        self.set_tilt_relative(smoothed)

    def go_home(self):
        """Move to the configured home position (absolute DMX values)."""
        self.pan = HOME_PAN
        self.tilt = HOME_TILT

    # -- color -----------------------------------------------------------

    @property
    def color(self) -> int:
        return self._channels[CH_COLOR]

    @color.setter
    def color(self, value: int):
        self._channels[CH_COLOR] = max(0, min(max(Color), value))

    # -- gobo ------------------------------------------------------------

    @property
    def gobo(self) -> int:
        return self._channels[CH_GOBO]

    @gobo.setter
    def gobo(self, value: int):
        self._channels[CH_GOBO] = max(0, min(max(Gobo), value))

    # -- lamp / strobe ---------------------------------------------------

    @property
    def lamp(self) -> int:
        return self._channels[CH_LAMP]

    @lamp.setter
    def lamp(self, value: int):
        self._channels[CH_LAMP] = max(0, min(247, value))

    def lamp_on(self):
        self.lamp = 8

    def lamp_off(self):
        self.lamp = 0

    def strobe(self, speed: float = 0.5):
        """Strobe effect. *speed* 0.0 (slow) to 1.0 (fast), mapped to DMX 16-131."""
        speed = max(0.0, min(1.0, speed))
        self.lamp = int(16 + speed * 115)

    def strobe_random(self):
        """Random strobe effect (DMX 240)."""
        self.lamp = 240

    # -- dimmer ----------------------------------------------------------

    @property
    def dimmer(self) -> int:
        return self._channels[CH_DIMMER]

    @dimmer.setter
    def dimmer(self, value: int):
        self._channels[CH_DIMMER] = max(0, min(255, value))

    # -- speed (pan/tilt motor speed) ------------------------------------

    @property
    def speed(self) -> int:
        return self._channels[CH_SPEED]

    @speed.setter
    def speed(self, value: int):
        self._channels[CH_SPEED] = max(0, min(255, value))

    def set_speed(self, t: float):
        """t in [0, 1] where 0 = full speed (DMX 0), 1 = slowest (DMX 255)."""
        t = max(0.0, min(1.0, t))
        self.speed = int(t * 255)

    # -- DMX output ------------------------------------------------------

    def get_channel_values(self) -> dict[int, int]:
        """Returns {1-indexed DMX address: value} for all channels.

        The dimmer channel is scaled by master_brightness so the UI
        slider acts as a global cap.
        """
        out = {}
        for i, v in enumerate(self._channels):
            addr = self.base_addr + i
            if i == CH_DIMMER:
                v = int(v * max(0.0, min(1.0, self.master_brightness)))
            out[addr] = v
        return out
