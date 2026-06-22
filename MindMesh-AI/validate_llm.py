"""
validate_llm.py — MindMesh AI
Simple script to test both Gemini and Groq integrations via the LLM Manager.
"""

import sys
from pathlib import Path

# Ensure root is in path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.llm_manager import check_providers, generate_response

def run_tests():
    print("=" * 50)
    print("MindMesh AI — LLM Gateway Validation")
    print("=" * 50 + "\n")

    status = check_providers()
    print("[1] Authentication Status:")
    for prov, (is_up, msg) in status.items():
        print(f"  - {prov.title():<8} : {'✅' if is_up else '❌'} {msg}")

    print("\n[2] Inference Tests:")
    prompt = "Reply with exactly the words: Hello MindMesh"

    for prov in ["gemini", "groq"]:
        if status.get(prov, (False,))[0]:
            print(f"  - Testing {prov.title()}...")
            try:
                # Default models are set in env or llm_manager
                response = generate_response(prompt, provider=prov, stream=False, fallback_allowed=False)
                print(f"    ✓ Success! Response: '{response}'")
            except Exception as e:
                print(f"    ✗ Failed! Error: {e}")
        else:
            print(f"  - Skipping {prov.title()} (Not configured)")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    run_tests()
