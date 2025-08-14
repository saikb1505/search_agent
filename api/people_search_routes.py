# api/people_search_routes.py
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from db.people_search import search_people_by_keyword

router = APIRouter(prefix="/people", tags=["People Search"])

class PeopleSearchResponse(BaseModel):
    q: str
    location: Optional[str] = None
    limit: int
    offset: int
    count: int
    items: List[Dict[str, Any]] = Field(default_factory=list)

@router.get("/search", response_model=PeopleSearchResponse, summary="Search people by keyword (e.g., q=java)")
async def people_search(
    q: str = Query(..., description="Keyword like 'java'"),
    location: Optional[str] = Query(None, description="Optional location filter (e.g., Hyderabad)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        items = await search_people_by_keyword(q=q, location=location, limit=limit, offset=offset)
        return PeopleSearchResponse(q=q, location=location, limit=limit, offset=offset, count=len(items), items=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"People search failed: {e}")
