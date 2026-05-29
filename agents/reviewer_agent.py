from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.1
)


def review_node(state: dict):
    # 【新增核心逻辑】：如果白板上已经有 feedback，说明程序员已经苦逼地重写过一次了
    if state.get("feedback"):
        print("[测试员 Reviewer] 🙄 算了，看你改过一次了，勉强让你过吧！准许交付！")
        return {"feedback": "PASS"}

    print("[测试员 Reviewer] 🧐 拿到初版代码，正在进行严苛审查...")
    code = state["code"]

    prompt = f"你是一个极其严苛的测试工程师。请检查以下 Python 代码是否有明显的语法错误。\n代码：{code}\n如果代码没问题，请务必仅回复 'PASS'。如果有问题，请用一句话指出。"

    response = llm.invoke(prompt)
    feedback = response.content.strip()

    # 强制找茬彩蛋
    if feedback == "PASS":
        feedback = "代码看起来太简单了，缺少详细的中文注释，打回测试！"

    print(f"[测试员 Reviewer] ❌ 发现问题，打回重写！原因：{feedback}")
    return {"feedback": feedback}