"""
Phase 7: Style Resolver and Recipe Definitions

Four recipes: flat, sticker, monochrome, neon.
Each recipe maps roles to concrete colors and stroke properties.
"""

from dataclasses import dataclass
from typing import Optional
from .schema import Role, StyleRecipe


@dataclass
class ColorStop:
    """A color value with optional opacity."""
    hex_color: str  # e.g. "#4A90E2"
    opacity: float = 1.0  # 0.0-1.0


@dataclass
class RoleStyle:
    """Style for a single role."""
    fill: Optional[ColorStop] = None
    stroke: Optional[ColorStop] = None
    stroke_width: float = 0.0


# ============================================================================
# Recipe Definitions
# ============================================================================

RECIPE_FLAT = {
    Role.PRIMARY_SURFACE: RoleStyle(
        fill=ColorStop("#4A90E2"),
        stroke=None,
    ),
    Role.SECONDARY_SURFACE: RoleStyle(
        fill=ColorStop("#7FB3F0"),
        stroke=None,
    ),
    Role.OUTLINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#1F2A44"),
        stroke_width=4,
    ),
    Role.ACCENT: RoleStyle(
        fill=ColorStop("#F5A623"),
        stroke=None,
    ),
    Role.HIGHLIGHT: RoleStyle(
        fill=ColorStop("#FFFFFF"),
        stroke=None,
    ),
    Role.SHADOW: RoleStyle(
        fill=ColorStop("#1F2A44", opacity=0.2),
        stroke=None,
    ),
    Role.GLOW: RoleStyle(
        fill=None,
        stroke=None,
    ),
    Role.DETAIL_LINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#1F2A44"),
        stroke_width=2,
    ),
    Role.BACKGROUND_FILL: RoleStyle(
        fill=ColorStop("#F4F6FA"),
        stroke=None,
    ),
}

RECIPE_STICKER = {
    Role.PRIMARY_SURFACE: RoleStyle(
        fill=ColorStop("#4A90E2"),
        stroke=ColorStop("#FFFFFF"),
        stroke_width=8,
    ),
    Role.SECONDARY_SURFACE: RoleStyle(
        fill=ColorStop("#7FB3F0"),
        stroke=ColorStop("#FFFFFF"),
        stroke_width=6,
    ),
    Role.OUTLINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#1F2A44"),
        stroke_width=6,
    ),
    Role.ACCENT: RoleStyle(
        fill=ColorStop("#F5A623"),
        stroke=ColorStop("#FFFFFF"),
        stroke_width=4,
    ),
    Role.HIGHLIGHT: RoleStyle(
        fill=ColorStop("#FFFFFF"),
        stroke=None,
    ),
    Role.SHADOW: RoleStyle(
        fill=ColorStop("#1F2A44", opacity=0.25),
        stroke=None,
    ),
    Role.GLOW: RoleStyle(
        fill=None,
        stroke=None,
    ),
    Role.DETAIL_LINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#1F2A44"),
        stroke_width=3,
    ),
    Role.BACKGROUND_FILL: RoleStyle(
        fill=None,  # transparent
        stroke=None,
    ),
}

RECIPE_MONOCHROME = {
    Role.PRIMARY_SURFACE: RoleStyle(
        fill=ColorStop("#1F2A44"),
        stroke=None,
    ),
    Role.SECONDARY_SURFACE: RoleStyle(
        fill=ColorStop("#5A6378"),
        stroke=None,
    ),
    Role.OUTLINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#1F2A44"),
        stroke_width=4,
    ),
    Role.ACCENT: RoleStyle(
        fill=ColorStop("#1F2A44"),
        stroke=None,
    ),
    Role.HIGHLIGHT: RoleStyle(
        fill=ColorStop("#FFFFFF"),
        stroke=None,
    ),
    Role.SHADOW: RoleStyle(
        fill=ColorStop("#1F2A44", opacity=0.15),
        stroke=None,
    ),
    Role.GLOW: RoleStyle(
        fill=None,
        stroke=None,
    ),
    Role.DETAIL_LINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#1F2A44"),
        stroke_width=2,
    ),
    Role.BACKGROUND_FILL: RoleStyle(
        fill=ColorStop("#FFFFFF"),
        stroke=None,
    ),
}

RECIPE_NEON = {
    Role.PRIMARY_SURFACE: RoleStyle(
        fill=ColorStop("#0E1A2B"),
        stroke=ColorStop("#00E5FF"),
        stroke_width=3,
    ),
    Role.SECONDARY_SURFACE: RoleStyle(
        fill=ColorStop("#1B2C44"),
        stroke=ColorStop("#00E5FF"),
        stroke_width=2,
    ),
    Role.OUTLINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#00E5FF"),
        stroke_width=4,
    ),
    Role.ACCENT: RoleStyle(
        fill=ColorStop("#FF00A8"),
        stroke=None,
    ),
    Role.HIGHLIGHT: RoleStyle(
        fill=ColorStop("#FFFFFF"),
        stroke=None,
    ),
    Role.SHADOW: RoleStyle(
        fill=ColorStop("#000000", opacity=0.4),
        stroke=None,
    ),
    Role.GLOW: RoleStyle(
        fill=ColorStop("#00E5FF", opacity=0.4),
        stroke=None,
    ),
    Role.DETAIL_LINE: RoleStyle(
        fill=None,
        stroke=ColorStop("#00E5FF"),
        stroke_width=2,
    ),
    Role.BACKGROUND_FILL: RoleStyle(
        fill=ColorStop("#0A0F1A"),
        stroke=None,
    ),
}

# Recipe registry
RECIPES = {
    StyleRecipe.FLAT: RECIPE_FLAT,
    StyleRecipe.STICKER: RECIPE_STICKER,
    StyleRecipe.MONOCHROME: RECIPE_MONOCHROME,
    StyleRecipe.NEON: RECIPE_NEON,
}


def get_role_style(role: Role, recipe: StyleRecipe) -> RoleStyle:
    """Get the style for a role in a given recipe."""
    if recipe not in RECIPES:
        raise ValueError(f"Unknown recipe: {recipe}")
    recipe_map = RECIPES[recipe]
    if role not in recipe_map:
        raise ValueError(f"Unknown role in recipe {recipe}: {role}")
    return recipe_map[role]
