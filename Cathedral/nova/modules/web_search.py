#!/usr/bin/env python3
"""
Nova web search module.
DuckDuckGo search + page fetch + Wikipedia summaries.
Requires: pip install duckduckgo-search beautifulsoup4 --break-system-packages
"""

import json
import re
import urllib.request
import urllib.parse

try:
    from ddgs import DDGS
    _HAS_DDG = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        _HAS_DDG = True
    except ImportError:
        _HAS_DDG = False

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False


def search_web(query: str, max_results: int = 4) -> list:
    """Search DuckDuckGo. Returns list of {title, href, body}."""
    if not _HAS_DDG:
        return [{"error": "duckduckgo-search not installed — run: pip install duckduckgo-search --break-system-packages"}]
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return [{"error": str(e)}]


def fetch_page(url: str, max_chars: int = 3000) -> str:
    """Fetch a URL and return clean plain text."""
    if not _HAS_BS4:
        return ""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 Nova/1.0"}
        )
        html = urllib.request.urlopen(req, timeout=8).read()
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars]
    except Exception:
        return ""


def search_and_summarize(query: str, max_results: int = 3) -> dict:
    """
    Search DuckDuckGo and build a context string ready for LLM injection.
    Returns: {query, results, context, error?}
    """
    results = search_web(query, max_results)

    if results and "error" in results[0]:
        return {"error": results[0]["error"], "context": "", "results": [], "query": query}

    parts = []
    for r in results:
        title = r.get("title", "")
        body  = r.get("body", "")
        href  = r.get("href", "")
        parts.append(f"Source: {title}\nURL: {href}\n{body}")

    return {
        "query":   query,
        "results": results,
        "context": "\n\n---\n\n".join(parts),
    }


def wikipedia_summary(topic: str) -> dict:
    """Fetch a Wikipedia article summary via the REST API (no key needed)."""
    try:
        slug = urllib.parse.quote(topic.replace(" ", "_"))
        url  = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
        req  = urllib.request.Request(url, headers={"User-Agent": "Nova/1.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=8).read())
        return {
            "title":   data.get("title", topic),
            "summary": data.get("extract", ""),
            "url":     data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except Exception as e:
        return {"error": str(e), "title": topic, "summary": ""}
