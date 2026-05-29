from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.1
)


def code_node(state: dict):
    plan = state["plan"]
    # 尝试从状态里拿“测试反馈”（第一遍写代码时是没有反馈的）
    feedback = state.get("feedback", "")

    if feedback and feedback != "PASS":
        print("[程序员 Coder] 😭 收到 Bug 反馈，正在痛苦地修改代码...")
        prompt = f"你之前写的代码有 Bug！请根据测试员的反馈进行修改。\n原始计划：{plan}\n测试反馈：{feedback}\n请直接输出修改后的完整 Python 代码。"
    else:
        print("[程序员 Coder] 👨‍💻 收到项目经理的计划，正在狂敲代码...")
        prompt = f"你是一个高级程序员。请严格按照以下计划，写出具体的 Python 代码：\n计划：{plan}\n注意：只输出代码块，不要加多余的解释。"

    response = llm.invoke(prompt)
    return {"code": response.content}