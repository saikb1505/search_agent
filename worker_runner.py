# worker_runner.py
# Simple background worker loop for Agent Vikram
import asyncio
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Import the async worker that processes pending queries
from agent.workers.linkedin_search_worker import run_linkedin_search_worker

INTERVAL_SECONDS = int(os.getenv("WORKER_POLL_INTERVAL", "20"))
MAX_RESULTS_PER_QUERY = int(os.getenv("WORKER_MAX_RESULTS_PER_QUERY", "20"))

async def main():
    while True:
        try:
            result = await run_linkedin_search_worker(max_results_per_query=MAX_RESULTS_PER_QUERY)
            # Basic visibility in logs
            print({"worker_run": result})
        except Exception as e:
            # Never crash the worker loop
            print({"worker_error": str(e)})
        await asyncio.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())

