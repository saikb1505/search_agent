# api/people_routes.py
from fastapi import APIRouter, Query
from typing import List, Optional, Literal
from models.schemas import PeopleSearchResponse, PeopleItem
from db.people_repo import search_people

router = APIRouter(tags=["People"])

@router.get("/people", response_model=PeopleSearchResponse, summary="List enriched people")
async def list_people(
    search_id: Optional[int] = None,
    q: Optional[str] = None,
    tech_stack: Optional[List[str]] = Query(default=None, alias="tech_stack"),
    locations: Optional[List[str]] = Query(default=None, alias="locations"),
    sort: Literal["recent", "name"] = "recent",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    records, total = await search_people(
        search_id=search_id,
        q=q,
        tech_stack=tech_stack or [],
        locations=locations or [],
        sort=sort,
        limit=limit,
        offset=offset,
    )
    items = [PeopleItem(**r) for r in records]
    return PeopleSearchResponse(
        q=q,
        search_id=search_id,
        tech_stack=tech_stack or [],
        locations=locations or [],
        sort=sort,
        limit=limit,
        offset=offset,
        count=total,
        items=items,
    )
