"""
Phase 7: Style Resolver (Refactored for Iterative Generation)

Resolves all roles to concrete colors and stroke properties based on recipe.
Applies palette hints.
"""

from colorsys import rgb_to_hsv, hsv_to_rgb

from src.models.schema import (
    SceneDocument, ComponentNode, Role, StyleRecipe, PaletteHint, ResolvedStyle
)
from src.models.recipes import get_role_style


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color (e.g., '#4A90E2') to RGB tuple (0-1 range)."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(r: float, g: float, b: float) -> str:
    """Convert RGB tuple (0-1 range) to hex color."""
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))


def apply_palette_hint(hex_color: str, hint: PaletteHint) -> str:
    """
    Apply palette hint to a hex color.
    Only modifies primary_surface and secondary_surface.
    """
    if hint == PaletteHint.COOL:
        return hex_color
    
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = rgb_to_hsv(r, g, b)
    
    if hint == PaletteHint.WARM:
        h = (h + 30/360) % 1.0
    elif hint == PaletteHint.NEUTRAL:
        s = s * 0.7
    elif hint == PaletteHint.VIBRANT:
        s = min(1.0, s * 1.2)
    elif hint == PaletteHint.MUTED:
        s = s * 0.5
        v = min(1.0, v * 1.1)
    
    r, g, b = hsv_to_rgb(h, s, v)
    return rgb_to_hex(r, g, b)


def style_resolver(
    doc: SceneDocument,
) -> SceneDocument:
    """
    Phase 7: Style Resolver
    
    Resolves all roles to concrete style values based on recipe.
    Applies palette hints to primary and secondary surfaces.
    
    Input: SceneDocument
    Output: same document with resolved colors in node params
    """
    recipe = doc.style_recipe
    palette_hint = doc.palette_hint
    
    for node_id, node in doc.nodes.items():
        if isinstance(node, ComponentNode):
            # Get the style for this role
            role_style = get_role_style(node.role, recipe)

            fill = "none"
            stroke = "none"
            stroke_width = 0.0
            fill_opacity = 1.0
            stroke_opacity = 1.0
            
            # Resolve colors
            if role_style.fill:
                fill_hex = role_style.fill.hex_color
                if node.role in (Role.PRIMARY_SURFACE, Role.SECONDARY_SURFACE):
                    fill_hex = apply_palette_hint(fill_hex, palette_hint)
                fill = fill_hex
                fill_opacity = role_style.fill.opacity
            
            if role_style.stroke:
                stroke = role_style.stroke.hex_color
                stroke_opacity = role_style.stroke.opacity
                stroke_width = role_style.stroke_width

            node.resolved_style = ResolvedStyle(
                fill=fill,
                stroke=stroke,
                stroke_width=stroke_width,
                fill_opacity=fill_opacity,
                stroke_opacity=stroke_opacity,
            )
    
    return doc
