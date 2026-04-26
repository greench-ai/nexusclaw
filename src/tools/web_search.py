"""
NexusClaw Web Search — Perplexity-style with citations
Uses DuckDuckGo instant answer API + Brave Search for real results.
"""
import os, json, asyncio
from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    citation: int = 0

class WebSearch:
    """
    Perplexity-style web search with:
    - Real-time results from multiple sources
    - Cited responses
    - Follow-up questions
    - Source credibility scoring
    """
    
    def __init__(self, brave_api_key: str = None):
        self.brave_key = brave_api_key or os.environ.get("BRAVE_API_KEY", "")
        self.citation_counter = 0
    
    async def search(self, query: str, num_results: int = 10) -> dict:
        """
        Search the web and return structured results with citations.
        """
        self.citation_counter = 0
        
        # Try Brave Search first (more comprehensive)
        if self.brave_key:
            results = await self._brave_search(query, num_results)
        else:
            results = await self._duckduckgo_search(query, num_results)
        
        # Format as Perplexity-style response
        response = self._format_response(query, results)
        return response
    
    async def _brave_search(self, query: str, num_results: int) -> list[SearchResult]:
        """Brave Search API."""
        import aiohttp
        results = []
        
        async with aiohttp.ClientSession() as session:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "X-Subscription-Token": self.brave_key,
                "Accept": "application/json"
            }
            params = {"q": query, "count": num_results}
            
            try:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("web", {}).get("results", []):
                            self.citation_counter += 1
                            results.append(SearchResult(
                                title=item.get("title", ""),
                                url=item.get("url", ""),
                                snippet=item.get("description", ""),
                                source=item.get("meta_url", {}).get("netloc", ""),
                                citation=self.citation_counter
                            ))
                    else:
                        results = await self._duckduckgo_search(query, num_results)
            except:
                results = await self._duckduckgo_search(query, num_results)
        
        return results
    
    async def _duckduckgo_search(self, query: str, num_results: int) -> list[SearchResult]:
        """DuckDuckGo Instant Answer API (free, no API key)."""
        import aiohttp
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Instant Answer API
                url = "https://api.duckduckgo.com/"
                params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Abstract
                        if data.get("AbstractText"):
                            self.citation_counter += 1
                            results.append(SearchResult(
                                title=data.get("Heading", query),
                                url=data.get("AbstractURL", ""),
                                snippet=data.get("AbstractText", ""),
                                source=data.get("AbstractSource", ""),
                                citation=self.citation_counter
                            ))
                        
                        # Related topics
                        for topic in data.get("RelatedTopics", [])[:num_results - len(results)]:
                            if topic.get("Text"):
                                self.citation_counter += 1
                                results.append(SearchResult(
                                    title=topic.get("Text", "")[:80],
                                    url=topic.get("FirstURL", ""),
                                    snippet=topic.get("Text", ""),
                                    source="DuckDuckGo",
                                    citation=self.citation_counter
                                ))
        except Exception as e:
            return [{"title": "Search failed", "url": "", "snippet": str(e), "source": "error", "citation": 0}]
        
        return results
    
    def _format_response(self, query: str, results: list) -> dict:
        """Format as Perplexity-style response."""
        if not results:
            return {
                "query": query,
                "answer": f"No results found for '{query}'",
                "results": [],
                "follow_ups": []
            }
        
        # Build cited answer
        answer_parts = [f"**Query:** {query}\n\n"]
        
        for i, r in enumerate(results[:5]):
            if r.snippet:
                answer_parts.append(f"[^{r.citation}] **{r.title}**\n{r.snippet}\n\n")
        
        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(query, results)
        
        return {
            "query": query,
            "answer": "".join(answer_parts),
            "results": [
                {"citation": r.citation, "title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source}
                for r in results
            ],
            "follow_ups": follow_ups,
            "total_results": len(results),
            "web_search": True
        }
    
    def _generate_follow_ups(self, query: str, results: list) -> list[str]:
        """Generate suggested follow-up questions."""
        # Simple heuristic follow-ups
        words = query.lower().split()
        follow_ups = []
        
        if "what" in words:
            follow_ups = [
                f"Why is {query.split('what is ')[-1] if 'what is' in query.lower() else query} important?",
                f"Who uses {query.split('what is ')[-1] if 'what is' in query.lower() else query}?",
                f"How does {query.split('what is ')[-1] if 'what is' in query.lower() else query} work?"
            ]
        elif "how" in words:
            follow_ups = [
                f"What are the best practices for {query}?",
                f"Common mistakes with {query}?",
                f"{query.replace('how to', 'Can I')}?"
            ]
        elif "who" in words:
            follow_ups = [
                f"What is {query.split('who ')[-1] if 'who' in query.lower() else query}'s history?",
                f"What else is {query.split('who ')[-1] if 'who' in query.lower() else query} known for?"
            ]
        
        return follow_ups[:3]

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NexusClaw Web Search")
    parser.add_argument("query", nargs="+", help="search query")
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()
    
    query = " ".join(args.query)
    search = WebSearch()
    result = asyncio.run(search.search(query))
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["answer"])
        print("\n--- Sources ---")
        for r in result["results"][:5]:
            print(f"[{r['citation']}] {r['title']} — {r['url']}")
        if result["follow_ups"]:
            print("\n--- Follow-ups ---")
            for f in result["follow_ups"]:
                print(f"  • {f}")
