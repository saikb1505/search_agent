import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

async def serper_linkedin_search(query: str, num_results: int = 20) -> list[dict]:
    """
    Search Google via Serper.dev API and return only LinkedIn profile results.
    """
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": query, "num": num_results}

    results = []
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"[Serper LinkedIn Search] Error for query='{query}': {e}")
            return []

    # Extract organic results and filter for LinkedIn profiles
    for item in data.get("organic", []):
        link = item.get("link", "")
        if "linkedin.com/in" in link.lower():
            results.append({
                "title": item.get("title"),
                "link": link,
                "snippet": item.get("snippet", "")
            })

    return results
