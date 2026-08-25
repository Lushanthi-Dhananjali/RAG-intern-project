import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class BingSearchEngine:
    """
    Bing Web Search API wrapper to retrieve live web results
    for RAG fallback augmentation.
    """

    def __init__(self):
        self.api_key = os.getenv("BING_SEARCH_API_KEY")
        self.endpoint = os.getenv("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")

    def search(self, query: str, count: int = 3) -> List[Dict[str, str]]:
        """
        Executes web search query against Bing Search API.
        """
        if not self.api_key or self.api_key.startswith("your_"):
            print("⚠️ Bing API Key missing or invalid. Returning empty search fallback.")
            return []

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {
            "q": query,
            "count": count,
            "textDecorations": False,
            "textFormat": "RAW"
        }

        try:
            response = requests.get(self.endpoint, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            search_results = response.json()

            results = []
            if "webPages" in search_results and "value" in search_results["webPages"]:
                for page in search_results["webPages"]["value"]:
                    results.append({
                        "title": page.get("name", ""),
                        "snippet": page.get("snippet", ""),
                        "url": page.get("url", ""),
                        "source": "Bing Web Search"
                    })
            return results

        except Exception as e:
            print(f"❌ Bing Search Request Failed: {e}")
            return []


# --- Simple Test Execution ---
if __name__ == "__main__":
    engine = BingSearchEngine()
    test_query = "Civic Education Grade 9 fundamental rights and duties lesson plan"
    print(f"🔍 Testing Bing Search for: '{test_query}'")

    web_results = engine.search(test_query, count=2)
    for idx, res in enumerate(web_results, 1):
        print(f"\n[{idx}] {res['title']}\n    URL: {res['url']}\n    Snippet: {res['snippet'][:120]}...")