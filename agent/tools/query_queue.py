# agent/tools/query_queue.py
from __future__ import annotations
from typing import Iterable, List, Optional, Dict, Any
import json
import aiomysql
from db.async_mysql import get_db_connection

TABLE_QUEUE = "search_query_queue"


async def enqueue_queries(queries: List[str]) -> int:
    """Legacy insert: enqueues queries without parsed metadata.
    Returns number of rows inserted.
    """
    return await enqueue_queries_with_parsed(queries=queries)


async def enqueue_queries_with_parsed(
    queries: Iterable[str],
    tech_stack: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    parser_version: Optional[str] = None,
) -> int:
    """Insert queries into the queue with parsed technologies/locations JSON.
    Each row inserted will later act as a `search_id` for downstream tables.
    Returns number of rows inserted.
    """
    qlist = [q.strip() for q in (list(queries) if queries else []) if q and q.strip()]
    if not qlist:
        return 0

    tech_json = json.dumps(tech_stack or [], ensure_ascii=False)
    loc_json = json.dumps(locations or [], ensure_ascii=False)

    conn = await get_db_connection()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            for q in qlist:
                await cur.execute(
                    f"""
                    INSERT INTO {TABLE_QUEUE}
                        (query, status, parsed_technologies_json, parsed_locations_json, parser_version)
                    VALUES
                        (%s, 'pending', %s, %s, %s)
                    """,
                    (q, tech_json, loc_json, parser_version),
                )
        # autocommit=True in connection
        return len(qlist)
    finally:
        conn.close()


async def get_pending_queries(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch pending queue rows to be processed by the worker."""
    conn = await get_db_connection()
    rows: List[Dict[str, Any]] = []
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT id, query
                FROM {TABLE_QUEUE}
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT %s
                """,
                (int(limit),),
            )
            rows = await cur.fetchall()
    finally:
        conn.close()
    return rows


async def mark_query_done(row_id: int) -> None:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"UPDATE {TABLE_QUEUE} SET status = 'done' WHERE id = %s",
                (row_id,),
            )
    finally:
        conn.close()


async def mark_query_failed(row_id: int, error_message: Optional[str] = None) -> None:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            if error_message is None:
                await cur.execute(
                    f"UPDATE {TABLE_QUEUE} SET status = 'failed' WHERE id = %s",
                    (row_id,),
                )
            else:
                # Try to store error_message if column exists; ignore failure if not
                try:
                    await cur.execute(
                        f"UPDATE {TABLE_QUEUE} SET status = 'failed', error_message = %s WHERE id = %s",
                        (error_message[:2000], row_id),
                    )
                except Exception:
                    await cur.execute(
                        f"UPDATE {TABLE_QUEUE} SET status = 'failed' WHERE id = %s",
                        (row_id,),
                    )
    finally:
        conn.close()
