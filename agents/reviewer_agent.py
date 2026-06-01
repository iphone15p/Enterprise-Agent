from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.1
)


def review_node(state: dict):
    """
    AI Code Reviewer: checks execution results and decides whether the code passes.
    Returns PASS if successful, or feedback for the coder to fix issues.
    """
    print("\n[Reviewer] Checking code execution results...")

    exec_result = state.get("execution_result", "")

    # Fast path: execution succeeded
    if "✅ 运行成功" in exec_result or "success" in exec_result.lower():
        print("      -> Code executed successfully. PASS.")
        return {"feedback": "PASS"}

    prompt = f"""You are a strict code reviewer.

The code execution produced this output/error:
{exec_result}

User's original task: {state.get("task", "")}

Analyze the failure and provide a concise fix suggestion for the developer.
Focus on the root cause. Do not output code — just the diagnosis and fix direction.
"""

    response = llm.invoke(prompt)
    return {"feedback": response.content}
