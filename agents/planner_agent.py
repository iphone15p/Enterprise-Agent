"""
================================================================================
🧠 Planner Agent — AI 项目经理
================================================================================

职责：分析用户任务，判断是简单问答还是复杂工程任务。
- 简单任务 → 返回 "SIMPLE_QUERY"，后续走快速通道
- 复杂任务 → 输出分步执行计划，交给 Researcher 去调研
"""

from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.7     # 较高温度，让规划更有创意
)


def plan_node(state: dict):
    """
    被 LangGraph 工作流调用的入口函数。
    输入：state["task"]  = 用户原始输入
    输出：{"plan": "..."} → 写入共享 state，传递给 Researcher
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
