"""
Step-by-step helper to check saved image analysis JSON files.
Run: python check_json.py
"""
import json
from pathlib import Path

def main():
    base = Path(__file__).parent

    # Step 1: Check generated/ folder (JSON next to each generated image)
    generated_dir = base / "generated"
    if generated_dir.exists():
        json_files = sorted(generated_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        print("=== GENERATED (creative generation) ===\n")
        if not json_files:
            print("  No JSON files yet. Generate an image via /api/generate-creative first.\n")
        else:
            for i, path in enumerate(json_files[:5], 1):
                print(f"  {i}. {path.name}")
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    print(f"     Keys: {list(data.keys())}")
                    if "visual_dna" in data:
                        print(f"     visual_dna.style: {data['visual_dna'].get('style', 'N/A')}")
                    if "prompt_reconstruction" in data:
                        print(f"     prompt_reconstruction: {data['prompt_reconstruction'][:60]}...")
                    print()
                except Exception as e:
                    print(f"     Error reading: {e}\n")
    else:
        print("=== GENERATED ===\n  Folder 'generated' not found.\n")

    # Step 2: Check image_analysis/ folder (analyzed uploads)
    analysis_dir = base / "image_analysis"
    if analysis_dir.exists():
        json_files = sorted(analysis_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        print("=== IMAGE_ANALYSIS (uploaded image analysis) ===\n")
        if not json_files:
            print("  No JSON files yet. Upload an image via /api/analyze-image first.\n")
        else:
            for i, path in enumerate(json_files[:5], 1):
                print(f"  {i}. {path.name}")
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    print(f"     Keys: {list(data.keys())}")
                    if "analysis" in data:
                        a = data["analysis"]
                        print(f"     analysis keys: {list(a.keys()) if isinstance(a, dict) else 'N/A'}")
                        if isinstance(a, dict) and "visual_dna" in a:
                            print(f"     visual_dna.style: {a['visual_dna'].get('style', 'N/A')}")
                    print()
                except Exception as e:
                    print(f"     Error reading: {e}\n")
    else:
        print("=== IMAGE_ANALYSIS ===\n  Folder 'image_analysis' not found.\n")

    # Step 3: Print full content of most recent generated JSON (if any)
    if generated_dir.exists():
        latest = sorted(generated_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if latest:
            print("=== FULL LATEST GENERATED JSON ===\n")
            print(json.dumps(json.loads(latest[0].read_text(encoding="utf-8")), indent=2, ensure_ascii=False))
            print()

if __name__ == "__main__":
    main()
