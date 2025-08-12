from typing import Any, Dict, List, Optional, Callable
import inspect

from agent.parser_agent import ParserAgent
from agent.query_generator_agent import QueryGeneratorAgent
from agent.workers.linkedin_search_worker import run_linkedin_search_worker


async def _maybe_call(fn: Callable, *args, **kwargs):
    """Call a function that may be sync or async."""
    if inspect.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    result = fn(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class BaseAgent:
    """
    Pipeline:
      1) ParserAgent -> dict {"tech_stack":[...], "locations":[...]}
      2) QueryGeneratorAgent.run() -> generates & ENQUEUES queries (MySQL)
      3) run_linkedin_search_worker -> pulls queued, Serper search, saves, marks done
    """

    def __init__(self) -> None:
        pass

    async def run(self, user_input: str, max_results_per_query: int = 20) -> Dict[str, Any]:
        # ---- 1) Instantiate ParserAgent (constructor may or may not take user_input)
        try:
            parser = ParserAgent(user_input)   # if your __init__ needs the text
        except TypeError:
            parser = ParserAgent()             # otherwise, no-arg constructor

        # ---- 2) Prefer parse(); fall back to run()
        parsed: Dict[str, Any]
        parse_fn = getattr(parser, "parse", None)
        run_fn = getattr(parser, "run", None)

        if callable(parse_fn):
            # parse() expected to take NO args
            parsed = await _maybe_call(parse_fn)
        elif callable(run_fn):
            # try run(user_input) first; if TypeError, try run() with no args
            try:
                parsed = await _maybe_call(run_fn, user_input)
            except TypeError:
                parsed = await _maybe_call(run_fn)
        else:
            raise AttributeError(
                "ParserAgent must define either .parse() or .run()"
            )

        if not isinstance(parsed, dict):
            parsed = {"raw": parsed}

        tech_stack_list: List[str] = parsed.get("tech_stack") or []
        locations: Optional[List[str]] = parsed.get("locations") or None

        # ---- 3) Query generation (your generator expects a comma string)
        tech_stack_str = ", ".join(tech_stack_list) if tech_stack_list else user_input
        qg = QueryGeneratorAgent(tech_stack=tech_stack_str, locations=locations)
        generated = await qg.run()  # async; returns [{"location": "...", "query": "..."}]

        # ---- 4) Process queue: search -> save -> mark done
        summary = await run_linkedin_search_worker(max_results_per_query=max_results_per_query)

        return {
            "parsed": parsed,
            "generated_count": len(generated),
            "generated": generated,
            "worker_summary": summary,
        }