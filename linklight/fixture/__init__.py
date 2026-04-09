"""Fixture package — re-exports from both submodules for backward compatibility."""

from fixture.moving_head import (
    ALL_COLORS,
    COLOR_NAMES,
    Color,
    GOBO_NAMES,
    Gobo,
    MovingHead,
    NON_WHITE_COLORS,
    SOLID_COLORS,
    STATIC_GOBOS,
)
from fixture.strobe import COLOR_TO_RGB, Effect, StrobeLight

__all__ = [
    "ALL_COLORS",
    "COLOR_NAMES",
    "COLOR_TO_RGB",
    "Color",
    "Effect",
    "GOBO_NAMES",
    "Gobo",
    "MovingHead",
    "NON_WHITE_COLORS",
    "SOLID_COLORS",
    "STATIC_GOBOS",
    "StrobeLight",
]
