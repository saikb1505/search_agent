# services/salesql_client.py
import os
from typing import Any, Dict, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

# Try a few common env var names; prefer SALESQL_API_KEY
SALESQL_API_KEY = (
    os.getenv("SALESQL_API_KEY")
    or os.getenv("SALESQL_TOKEN")
    or os.getenv("SALESQL_KEY")
)

API_BASE = "https://api-public.salesql.com/v1"


class SalesQLError(Exception):
    pass


def _auth_headers() -> Dict[str, str]:
    if not SALESQL_API_KEY:
        raise SalesQLError(
            "Missing SalesQL API key. Set SALESQL_API_KEY in your environment (.env)."
        )
    return {"Authorization": f"Bearer {SALESQL_API_KEY}"}


def _normalize_url(linkedin_url: str) -> str:
    # Basic normalization: strip query/fragment and whitespace
    url = linkedin_url.strip()
    if "?" in url:
        url = url.split("?", 1)[0]
    if "#" in url:
        url = url.split("#", 1)[0]
    # Remove trailing slashes
    while url.endswith("/"):
        url = url[:-1]
    return url


async def enrich_person_by_linkedin_url(linkedin_url: str) -> Dict[str, Any]:
    """Call SalesQL 'persons/enrich' by LinkedIn URL.
    Returns parsed JSON on 200, a dict with _not_found=True on 404,
    otherwise raises SalesQLError.
    """
    url = f"{API_BASE}/persons/enrich/"
    params = {"linkedin_url": _normalize_url(linkedin_url)}
    headers = _auth_headers()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            # Not found is a valid outcome
            return {"_not_found": True, "_status_code": 404, "_message": "No person found"}

        # Try to extract error payload
        try:
            payload = resp.json()
        except Exception:
            payload = {"text": resp.text}
        raise SalesQLError(f"SalesQL error {resp.status_code}: {payload}")
