import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from agent.tools.query_queue import enqueue_queries

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_LOCATIONS = ["Bangalore", "Hyderabad", "Mumbai", "Delhi", "Pune"]

class QueryGeneratorAgent:
    def __init__(self, tech_stack: str, locations: list[str] = None):
        self.tech_stack = [t.strip() for t in tech_stack.split(",") if t.strip()]
        self.locations = locations if locations else DEFAULT_LOCATIONS

    async def run(self) -> list[dict]:
        system_prompt = (
            "You are a helpful agent that generates Google search queries for finding developer profiles on LinkedIn. "
            "For each location, return a query in this exact JSON format: "
            '[{"location":"<Location>","query":"site:linkedin.com/in (\\"term1\\" OR \\"term2\\") <Location>"} , ...]. '
            "Do not include any explanations, backticks, or extra text—return only valid JSON."
        )

        user_prompt = (
            f"Tech Stack: {', '.join(self.tech_stack)}\n"
            f"Locations: {', '.join(self.locations)}"
        )

        resp = client.chat.completions.create(
            model="gpt-4",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        output = resp.choices[0].message.content or "[]"

        try:
            queries_data = json.loads(output)
        except json.JSONDecodeError:
            # Attempt to clean and parse
            cleaned = output.strip().strip("```").strip()
            try:
                queries_data = json.loads(cleaned)
            except Exception:
                return [{"error": "Failed to parse JSON", "raw": output}]

        # ✅ Save to DB
        queries = [item["query"] for item in queries_data if "query" in item]
        if queries:
            await enqueue_queries(queries)

        return queries_data
