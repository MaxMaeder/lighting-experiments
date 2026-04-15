"""Show-program registry.  Import this to get PROGRAM_REGISTRY."""

from programs.colors import ColorsProgram
from programs.disco import DiscoProgram
from programs.edm import EdmProgram
from programs.house import HouseLightsProgram

PROGRAM_REGISTRY: dict[str, type] = {
    ColorsProgram.name: ColorsProgram,
    DiscoProgram.name: DiscoProgram,
    EdmProgram.name: EdmProgram,
}

HOUSE_PROGRAM_CLASS = HouseLightsProgram
