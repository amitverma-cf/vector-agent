"""Compile a styled scene document into safe static SVG bytes."""

from lxml import etree

from src.geometry.svg_elements import SVG_NS, geometry_to_element, svg_tag
from src.models.schema import BackgroundType, ComponentNode, GroupNode, SceneDocument, Transform


def _apply_transform(element: etree._Element, transform: Transform) -> None:
    parts = []
    if transform.tx != 0 or transform.ty != 0:
        parts.append(f"translate({transform.tx:g} {transform.ty:g})")
    if transform.sx != 1 or transform.sy != 1:
        parts.append(f"scale({transform.sx:g} {transform.sy:g})")
    if transform.rotate != 0:
        parts.append(f"rotate({transform.rotate:g})")

    if parts:
        element.set("transform", " ".join(parts))


def compile_stage(doc: SceneDocument) -> bytes:
    width, height = doc.canvas
    svg = etree.Element(
        svg_tag("svg"),
        nsmap={None: SVG_NS},
        attrib={
            "viewBox": f"0 0 {width:g} {height:g}",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
        },
    )

    if doc.background == BackgroundType.SOLID_LIGHT:
        etree.SubElement(
            svg,
            svg_tag("rect"),
            width=f"{width:g}",
            height=f"{height:g}",
            fill="#F4F6FA",
        )
    elif doc.background == BackgroundType.SOLID_DARK:
        etree.SubElement(
            svg,
            svg_tag("rect"),
            width=f"{width:g}",
            height=f"{height:g}",
            fill="#0A0F1A",
        )

    def emit_node(parent_element: etree._Element, node_id: str) -> None:
        node = doc.nodes.get(node_id)
        if node is None:
            raise RuntimeError(f"Cannot compile missing node: {node_id}")

        if isinstance(node, GroupNode):
            group = etree.SubElement(parent_element, svg_tag("g"), id=node.id)
            _apply_transform(group, node.transform)
            for child_id in node.children:
                emit_node(group, child_id)
            return

        if isinstance(node, ComponentNode):
            if node.render_intent == "container":
                for child_id in node.children:
                    emit_node(parent_element, child_id)
                return
            if node.geometry is None:
                raise RuntimeError(f"Component {node.id} has no geometry")
            element = geometry_to_element(node.geometry, node.id, node.resolved_style)
            _apply_transform(element, node.transform)
            parent_element.append(element)
            for child_id in node.children:
                emit_node(parent_element, child_id)
            return

        raise RuntimeError(f"Unsupported node kind for compile: {node.kind}")

    root_nodes = [node_id for node_id, node in doc.nodes.items() if node.parent_id is None]
    for root_id in root_nodes:
        emit_node(svg, root_id)

    return etree.tostring(svg, encoding="utf-8", xml_declaration=False)
