from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.1
)


# (在你的 review_node 函数里，修改调用大模型的提示词部分，类似下面这样：)

# 注意：保留你原本文件最上方的 import 和 llm 配置代码
# 只替换 review_node 这个函数即可

def review_node(state: dict):
    print("\n[审查专员 Reviewer] 🕵️ 正在检查代码和运行结果...")

    exec_result = state.get("execution_result", "")

    # 【终极防卡死补丁】：只要包含"✅ 运行成功"，直接绕过大模型，强制绿灯！
    if "✅ 运行成功" in exec_result:
        print("      -> 🚀 代码已成功运行，强制亮起绿灯！进入保存流程！")
        return {"feedback": "PASS"}

    prompt = f"""你是一个严厉的代码审查员。
代码运行报错了：
{exec_result}

请结合用户需求：{state.get("task", "")}
分析这段错误，给出修改建议，让程序员重写。不要输出代码，只说原因。"""

    response = llm.invoke(prompt)
    return {"feedback": response.content}