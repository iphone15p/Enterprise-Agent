"""
================================================================================
🧠 Reviewer Agent — AI 代码审查员
================================================================================

职责：检查代码执行结果，决定通过还是打回。
- 执行成功 → 返回 "PASS"，管线结束
- 执行失败 → 分析错误原因，打回 Coder 重写（最多 2 次）
"""

from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.1     # 低温度，审查要精准
)


def review_node(state: dict):
    """
    被 LangGraph 工作流调用的入口函数。
    输入：state["execution_result"]、state["task"]
    输出：{"feedback": "PASS"} 或 {"feedback": "错误分析..."}
    """
    print("\n[Reviewer] Checking code execution results...")

    exec_result = state.get("execution_result", "")

    # 快速通道：执行成功直接通过
    if "✅ 运行成功" in exec_result or "success" in exec_result.lower():
        print("      -> Code executed successfully. PASS.")
        return {"feedback": "PASS"}

    # 失败 → 分析根因，给出修复建议
    prompt = f"""You are a strict code reviewer.

The code execution produced this output/error:
{exec_result}

User's original task: {state.get("task", "")}

Analyze the failure and provide a concise fix suggestion for the developer.
Focus on the root cause. Do not output code — just the diagnosis and fix direction.
"""

    response = llm.invoke(prompt)
    return {"feedback": response.content}
