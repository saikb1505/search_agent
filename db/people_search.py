# db/people_search.py
from typing import Any, Dict, List, Optional, Tuple
import json
import aiomysql
from db.async_mysql import get_db_connection


def _norm(s: Optional[str]) -> Optional[str]:
    """Lowercase + trim helper."""
    return s.strip().lower() if isinstance(s, str) else None


async def search_people_by_keyword(
    q: str,
    location: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Keyword search over SalesQL-enriched people.

    Matches if any of these are true:
      - q appears in title / headline / person_industry / org_industry (case-insensitive LIKE)
      - OR q appears (substring) inside any item of search_query_queue.parsed_technologies_json

    Optional location filter (case-insensitive) matches if location equals any of:
      - person_city/state/country OR org_city/state/country OR any item in parsed_locations_json

    Requires MySQL 8+ for JSON_TABLE. CAST() keeps it robust if JSON columns are TEXT.
    """
    qn = _norm(q)
    if not qn:
        return []

    has_loc = _norm(location) is not None
    locn = _norm(location) if has_loc else None

    # Optional location WHERE block
    location_filter_sql = ""
    location_params: Tuple[Any, ...] = tuple()
    if has_loc:
        location_filter_sql = """
        AND (
              LOWER(COALESCE(sep.person_city,''))    = %s
          OR  LOWER(COALESCE(sep.person_state,''))   = %s
          OR  LOWER(COALESCE(sep.person_country,'')) = %s
          OR  LOWER(COALESCE(sep.org_city,''))       = %s
          OR  LOWER(COALESCE(sep.org_state,''))      = %s
          OR  LOWER(COALESCE(sep.org_country,''))    = %s
          OR  LOWER(COALESCE(jl.loc,''))             = %s
        )
        """
        location_params = (locn, locn, locn, locn, locn, locn, locn)

    # Build SQL using substring match for tech (LIKE) and CAST() to JSON for safety.
    sql = f"""
    SELECT DISTINCT sep.*
    FROM salesql_enriched_people AS sep
    LEFT JOIN search_query_queue AS s
      ON s.id = sep.search_id
    /* Expand parsed techs and locations; CAST handles TEXT/BLOB JSON storage */
    LEFT JOIN JSON_TABLE(CAST(s.parsed_technologies_json AS JSON), '$[*]'
      COLUMNS (tech VARCHAR(128) PATH '$')) jt
      ON TRUE
    LEFT JOIN JSON_TABLE(CAST(s.parsed_locations_json AS JSON), '$[*]'
      COLUMNS (loc VARCHAR(128) PATH '$')) jl
      ON TRUE
    WHERE (
             LOWER(COALESCE(sep.title,''))           LIKE %s
          OR LOWER(COALESCE(sep.headline,''))        LIKE %s
          OR LOWER(COALESCE(sep.person_industry,'')) LIKE %s
          OR LOWER(COALESCE(sep.org_industry,''))    LIKE %s
          OR LOWER(COALESCE(jt.tech,''))             LIKE %s
    )
    {location_filter_sql}
    ORDER BY sep.id DESC
    LIMIT %s OFFSET %s
    """

    like = f"%{qn}%"
    params: Tuple[Any, ...] = (like, like, like, like, like) + location_params + (int(limit), int(offset))

    conn = await get_db_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

        # Parse possible TEXT-stored JSON columns into Python objects
        for r in rows:
            for key in ("emails_json", "phones_json", "raw_json"):
                val = r.get(key)
                if isinstance(val, (bytes, bytearray)):
                    try:
                        val = val.decode("utf-8")
                    except Exception:
                        pass
                if isinstance(val, str):
                    try:
                        r[key] = json.loads(val)
                    except Exception:
                        # leave as-is if not valid JSON
                        pass
        return rows
    finally:
        conn.close()
