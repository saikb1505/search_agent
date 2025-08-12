import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ParserAgent:
    def __init__(self, user_input: str):
        self.user_input = user_input

    def parse(self) -> dict:
        system_prompt = (
            "You are an AI assistant that extracts structured data from recruitment requests. "
            "Extract two fields: 'tech_stack' (array of technologies) and 'locations' (array of cities or regions). "
            "If the location is generic like 'India', output top 10 tech cities in India. "
            "Return JSON like this: "
            "{ \"tech_stack\": [\"Ruby\", \"Ruby on Rails\"], \"locations\": [\"Bangalore\", \"Hyderabad\", ...] }"
        )

        response = client.chat.completions.create(model="gpt-4",
        temperature=0,
        messages=[
            { "role": "system", "content": system_prompt },
            { "role": "user", "content": self.user_input }
        ])

        content = response.choices[0].message.content
        try:
            return eval(content) if isinstance(content, str) else content
        except Exception:
            return { "error": "Failed to parse LLM output", "raw": content }
