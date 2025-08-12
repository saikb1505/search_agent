# agent/tools/save_search_results.py
from db.async_mysql import get_db_connection

async def save_search_results(search_id: int, query: str, results: list[dict]):
    """
    Persist Google search results for a given search_id.
    Each result item should have keys: title, link, snippet.
    """
    if not results:
        return

    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        for item in results:
            await cursor.execute(
                """
                INSERT INTO google_search_results (search_id, query, title, link, snippet)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    search_id,
                    query,
                    item.get("title"),
                    item.get("link"),
                    item.get("snippet")
                ),
            )
    conn.close()
