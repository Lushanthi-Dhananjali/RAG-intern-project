import os
import sys
from typing import List, Dict, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from app.core.vector_store import ChromaVectorStore
except ModuleNotFoundError:
    try:
        from core.vector_store import ChromaVectorStore
    except ModuleNotFoundError:
        from vector_store import ChromaVectorStore

try:
    from app.services.search_engine import BingSearchEngine
except ModuleNotFoundError:
    try:
        from services.search_engine import BingSearchEngine
    except ModuleNotFoundError:
        from search_engine import BingSearchEngine


class HybridRAGRetriever:
    """
    Hybrid Retriever combining ChromaDB local vector search with
    Bing Web Search API fallback when relevance thresholds are not met.
    """

    def __init__(self, score_threshold: float = 0.35):
        """
        :param score_threshold: Cosine distance threshold (lower is closer/better).
                                If best distance > threshold, trigger web fallback.
        """
        self.vector_db = ChromaVectorStore(embedding_provider="openai")
        self.bing_search = BingSearchEngine()
        self.score_threshold = score_threshold

    def retrieve_context(
            self,
            query: str,
            subject: Optional[str] = "Civic Education",
            grade_level: Optional[str] = None,
            top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieves context from ChromaDB, triggering Bing search if local scores fall below target quality.
        """
        print(f"\n🔎 Executing Hybrid Retrieval for Query: '{query}'")

        # 1. Search ChromaDB Vector Database
        chroma_res = self.vector_db.search_with_filters(
            query=query,
            subject=subject,
            grade_level=grade_level,
            n_results=top_k
        )

        documents = chroma_res.get("documents", [[]])[0]
        distances = chroma_res.get("distances", [[]])[0] if "distances" in chroma_res else []
        metadatas = chroma_res.get("metadatas", [[]])[0]

        retrieved_contexts = []
        is_fallback_triggered = False

        # Evaluate quality of ChromaDB matches
        best_distance = distances[0] if distances else 1.0

        # Check if local ChromaDB results are strong enough
        if documents and best_distance <= self.score_threshold:
            print(
                f"✅ Strong ChromaDB matches found (Best distance: {best_distance:.4f} <= Threshold {self.score_threshold})")
            for doc, meta in zip(documents, metadatas):
                retrieved_contexts.append({
                    "source": "ChromaDB (Local)",
                    "segment_type": meta.get("segment_type", "unknown"),
                    "content": doc
                })
        else:
            print(
                f"⚠️ ChromaDB results insufficient (Best distance: {best_distance:.4f} > Threshold {self.score_threshold}).")
            print("🌐 Triggering Fallback: Bing Web Search API...")
            is_fallback_triggered = True

            # Execute Bing Search
            search_query = f"{subject or ''} {grade_level or ''} {query}".strip()
            web_results = self.bing_search.search(search_query, count=top_k)

            for item in web_results:
                retrieved_contexts.append({
                    "source": f"Bing Search ({item['url']})",
                    "segment_type": "web_page_snippet",
                    "content": f"Title: {item['title']}\nSnippet: {item['snippet']}"
                })

        return {
            "query": query,
            "fallback_used": is_fallback_triggered,
            "retrieved_items_count": len(retrieved_contexts),
            "contexts": retrieved_contexts
        }


# --- Demonstration Run ---
if __name__ == "__main__":
    retriever = HybridRAGRetriever(score_threshold=0.35)

    # Test query that should fail local ChromaDB (if missing) and trigger Bing Search
    result = retriever.retrieve_context(
        query="Constitutional duties of democratic citizens in elections",
        subject="Civic Education",
        grade_level="Grade 9"
    )

    print("\n--- Final Hybrid Retrieval Context Output ---")
    print(f"Fallback Triggered: {result['fallback_used']}")
    print(f"Context Count: {result['retrieved_items_count']}")
    for idx, ctx in enumerate(result['contexts'], 1):
        print(f"\n[{idx}] Source: {ctx['source']}")
        print(f"    Content: {ctx['content'][:150]}...")