import sys
import os
import asyncio

# Add the root project directory (QUERY_AGENT_FASTAPI) to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir))
sys.path.append(project_root)

# Load env variables
from dotenv import load_dotenv
load_dotenv()

# Now imports will work
from agent.tools.google_search import google_search

async def test():
    query = 'site:linkedin.com/in ("Ruby on Rails") Bangalore'
    results = await google_search(query)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}\n{r['link']}\n{r['snippet']}\n")

if __name__ == "__main__":
    asyncio.run(test())
