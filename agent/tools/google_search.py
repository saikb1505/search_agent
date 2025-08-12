# agent/tools/google_search.py

import os
import httpx

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

async def google_search(query: str, max_results: int = 100) -> list[dict]:
  """
  Fetches up to 100 results from Google Custom Search API for a given query.
  Automatically paginates using 'start' parameter (10 results per request).
  """

  url = "https://www.googleapis.com/customsearch/v1"
  results = []
  results_per_page = 10

  async with httpx.AsyncClient() as client:
    for start in range(1, max_results + 1, results_per_page):
      params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": results_per_page,
        "start": start
      }

      try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
      except Exception as e:
        print(f"[Google Search] Failed at start={start} for query='{query}': {e}")
        break

      items = data.get("items", [])
      if not items:
        break  # No more results

      for item in items:
        results.append({
          "title": item.get("title"),
          "link": item.get("link"),
          "snippet": item.get("snippet", "")
        })

      if len(items) < results_per_page:
        break  # Last page

  return results