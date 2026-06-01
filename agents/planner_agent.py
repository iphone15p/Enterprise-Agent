from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.7
)


def plan_node(state: dict):
    """
    AI Project Manager: analyzes the task and produces a step-by-step plan.
    For simple queries, returns a directive to skip the coding pipeline.
    """
    task = state.get("task", "")
    history_info = state.get("research_info", "")

    prompt = f"""
You are a senior AI Project Manager.

[Historical Context]:
{history_info if history_info else "None"}

[User Task]:
{task}

Rules:
1. If the task is a simple question, lookup, or casual chat (e.g. "what's the late penalty?", "who is the CEO?"),
   respond with exactly: "SIMPLE_QUERY: no code needed."
2. If the task requires code development (e.g. "write a snake game", "build a web scraper"),
   output a concise step-by-step plan.
3. No greetings, no filler — be direct and actionable.
"""

    response = llm.invoke(prompt)
    return {"plan": response.content}
