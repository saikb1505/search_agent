from agent.query_generator_agent import QueryGeneratorAgent
from agent.parser_agent import ParserAgent

def parse_input(text: str) -> dict:
    return ParserAgent(user_input=text).parse()

def generate_queries(parsed: dict) -> list[dict]:
    agent = QueryGeneratorAgent(
        tech_stack=", ".join(parsed["tech_stack"]),
        locations=parsed["locations"]
    )
    return agent.run()

tools = {
    "parse_input": parse_input,
    "generate_queries": generate_queries
}
