"""Stage 4: Process user queries with hybrid search and LLM response generation."""

import sys
import logging
import argparse

from config import Config
from utils import check_ollama_availability, inference, logger
from search import HybridSearchEngine
from prompts import build_query_prompt


def process_query(
    query: str,
    engine: HybridSearchEngine,
    model: str = None,
    top_k: int = None,
) -> str:
    """
    Process a single query through the full RAG pipeline.
    Returns the LLM response.
    """
    model = model or Config.LLM_MODEL
    top_k = top_k or Config.TOP_K_RESULTS

    # Step 1: Hybrid search
    results = engine.search(query, top_k=top_k)

    if not results:
        return "I couldn't find any relevant content in the course videos for your question. Please try rephrasing or ask about a topic covered in the course."

    # Step 2: Build prompt
    prompt = build_query_prompt(query, results)

    # Save prompt for debugging
    try:
        with open("prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt)
    except Exception:
        pass

    # Step 3: Generate response
    response = inference(prompt, model=model)

    # Save response for debugging
    try:
        with open("response.txt", "w", encoding="utf-8") as f:
            f.write(response)
    except Exception:
        pass

    return response


def interactive_mode(engine: HybridSearchEngine, model: str = None):
    """Run in interactive CLI mode with conversation history."""
    print("\n" + "=" * 60)
    print("  RAG Course Assistant - Sigma Web Development")
    print("  Type 'quit' or 'exit' to stop. Type 'clear' to reset.")
    print("=" * 60 + "\n")

    conversation_history = []

    while True:
        try:
            query = input("\n📝 Ask a Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if query.lower() == "clear":
            conversation_history.clear()
            print("Conversation history cleared.")
            continue

        # Add context from conversation history for follow-up questions
        if conversation_history:
            enhanced_query = (
                f"Previous context: {conversation_history[-1]['query']} -> "
                f"{conversation_history[-1]['response'][:200]}... "
                f"New question: {query}"
            )
        else:
            enhanced_query = query

        print("\n🔍 Searching...")
        response = process_query(enhanced_query, engine, model=model)

        print(f"\n💡 Answer:\n{response}")

        conversation_history.append({"query": query, "response": response})


def main():
    parser = argparse.ArgumentParser(description="Query the RAG course assistant.")
    parser.add_argument("--query", "-q", type=str, help="Single query (non-interactive)")
    parser.add_argument("--model", "-m", type=str, default=Config.LLM_MODEL, help="LLM model")
    parser.add_argument("--top-k", "-k", type=int, default=Config.TOP_K_RESULTS, help="Results count")
    parser.add_argument(
        "--no-reranker", action="store_true", help="Disable cross-encoder reranking"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not check_ollama_availability():
        sys.exit(1)

    # Initialize search engine
    engine = HybridSearchEngine(use_reranker=not args.no_reranker)

    if args.query:
        response = process_query(args.query, engine, model=args.model, top_k=args.top_k)
        print(response)
    else:
        interactive_mode(engine, model=args.model)


if __name__ == "__main__":
    main()
