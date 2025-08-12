# agent/workers/linkedin_search_worker.py
from agent.tools.serper_linkedin_search import serper_linkedin_search
from agent.tools.save_search_results import save_search_results
from agent.tools.query_queue import get_pending_queries, mark_query_done, mark_query_failed

async def run_linkedin_search_worker(max_results_per_query: int = 20) -> dict:
    """
    Processes pending queries:
      - pulls from search_query_queue
      - calls Serper.dev for LinkedIn
      - saves results to google_search_results
    Returns a small summary for the API response.
    """
    processed = []
    failed = []

    queries = await get_pending_queries(limit=5)
    for row in queries:
        qid = row["id"]
        qtext = row["query"]
        try:
            results = await serper_linkedin_search(qtext, num_results=max_results_per_query)
            await save_search_results(qid, qtext, results)
            await mark_query_done(qid)
            processed.append({"search_id": qid, "query": qtext, "saved": len(results)})
        except Exception as e:
            await mark_query_failed(qid)
            failed.append({"search_id": qid, "query": qtext, "error": str(e)})

    return {"processed": processed, "failed": failed}
