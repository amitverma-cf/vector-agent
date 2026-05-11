"""
Phase 6: Assembly Stage (Iterative)

Python backend computes absolute coordinates from relative bounding boxes.
Maps 100x100 local component geometry to global canvas coordinates.
"""

from src.models.schema import SceneDocument, ComponentNode, Transform


def assemble_stage(doc: SceneDocument) -> SceneDocument:
    """
    Phase 6: Assembly Stage
    
    Traverses the component tree and computes absolute transforms.
    """
    def compute_transform(node_id, parent_bbox=(0, 0, 512, 512)):
        node = doc.nodes[node_id]
        if not isinstance(node, ComponentNode):
            return

        # parent_bbox is (x, y, w, h) in global units
        px, py, pw, ph = parent_bbox
        
        if node.layout_box is None:
            raise RuntimeError(f"Component {node.id} has no layout_box")

        # Layout box in percentages (0-100)
        lx = node.layout_box.x
        ly = node.layout_box.y
        lw = node.layout_box.w
        lh = node.layout_box.h
        
        # Map percentages to absolute units relative to parent
        abs_x = px + (lx / 100.0) * pw
        abs_y = py + (ly / 100.0) * ph
        abs_w = (lw / 100.0) * pw
        abs_h = (lh / 100.0) * ph
        
        # Transform maps normalized 100x100 space to this absolute box
        # Scale: 100 -> abs_w, 100 -> abs_h => abs_w/100, abs_h/100
        node.transform = Transform(
            tx=abs_x,
            ty=abs_y,
            sx=abs_w / 100.0,
            sy=abs_h / 100.0,
        )
        
        # Recurse for children
        current_bbox = (abs_x, abs_y, abs_w, abs_h)
        for child_id in node.children:
            compute_transform(child_id, current_bbox)

    # Start from root nodes (no parent_id)
    roots = [node_id for node_id, node in doc.nodes.items() if node.parent_id is None]
    for root_id in roots:
        compute_transform(root_id)

    return doc
