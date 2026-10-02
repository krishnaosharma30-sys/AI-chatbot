from typing import List, Dict
from duckduckgo_search import DDGS

class WebSearchService:
    def __init__(self):
        pass

    async def search(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Perform a web search using DuckDuckGo.
        Returns a list of dicts with 'title', 'href', and 'body' (snippet).
        """
        try:
            results = []
            with DDGS() as ddgs:
                ddgs_gen = ddgs.text(query, max_results=max_results)
                for r in ddgs_gen:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "content": r.get("body", "")
                    })
            return results
        except Exception as e:
            print(f"WebSearchService Error: {e}")
            return []

web_search_service = WebSearchService()
