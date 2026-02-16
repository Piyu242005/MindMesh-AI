"""Evaluate retrieval quality using the eval dataset."""

import json
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search import HybridSearchEngine
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG.eval")


def evaluate(eval_file: str = "tests/eval_dataset.json", top_k: int = 5):
    """Run evaluation and compute precision@k metrics."""
    with open(eval_file, "r") as f:
        eval_data = json.load(f)

    engine = HybridSearchEngine(use_reranker=True)

    total = len(eval_data["test_cases"])
    hits = 0
    keyword_hits = 0
    results_detail = []

    for tc in eval_data["test_cases"]:
        query = tc["query"]
        expected_videos = set(tc["expected_video_numbers"])
        expected_keywords = [kw.lower() for kw in tc["expected_keywords"]]

        results = engine.search(query, top_k=top_k)
        retrieved_videos = {str(r["number"]) for r in results}
        retrieved_text = " ".join(r["text"].lower() for r in results)

        # Check video number match
        video_match = bool(expected_videos & retrieved_videos)
        if video_match:
            hits += 1

        # Check keyword coverage
        kw_found = sum(1 for kw in expected_keywords if kw in retrieved_text)
        kw_coverage = kw_found / len(expected_keywords) if expected_keywords else 0
        keyword_hits += kw_coverage

        status = "✅" if video_match else "❌"
        results_detail.append(
            {
                "id": tc["id"],
                "status": status,
                "query": query,
                "expected": list(expected_videos),
                "retrieved": list(retrieved_videos),
                "keyword_coverage": f"{kw_coverage:.0%}",
            }
        )

        logger.info(
            "%s Q%d: '%s' | Expected: %s | Got: %s | Keywords: %s",
            status,
            tc["id"],
            query[:50],
            expected_videos,
            retrieved_videos,
            f"{kw_coverage:.0%}",
        )

    precision = hits / total if total else 0
    avg_kw_coverage = keyword_hits / total if total else 0

    print("\n" + "=" * 60)
    print(f"EVALUATION RESULTS")
    print(f"=" * 60)
    print(f"Video Precision@{top_k}: {precision:.1%} ({hits}/{total})")
    print(f"Avg Keyword Coverage:   {avg_kw_coverage:.1%}")
    print(f"=" * 60)

    # Save detailed results
    with open("eval_results.json", "w") as f:
        json.dump(
            {
                "precision_at_k": precision,
                "avg_keyword_coverage": avg_kw_coverage,
                "top_k": top_k,
                "details": results_detail,
            },
            f,
            indent=2,
        )
    print("Detailed results saved to eval_results.json")


if __name__ == "__main__":
    evaluate()
