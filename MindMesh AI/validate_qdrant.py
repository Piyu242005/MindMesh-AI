"""
validate_qdrant.py — MindMesh AI
Run this after preprocessing to verify the full Qdrant integration.

Usage:
    cd "MindMesh AI"
    python validate_qdrant.py

Exit code: 0 = all passed, 1 = one or more failures.
"""

import sys
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import qdrant_helper as qh

load_dotenv()

PASS = "✓"
FAIL = "✗"
results: list[bool] = []


def check(label: str, fn) -> bool:
    """Run fn(), print result, append to results. Returns pass/fail bool."""
    try:
        ok, msg = fn()
        symbol = PASS if ok else FAIL
        color  = "\033[92m" if ok else "\033[91m"   # green / red
        reset  = "\033[0m"
        print(f"  {color}[{symbol}]{reset} {label}: {msg}")
        results.append(ok)
        return ok
    except Exception as e:
        print(f"  \033[91m[{FAIL}]\033[0m {label}: ERROR — {e}")
        results.append(False)
        return False


print("\n" + "━" * 52)
print("  MindMesh AI — Qdrant Integration Validator")
print("━" * 52 + "\n")

# ── 1. Qdrant connection ───────────────────────────────────────────────────────
_client = None

def _test_connection():
    global _client
    _client = qh.get_client()
    ok, msg = qh.health_check(_client)
    return ok, msg

conn_ok = check("Qdrant connection", _test_connection)

if not conn_ok:
    print("\n\033[91m[ABORT] Cannot reach Qdrant. Check your .env credentials.\033[0m")
    sys.exit(1)

# ── 2. Collection exists ───────────────────────────────────────────────────────
def _test_collection():
    info = qh.collection_info(_client)
    exists = info["status"] not in ("error",)
    return exists, f"'{qh.QDRANT_COLLECTION}' — status: {info['status']}"

check("Collection exists", _test_collection)

# ── 3. Vector count > 0 ───────────────────────────────────────────────────────
def _test_vector_count():
    info = qh.collection_info(_client)
    count = info["vector_count"]
    ok = count > 0
    msg = f"{count:,} vectors stored"
    if not ok:
        msg += " — run preprocess_json.py to populate"
    return ok, msg

check("Vector count > 0", _test_vector_count)

# ── 4. Search returns results ─────────────────────────────────────────────────
def _test_search():
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    vec = model.encode(
        ["What is CSS and how do I use it?"],
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()[0]
    hits = qh.search(_client, vec, top_k=3)
    ok  = len(hits) > 0
    msg = f"returned {len(hits)} results"
    if hits:
        msg += f" (top score: {hits[0]['score']:.4f}, title: \"{hits[0].get('title','?')}\")"
    return ok, msg

check("Search functionality", _test_search)

# ── 5. Upload + delete test point ─────────────────────────────────────────────
def _test_upload_delete():
    from qdrant_client.models import PointStruct, PointIdsList

    TEST_ID     = 2_147_483_647          # max int32 — won't clash with real IDs
    TEST_VECTOR = [0.01] * qh.VECTOR_SIZE
    TEST_PAYLOAD = {
        "text":  "_validation test — safe to ignore",
        "title": "_test",
        "number": "0",
        "start": 0.0,
        "end":   0.0,
    }

    # Upsert
    _client.upsert(
        collection_name=qh.QDRANT_COLLECTION,
        points=[PointStruct(id=TEST_ID, vector=TEST_VECTOR, payload=TEST_PAYLOAD)],
        wait=True,
    )
    # Delete
    _client.delete(
        collection_name=qh.QDRANT_COLLECTION,
        points_selector=PointIdsList(points=[TEST_ID]),
        wait=True,
    )
    return True, "test point upserted and deleted successfully"

check("Upload / delete test", _test_upload_delete)

# ── Summary ───────────────────────────────────────────────────────────────────
passed = sum(results)
total  = len(results)
all_ok = passed == total

print(f"\n{'━' * 52}")
print(f"  Result: {passed}/{total} checks passed")
if all_ok:
    print("  \033[92m🎉 MindMesh AI Qdrant integration is fully operational!\033[0m")
else:
    print("  \033[93m⚠️  Some checks failed. Review the output above.\033[0m")
print("━" * 52 + "\n")

sys.exit(0 if all_ok else 1)
