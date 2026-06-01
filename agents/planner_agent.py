"""
================================================================================
🧠 Planner Agent — AI 项目经理
================================================================================

职责：分析用户任务，判断是简单问答还是复杂工程任务。
- 简单任务 → 返回 "SIMPLE_QUERY: 无需编码"
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
你是一个资深的 AI 项目经理。

【历史上下文】：
{history_info if history_info else "无"}

【用户任务】：
{task}

执行规则：
1. 如果任务只是简单的【问答、查资料、闲聊】（比如"迟到怎么罚"、"今天有什么新闻"），
   请直接输出："SIMPLE_QUERY: 无需编码"
2. 如果任务需要【编写代码、开发程序】（比如"写一个贪吃蛇"、"帮我写个爬虫"），
   请输出简洁的分步执行计划。
3. 禁止输出寒暄、反问或废话，直接给出判断结果。
"""

    response = llm.invoke(prompt)
    return {"plan": response.content}
