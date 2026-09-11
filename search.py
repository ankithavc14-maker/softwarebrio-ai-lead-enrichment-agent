import httpx


async def tavily_leadership_search(api_key: str, domain: str, query: str) -> list[str]:
    """Optional bonus integration for external LinkedIn discovery."""
    if not api_key:
        return []

    payload = {
        "api_key": api_key,
        "query": f"site:linkedin.com/in {query} {domain}",
        "search_depth": "basic",
        "max_results": 5,
        "include_domains": ["linkedin.com"],
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        urls = []
        for item in data.get("results", []):
            url = item.get("url")
            if url and "linkedin.com/in/" in url:
                urls.append(url)
        return sorted(set(urls))
    except Exception:
        # External search is a bonus path, never a reason to fail enrichment.
        return []
