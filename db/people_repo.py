# db/people_repo.py
import json
from typing import List, Optional, Tuple, Dict, Any
from db.async_mysql import get_db_connection

_TABLE = "salesql_enriched_people"
_cached_cols: Optional[List[str]] = None  # preserve order


async def _get_columns() -> List[str]:
    """
    Return all column names for the table, preserving the physical order.
    Cached after first lookup.
    """
    global _cached_cols
    if _cached_cols is not None:
        return _cached_cols

    sql = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """
    async with await get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (_TABLE,))
            _cached_cols = [row[0] for row in await cur.fetchall()]
    return _cached_cols


def _build_like_clause(cols: List[str]) -> str:
    # Produces "(p.a LIKE %s OR p.b LIKE %s ...)"
    return "(" + " OR ".join([f"p.`{c}` LIKE %s" for c in cols]) + ")"


async def search_people(
    search_id: Optional[int],
    q: Optional[str],
    tech_stack: List[str],   # kept for compatibility; used only if columns exist
    locations: List[str],    # kept for compatibility; used only if columns exist
    sort: str,
    limit: int,
    offset: int,
) -> Tuple[List[Dict[str, Any]], int]:
    cols = await _get_columns()

    # SELECT all columns dynamically
    select_sql = ", ".join([f"p.`{c}`" for c in cols])

    # WHERE
    where = ["1=1"]
    params: List[Any] = []

    if search_id is not None and "search_id" in cols:
        where.append("p.`search_id` = %s")
        params.append(search_id)

    # free-text against commonly useful columns IF present
    q_targets_preference = [
        "full_name", "first_name", "last_name", "title", "headline",
        "person_industry", "person_city", "person_state", "person_country",
        "org_name", "org_industry", "org_city", "org_state", "org_country",
        "linkedin_url", "org_website", "org_domain"
    ]
    q_targets = [c for c in q_targets_preference if c in cols]
    if q and q_targets:
        where.append(_build_like_clause(q_targets))
        like = f"%{q}%"
        params.extend([like] * len(q_targets))

    # Optional JSON array filters if you add such columns in the future.
    # (Your sample schema doesn’t have these, so these are no-ops unless present.)
    def _json_contains_any(column: str, values: List[str]) -> Tuple[str, List[str]]:
        parts, p = [], []
        for v in values:
            parts.append(f"JSON_CONTAINS(p.`{column}`, %s, '$')")
            p.append(json.dumps(v))
        return "(" + " OR ".join(parts) + ")", p

    if tech_stack and "tech_stack" in cols:
        clause, p = _json_contains_any("tech_stack", tech_stack)
        where.append(clause)
        params.extend(p)

    if locations and "locations" in cols:
        clause, p = _json_contains_any("locations", locations)
        where.append(clause)
        params.extend(p)

    where_sql = " AND ".join(where)

    # ORDER
    if sort == "name" and "full_name" in cols:
        order_sql = "p.`full_name` ASC"
    elif "created_at" in cols:
        order_sql = "p.`created_at` DESC"
    elif "id" in cols:
        order_sql = "p.`id` DESC"
    else:
        order_sql = "1"

    # COUNT
    count_sql = f"SELECT COUNT(*) FROM `{_TABLE}` p WHERE {where_sql}"

    # DATA
    data_sql = f"""
        SELECT {select_sql}
        FROM `{_TABLE}` p
        WHERE {where_sql}
        ORDER BY {order_sql}
        LIMIT %s OFFSET %s
    """

    # Execute
    async with await get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(count_sql, params)
            row = await cur.fetchone()
            total = int(row[0]) if row and row[0] is not None else 0

            dparams = params + [limit, offset]
            await cur.execute(data_sql, dparams)
            rows = await cur.fetchall()
            colnames = [c[0] for c in cur.description]
            raw = [dict(zip(colnames, r)) for r in rows]

    # Parse JSON columns if present
    def _parse_json(val):
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return val  # leave as-is if not valid JSON

    for r in raw:
        if "emails_json" in r:
            r["emails_json"] = _parse_json(r["emails_json"])
        if "phones_json" in r:
            r["phones_json"] = _parse_json(r["phones_json"])
        if "raw_json" in r:
            r["raw_json"] = _parse_json(r["raw_json"])

    return raw, total
