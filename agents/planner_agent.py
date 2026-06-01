from langchain_openai import ChatOpenAI
from core.config import settings

# 给项目经理配一个活跃一点的大脑 (temperature=0.7)
llm = ChatOpenAI(
    api_key=settings.API_KEY, 
    base_url=settings.BASE_URL, 
    model=settings.MODEL_NAME, 
    temperature=0.7
)


def plan_node(state: dict):
    task = state.get("task", "")

    # 🌟 核心修复 1：把档案柜里的记忆拿出来
    history_info = state.get("research_info", "")

    # 🌟 核心修复 2：把记忆强行喂给项目经理看！
    # 🌟 让 Planner 学会“闭嘴”和“精准判断”
    prompt = f"""
        你是一个资深的 AI 项目经理。

        【系统历史记忆】：
        {history_info if history_info else "无"}

        【用户新任务】：
        {task}

        🚨 核心执行规则（必须严格遵守）：
        1. 判断任务类型：如果用户的任务只是【简单的问答、查资料、闲聊】（比如“迟到怎么罚款”、“马斯克是谁”），请你不要做任何规划！直接输出这四个字：“无需计划，直接查询”。
        2. 如果任务是【复杂的工程代码开发】（比如“写一个爬虫”、“开发贪吃蛇”），你才需要输出分步骤的执行计划。
        3. 绝对禁止输出任何寒暄、反问、废话或“极简三锚点”等格式化模板！
        """

    # ... 接着往下调用你的 llm.invoke(prompt) ...

    response = llm.invoke(prompt)
    # 将写好的计划更新到共享的 state (白板) 里
    return {"plan": response.content}