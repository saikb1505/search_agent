# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.agent_base import BaseAgent
from api.salesql_routes import router as salesql_router  # <-- NEW

load_dotenv()

app = FastAPI(
    title="Agent Vikram API",
    version="0.2.0",
    openapi_tags=[
        {"name": "SalesQL", "description": "Enrich LinkedIn profiles using SalesQL"},
    ],
)

class AgentInput(BaseModel):
    user_input: str
    max_results_per_query: int = 20  # keep configurable (1..100 depending on plan)

@app.post("/agentic-query-generator")
async def agentic_query_generator(payload: AgentInput):
    agent = BaseAgent()
    result = await agent.run(
        user_input=payload.user_input,
        max_results_per_query=payload.max_results_per_query,
    )
    return result

# NEW: mount SalesQL routes at /salesql/...
app.include_router(salesql_router)

@app.get("/health")
def health():
    return {"ok": True}
