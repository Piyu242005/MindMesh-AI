import os
import json
import time
from pathlib import Path
from duckduckgo_search import DDGS

CACHE_FILE = Path(__file__).parent.parent / "web_cache.json"
CACHE_DURATION = 24 * 3600  # 24 hours

def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_cache(cache_data: dict):
    try:
        CACHE_FILE.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
    except Exception:
        pass

def get_trust_score(url: str) -> int:
    """Give higher priority to high-trust domains."""
    url_lower = url.lower()
    if ".edu" in url_lower or ".gov" in url_lower:
        return 10
    if "docs" in url_lower or "documentation" in url_lower:
        return 8
    if "mozilla.org" in url_lower or "python.org" in url_lower or "fastapi.tiangolo.com" in url_lower:
        return 8
    if "qdrant.tech" in url_lower or "developer" in url_lower:
        return 8
    if "github.com" in url_lower or "stackoverflow.com" in url_lower:
        return 6
    if "forum" in url_lower or "reddit.com" in url_lower:
        return 2
    return 5

def search_web(query: str, max_results: int = 3) -> list:
    cache = _load_cache()
    now = time.time()
    
    # Check cache
    if query in cache:
        entry = cache[query]
        if now - entry["timestamp"] < CACHE_DURATION:
            return entry["results"]
            
    # Perform search
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
            
        # Score and rank
        for r in results:
            r["trust_score"] = get_trust_score(r.get("href", ""))
            
        results = sorted(results, key=lambda x: x["trust_score"], reverse=True)[:max_results]
        
        # Save to cache
        cache[query] = {
            "timestamp": now,
            "results": results
        }
        _save_cache(cache)
        
        return results
    except Exception as e:
        print(f"Web search error: {e}")
        return []
