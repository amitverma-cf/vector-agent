from src.pipeline import run_pipeline

def test_prompt(prompt):
    print("=" * 60)
    print(f"Testing: '{prompt}'")
    print("=" * 60)
    result = run_pipeline(prompt)
    print(f'✓ Pipeline executed')
    print(f'  Recipe: {result.scene_document.style_recipe}')
    print(f'  Components: {len(result.scene_document.nodes)}')
    print(f'  Validation: {result.validation_report.overall_status}')
    print(f'  Notes: {result.validation_report.notes}')
    print(f'  Component tree:')
    for node_id, node in result.scene_document.nodes.items():
        if node.kind == "component":
            parent = node.parent_id or "Root"
            print(f'    [{node_id}] {node.name} (Parent: {parent}, Role: {node.role.value})')
    print()

if __name__ == "__main__":
    test_prompt("a friendly robot")
    test_prompt("a mystical unicorn")
    test_prompt("a glowing neon gear")
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
