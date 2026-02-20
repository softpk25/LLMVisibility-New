"""Debug script to check Ollama connection and models"""

import ollama
import json

print("Testing Ollama connection...")
print("=" * 60)

try:
    response = ollama.list()
    print(f"Response type: {type(response)}")
    print(f"\nFull response:")
    print(json.dumps(response, indent=2, default=str))

    print("\n" + "=" * 60)

    if isinstance(response, dict):
        print(f"Keys in response: {response.keys()}")
        if 'models' in response:
            print(f"Number of models: {len(response['models'])}")
            print("\nModels:")
            for model in response['models']:
                print(f"  - {model}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
