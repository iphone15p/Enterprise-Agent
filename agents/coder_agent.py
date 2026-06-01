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
    print("\n[Coder] 正在根据计划和调研资料编写代码...")

    prompt = f"""你是一个顶级的 Python 程序员。

用户需求：{state["task"]}
架构师计划：{state["plan"]}
调研资料（含最新 API 信息）：{state.get("research_info", "无附加资料")}

请编写完整的、可直接运行的 Python 代码。

要求：
1. 只输出纯 Python 代码，不要任何解释文字。
2. 严禁用 ```python 或 ``` 包裹代码，直接以代码本身开头。
"""

    response = llm.invoke(prompt)
    return {"code": response.content}
