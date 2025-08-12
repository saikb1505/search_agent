# api/salesql_routes.py
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
import asyncio

from db.salesql_results import (
    get_linkedin_urls_for_search_id,
    get_existing_linkedin_urls,
    save_salesql_person,
)
from services.salesql_client import enrich_person_by_linkedin_url, SalesQLError

router = APIRouter(prefix="/salesql", tags=["SalesQL"])


@router.post("/enrich/{search_id}")
async def enrich_salesql_for_search(search_id: int, max_profiles: Optional[int] = None) -> Dict[str, Any]:
    """
    For the given search_id, read LinkedIn profile URLs from google_search_results,
    call SalesQL enrichment API for each, and save to salesql_enriched_people.
    Skips URLs already enriched for this search_id.
    """
    rows = await get_linkedin_urls_for_search_id(search_id)
    found = len(rows)

    if found == 0:
        # Not a hard error, but signal nothing to do
        return {
            "search_id": search_id,
            "found_urls": 0,
            "already_enriched": 0,
            "enriched": 0,
            "not_found": 0,
            "failed": 0,
            "failures": [],
        }

    already = await get_existing_linkedin_urls(search_id)
    to_process = [r for r in rows if r["link"] not in already]

    if max_profiles is not None and max_profiles > 0:
        to_process = to_process[:max_profiles]

    summary = {
        "search_id": search_id,
        "found_urls": found,
        "already_enriched": found - len(to_process),
        "enriched": 0,
        "not_found": 0,
        "failed": 0,
        "failures": [],
    }

    for r in to_process:
        url = r["link"]
        try:
            payload = await enrich_person_by_linkedin_url(url)
            if payload.get("_not_found"):
                summary["not_found"] += 1
                continue
            await save_salesql_person(search_id, r["id"], url, payload)
            summary["enriched"] += 1
        except SalesQLError as e:
            summary["failed"] += 1
            summary["failures"].append({"linkedin_url": url, "error": str(e)})
        except Exception as e:
            summary["failed"] += 1
            summary["failures"].append({"linkedin_url": url, "error": f"Unexpected: {e}"})
        # Gentle rate limiting
        await asyncio.sleep(0.25)

    return summary
