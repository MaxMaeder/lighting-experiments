from __future__ import annotations

from enum import IntEnum

from fixture.moving_head import Color

# ---------------------------------------------------------------------------
# Color enum -> RGB mapping for the strobe's RGB channels
# ---------------------------------------------------------------------------

COLOR_TO_RGB: dict[Color, tuple[int, int, int]] = {
    Color.WHITE:              (255, 255, 255),
    Color.RED:                (255, 0,   0),
    Color.LIGHT_BLUE:         (0,   180, 255),
    Color.ORANGE:             (255, 100, 0),
    Color.DARK_BLUE:          (0,   0,   200),
    Color.GREEN:              (0,   255, 0),
    Color.PURPLE:             (150, 0,   255),
    Color.YELLOW:             (255, 255, 0),
    Color.RED_WHITE:          (255, 130, 130),
#    Color.RED_LIGHT_BLUE:     (128, 90,  128),
    Color.ORANGE_LIGHT_BLUE:  (128, 140, 128),
    Color.ORANGE_DARK_BLUE:   (128, 50,  100),
    # Color.YELLOW_DARK_BLUE:   (128, 128, 100),
    Color.YELLOW_GREEN:       (128, 255, 0),
    Color.PURPLE_GREEN:       (75,  128, 128),
}

# ---------------------------------------------------------------------------
# Inner effect patterns (ch 4, 1-indexed)
# ---------------------------------------------------------------------------

class Effect(IntEnum):
    COLOR_CHANGE_LR     = 51
    DOTS                = 76
    CROSSHAIR           = 86
    RAINING_DOTS        = 90
    SINE_WAVE           = 101
    ARROWS              = 164
    COLOR_CHANGE_CENTER = 175
    THICK_SINE_WAVE     = 211


def _effect_display_name(member_name: str) -> str:
    return member_name.replace("_", " ").title()


EFFECT_NAMES: dict[Effect, str] = {e: _effect_display_name(e.name) for e in Effect}


ALL_EFFECTS: list[Effect] = list(Effect)

# ---------------------------------------------------------------------------
# DMX channel layout (10 channels)
# ---------------------------------------------------------------------------

NUM_CHANNELS = 10

CH_BRIGHTNESS = 0
CH_STROBE = 1
CH_MODE = 2
CH_EFFECT = 3
CH_EFFECT_SPEED = 4
CH_RED = 5
CH_GREEN = 6
CH_BLUE = 7

MODE_RGB = 0
MODE_EFFECT = 86

EFFECT_SPEED_MIN = 190
EFFECT_SPEED_MAX = 240


class StrobeLight:
    def __init__(self, base_addr: int):
        self.base_addr = base_addr
        self._channels = [0] * NUM_CHANNELS
        self.master_brightness: float = 1.0

    # -- brightness ------------------------------------------------------

    @property
    def brightness(self) -> int:
        return self._channels[CH_BRIGHTNESS]

    @brightness.setter
    def brightness(self, value: int):
        self._channels[CH_BRIGHTNESS] = max(0, min(255, value))

    # -- RGB channels ----------------------------------------------------

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

    def set_rgb(self, r: int, g: int, b: int):
        self.mode = MODE_RGB
        self.red = r
        self.green = g
        self.blue = b

    def set_color(self, color: Color):
        """Set RGB from a Color enum value using the COLOR_TO_RGB mapping."""
        r, g, b = COLOR_TO_RGB.get(color, (255, 255, 255))
        self.set_rgb(r, g, b)

    # -- operation mode --------------------------------------------------

    @property
    def mode(self) -> int:
        return self._channels[CH_MODE]

    @mode.setter
    def mode(self, value: int):
        self._channels[CH_MODE] = max(0, min(255, value))

    # -- inner effect ----------------------------------------------------

    @property
    def effect(self) -> int:
        return self._channels[CH_EFFECT]

    @effect.setter
    def effect(self, value: int):
        self._channels[CH_EFFECT] = max(0, min(255, value))

    def set_effect(self, effect: Effect):
        """Select an inner effect pattern. Automatically enters effect mode."""
        self.mode = MODE_EFFECT
        self.effect = int(effect)

    # -- effect speed ----------------------------------------------------

    @property
    def effect_speed(self) -> int:
        return self._channels[CH_EFFECT_SPEED]

    @effect_speed.setter
    def effect_speed(self, value: int):
        self._channels[CH_EFFECT_SPEED] = max(0, min(255, value))

    def set_effect_speed(self, t: float):
        """t in [0, 1] mapped to the useful DMX range (190-240)."""
        self.mode = MODE_EFFECT
        t = max(0.0, min(1.0, t))
        self.effect_speed = int(EFFECT_SPEED_MIN + t * (EFFECT_SPEED_MAX - EFFECT_SPEED_MIN))

    # -- strobe speed ----------------------------------------------------

    @property
    def strobe_speed(self) -> int:
        return self._channels[CH_STROBE]

    @strobe_speed.setter
    def strobe_speed(self, value: int):
        self._channels[CH_STROBE] = max(0, min(255, value))

    def strobe(self, speed: float = 0.5):
        """Set strobe speed. 0.0 (slow) to 1.0 (fastest), mapped to 1-255."""
        speed = max(0.0, min(1.0, speed))
        self.strobe_speed = int(1 + speed * 254)

    def strobe_off(self):
        self.strobe_speed = 0

    # -- convenience -----------------------------------------------------

    def off(self):
        self._channels = [0] * NUM_CHANNELS

    # -- DMX output ------------------------------------------------------

    def get_channel_values(self) -> dict[int, int]:
        """Returns {1-indexed DMX address: value} for all channels.

        The brightness channel is scaled by master_brightness so the UI
        slider acts as a global cap.
        """
        out = {}
        for i, v in enumerate(self._channels):
            addr = self.base_addr + i
            if i == CH_BRIGHTNESS:
                v = int(v * max(0.0, min(1.0, self.master_brightness)))
            out[addr] = v
        return out
