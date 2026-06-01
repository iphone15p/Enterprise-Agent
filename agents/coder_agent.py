"""
================================================================================
🧠 Coder Agent — AI 程序员
================================================================================

职责：根据计划（plan）和调研资料（research_info）编写 Python 代码。
要求输出纯代码，不带 Markdown 包裹。
"""

from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.1     # 低温度，让代码更稳定、少出错
)


def code_node(state: dict):
    """
    被 LangGraph 工作流调用的入口函数。
    输入：state["task"]、state["plan"]、state["research_info"]
    输出：{"code": "..."} → 代码文本，传给 Executor
    """
    print("\n[Coder] Writing code based on plan and research...")

    prompt = f"""You are an expert Python developer.

User's Task: {state["task"]}
Architect's Plan: {state["plan"]}
Research Notes (with latest API info): {state.get("research_info", "No additional info")}

Write complete, runnable Python code.
Requirements:
1. Output ONLY the raw Python code — no explanations.
2. Do NOT wrap code in ```python or ``` markers.
"""

    response = llm.invoke(prompt)
    return {"code": response.content}
