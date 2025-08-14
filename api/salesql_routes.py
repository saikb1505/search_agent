# api/salesql_routes.py
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from db.salesql_results import fetch_salesql_people
from db.async_mysql import get_db_connection

router = APIRouter(prefix="/salesql", tags=["SalesQL"])


# ---- Pydantic response models ----

class SalesQLPeopleResponse(BaseModel):
    search_id: int = Field(..., description="Echo of the requested search_id")
    count: int = Field(..., description="Number of rows returned in this page (not the total)")
    limit: int = Field(..., description="Page size used for the query")
    offset: int = Field(..., description="Offset used for the query")
    items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Array of people rows (JSON columns already parsed)",
    )


class SalesQLPeopleCountResponse(BaseModel):
    search_id: int
    total: int = Field(..., description="Total number of rows for this search_id")


# ---- Routes ----

@router.get(
    "/people",
    summary="List SalesQL-enriched people by search_id",
    response_model=SalesQLPeopleResponse,
)
async def get_salesql_people(
    search_id: int = Query(..., description="search_id to filter rows"),
    limit: int = Query(100, ge=1, le=500, description="Max rows to return (1–500)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> SalesQLPeopleResponse:
    """
    Returns rows from `salesql_enriched_people` for the given `search_id`.

    Notes:
    - Parses JSON columns (`emails_json`, `phones_json`, `raw_json`) into Python objects.
    - Sorted by `id ASC` for stable pagination.
    """
    try:
        items = await fetch_salesql_people(search_id=search_id, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch people: {e}")

    return SalesQLPeopleResponse(
        search_id=search_id,
        count=len(items),
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get(
    "/people/count",
    summary="Get total count of SalesQL-enriched people for a search_id",
    response_model=SalesQLPeopleCountResponse,
)
async def get_salesql_people_count(
    search_id: int = Query(..., description="search_id to count rows for")
) -> SalesQLPeopleCountResponse:
    """
    Returns the total number of rows in `salesql_enriched_people` matching the given `search_id`.
    Useful for building pagination UIs without fetching all rows.
    """
    sql = """
        SELECT COUNT(*) AS total
        FROM salesql_enriched_people
        WHERE search_id = %s
    """

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, (int(search_id),))
            row = await cur.fetchone()
            if not row:
                total = 0
            else:
                # aiomysql default cursor returns tuples unless DictCursor is used
                # handle both cases safely
                if isinstance(row, dict) and "total" in row:
                    total = int(row["total"])
                else:
                    total = int(row[0])  # first column
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch count: {e}")
    finally:
        conn.close()

    return SalesQLPeopleCountResponse(search_id=search_id, total=total)
