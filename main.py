# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.agent_base import BaseAgent

load_dotenv()
app = FastAPI()

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

@app.get("/health")
def health():
    return {"ok": True}
