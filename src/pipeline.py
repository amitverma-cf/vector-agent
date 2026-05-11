"""
Main Pipeline Orchestrator (Iterative Edition)

Coordinates the multi-loop vector graphics compilation pipeline.
Decomposes subject into components, generates paths iteratively, 
assembles using relative positioning, and refines for quality.
"""

from src.models.schema import (
    PipelineOutput, SceneDocument, ComponentNode
)
from src.stages.brief_stage import brief_stage
from src.stages.route_stage import route_stage
from src.stages.plan_stage import plan_stage
from src.stages.decompose_stage import decompose_stage
from src.stages.layout_stage import layout_stage
from src.stages.generate_stage import generate_component_geometry
from src.stages.assemble_stage import assemble_stage
from src.stages.style_stage import style_resolver
from src.stages.compile_stage import compile_stage
from src.stages.refine_stage import refine_stage
from src.stages.validate_stage import validate_stage
from src.utils.llm import get_default_llm_client


def run_pipeline(
    prompt: str,
    llm_client=None,
    render_client=None,
    max_refinement_loops: int | None = None,
) -> PipelineOutput:
    """
    Iterative pipeline: Decomposition -> Iterative Generation -> Assembly -> Refinement.
    """
    
    notes = []
    if llm_client is None:
        llm_client = get_default_llm_client()
    if llm_client is None:
        raise RuntimeError("LLM client required. Set LLM_API_KEY/OPENAI_API_KEY and LLM_MODEL.")
    
    print(f"--- Stage 1: Briefing '{prompt}' ---")
    brief = brief_stage(prompt, llm_client)
    notes.extend(brief.notes)
    print(f"    Subject: {brief.subject}, Type: {brief.output_type}")

    print(f"--- Stage 2: Routing '{brief.subject}' ---")
    route_stage(brief, llm_client)
    
    print(f"--- Stage 3: Planning composition '{brief.subject}' ---")
    plan = plan_stage(brief, llm_client)
    notes.append(plan.reasoning)

    print(f"--- Stage 4: Decomposing '{brief.subject}' ---")
    comp_plan = decompose_stage(brief, plan, llm_client)
    notes.append(comp_plan.reasoning)
    print(f"    Decomposed into {len(comp_plan.components)} components.")
    
    # Initialize SceneDocument
    doc = SceneDocument(
        canvas=(512, 512),
        style_recipe=brief.style_recipe,
        background=brief.background,
        palette_hint=brief.palette_hint,
        nodes={},
        node_order=[],
    )
    
    # Populate document with planned components
    for comp in comp_plan.components:
        doc.nodes[comp.id] = ComponentNode(
            id=comp.id,
            name=comp.name,
            parent_id=comp.parent_id,
            role=comp.role,
            priority=comp.priority,
            render_intent=comp.render_intent,
        )
        doc.node_order.append(comp.id)
    
    # Build parent-child relationships in the nodes (for tree traversal)
    for node_id, node in doc.nodes.items():
        if node.parent_id and node.parent_id in doc.nodes:
            doc.nodes[node.parent_id].children.append(node_id)

    print(f"--- Stage 5: Laying out components ---")
    doc = layout_stage(doc, plan, llm_client)

    # 3. Iterative Generation Stage
    print(f"--- Stage 6: Generating component geometry ---")
    context_summary = f"a high-quality {brief.output_type.value} of a {brief.subject}"
    for i, (node_id, node) in enumerate(doc.nodes.items()):
        if isinstance(node, ComponentNode):
            if node.render_intent == "container":
                print(f"    [{i+1}/{len(doc.nodes)}] Skipping container {node.name} ({node.id})...")
                continue
            print(f"    [{i+1}/{len(doc.nodes)}] Generating {node.name} ({node.id})...")
            geometry_res = generate_component_geometry(node, context_summary, llm_client)
            node.geometry = geometry_res.geometry

    # 4. Refinement Loop
    refinement_loop = 0
    while True:
        refinement_loop += 1
        print(f"--- Stage 7: Refinement Loop {refinement_loop} ---")
        # Assemble (compute absolute transforms)
        doc = assemble_stage(doc)
        
        # Style (resolve colors)
        doc = style_resolver(doc)
        
        # Refine
        print(f"    Reviewing composition...")
        patches = refine_stage(doc, llm_client)
        if not patches:
            print(f"    No patches issued.")
            break

        if max_refinement_loops is not None and refinement_loop > max_refinement_loops:
            raise RuntimeError("Refinement produced patches after the configured loop limit")
            
        print(f"    Applying {len(patches)} patches...")
        for patch in patches:
            if patch.component_id not in doc.nodes:
                continue
            target = doc.nodes[patch.component_id]
            if not isinstance(target, ComponentNode):
                continue
                
            if patch.type == "update_layout":
                target.layout_box = patch.params
            elif patch.type == "regenerate_geometry":
                if target.render_intent == "container":
                    raise RuntimeError(f"Cannot regenerate geometry for container component {target.id}")
                geometry_res = generate_component_geometry(target, context_summary, llm_client)
                target.geometry = geometry_res.geometry
        
        notes.append(f"Refinement loop {refinement_loop} completed with {len(patches)} patches.")

    # Final Assembly and Style
    doc = assemble_stage(doc)
    doc = style_resolver(doc)
    
    # 5. Compile Stage
    print(f"--- Stage 8: Compiling final SVG ---")
    svg_bytes = compile_stage(doc)
    
    # 7. Validate Stage
    validation_report = validate_stage(doc, svg_bytes, notes)
    if validation_report.overall_status != "pass":
        details = "; ".join(check.details or check.check_name for check in validation_report.checks if check.status != "pass")
        raise RuntimeError(f"Validation failed: {details}")
    
    return PipelineOutput(
        svg_bytes=svg_bytes,
        scene_document=doc,
        validation_report=validation_report,
    )


if __name__ == "__main__":
    prompt = "a friendly robot"
    result = run_pipeline(prompt)
    print(f"Pipeline completed with {len(result.scene_document.nodes)} components.")
    print(f"Notes: {result.validation_report.notes}")
