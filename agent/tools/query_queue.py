# agent/tools/query_queue.py
import aiomysql
from db.async_mysql import get_db_connection

async def enqueue_queries(queries: list[str]):
    """Insert new search queries into the search_query_queue table."""
    if not queries:
        return

    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        for q in queries:
            await cursor.execute(
                "INSERT INTO search_query_queue (query) VALUES (%s)",
                (q,)
            )
    conn.close()

async def get_pending_queries(limit: int = 5):
  conn = await get_db_connection()
  async with conn.cursor(aiomysql.DictCursor) as cursor:
    await cursor.execute(
      "SELECT * FROM search_query_queue WHERE status = 'pending' LIMIT %s", (limit,)
    )
    rows = await cursor.fetchall()

    ids = [row["id"] for row in rows]
    if ids:
      in_clause = ",".join(["%s"] * len(ids))
      await cursor.execute(
          f"UPDATE search_query_queue SET status = 'processing' WHERE id IN ({in_clause})",
          tuple(ids)
      )
  conn.close()
  return rows

async def mark_query_done(search_id: int):
  conn = await get_db_connection()
  async with conn.cursor() as cursor:
    await cursor.execute(
      "UPDATE search_query_queue SET status = 'done' WHERE id = %s", (search_id,)
    )
  conn.close()

async def mark_query_failed(search_id: int):
  conn = await get_db_connection()
  async with conn.cursor() as cursor:
    await cursor.execute(
        "UPDATE search_query_queue SET status = 'failed' WHERE id = %s", (search_id,)
    )
  conn.close()
