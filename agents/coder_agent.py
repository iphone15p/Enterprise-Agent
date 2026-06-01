from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.1
)


def code_node(state: dict):
    print("\n[开发专员 Coder] 💻 正在根据计划和查阅的资料编写代码...")

    # 【核心修改】：把 research_info 塞给 Coder
    prompt = f"""你是一个顶级的 Python 程序员。

用户需求: {state["task"]}
架构师的计划: {state["plan"]}

【联网调研资料】(如果有报错重试，请参考这里的最新API):
{state.get("research_info", "无附加资料")}

请开始编写完整的 Python 代码。
要求：
1. 只输出代码，不要任何解释。
2. 必须用 ```python 和 ``` 包裹代码。
"""

    response = llm.invoke(prompt)
    return {"code": response.content}