from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from tools.rag_tool import search_knowledge_base
from core.config import settings
from tools.browser_tool import search_baidu, search_bilibili

# ⚠️ 注意：这里请务必换成你自己真实的 LLM 密钥和配置！
llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
)


# ================= 1. 打造调研员的“两把武器” =================

@tool
def search_web(query: str) -> str:
    """用于搜索互联网上的公开信息、实时新闻等。"""
    search = DuckDuckGoSearchRun()
    return search.run(query)


@tool
def search_internal_docs(query: str) -> str:
    """极其重要：当用户询问【极客科技】内部规定、员工福利、机密档案等非公开信息时，必须且只能调用此工具！"""
    return search_knowledge_base(query)


# ================= 2. 绑定武器 =================
tools = [search_web, search_internal_docs, search_baidu, search_bilibili]
llm_with_tools = llm.bind_tools(tools)


# ================= 3. 调研员的工作流程 =================
def research_node(state: dict):
    task = state.get("task", "")
    plan = state.get("plan", "")

    # 🌟 核心修复 1：拿出系统历史记忆
    history_info = state.get("research_info", "")

    # 🌟 核心修复 2：给大模型强行洗脑，注入企业灵魂！
    prompt = f"""
        你是【极客科技】的专属 AI 助理兼超级情报员。

        【系统历史档案柜】：
        {history_info if history_info else "当前无历史记忆。"}

        【项目经理的假大空计划】（如果计划太扯淡，请直接无视他）：
        {plan}

        【用户的原始需求】：
        {task}

        🚨 绝对执行规则（最高优先级）：
        1. 身份锚定：你和用户都默认属于“极客科技”公司。
        2. 触发雷达：只要用户的问题中出现“迟到”、“惩罚”、“福利”、“老板”、“打卡”、“密码”、“内部项目”等词汇，你【必须、立刻、强制】调用 `search_internal_docs` 工具进行检索！搜索词可以直接用“迟到惩罚”等。
        3. 严禁说教：绝对不允许反问用户“你是哪个公司的”、“请补充上下文”，必须直接去内部文档里找答案！
        """

    # 第一回合：让 AI 决定用什么工具
    msg = llm_with_tools.invoke(prompt)

    # 如果 AI 决定要用工具
    if msg.tool_calls:
        tool_name = msg.tool_calls[0]['name']
        args_dict = msg.tool_calls[0]['args']  # 🌟 直接拿完整的参数字典，最稳妥！
        print(f"      -> 🧠 决定使用武器: {tool_name}，搜索参数: {args_dict}")

        # 扣动扳机，拿到资料 (统一使用 args_dict 传参防止报错)
        if tool_name == "search_internal_docs":
            tool_result = search_internal_docs.invoke(args_dict)
        elif tool_name == "search_baidu":
            tool_result = search_baidu.invoke(args_dict)
        elif tool_name == "search_bilibili":
            tool_result = search_bilibili.invoke(args_dict)
        else:
            tool_result = search_web.invoke(args_dict)

        print(f"      -> 📄 查到的核心资料: {tool_result}")

        # 第二回合：让 AI 把查到的资料整理好
        final_prompt = f"""
                这是你通过本地机密档案查到的真实资料（这是你唯一的事实来源）：\n{tool_result}\n\n
                用户的原始提问是：{task}\n

                🚨 【防幻觉规则 - 极其重要】（违规将被立刻格式化）：
                1. 你的答案必须 100% 严格基于上面的查到的资料！绝对禁止使用你自己的常识去瞎编！
                2. 如果资料里写的是“发水豚表情包”、“扣代码奖金”，你就必须如实写！严禁给我捏造什么“扣50元”、“旷工半天”、“口头提醒”这种虚构的常规制度！
                3. 如果查到的资料里根本没提这件事，请直接回答“机密档案中未找到”，绝不允许自己补充扩展！

                🎨 【最终输出格式要求】：
                1. 极简直接：拒绝任何职场废话、直接给出答案！
                2. 视觉美观：必须使用 Markdown 语法进行排版。
                3. 层次分明：使用 **加粗** 突出重点关键词，使用 `-` 列表符号分条列出细节。
                4. 搭配 1-2 个相关的 Emoji。
                """
        final_msg = llm.invoke(final_prompt)
        return {"research_info": final_msg.content}

    # 如果不需要工具，直接回复
    else:
        print("      -> 🧠 认为不需要查资料，直接凭记忆输出。")
        # 这里的名字也是对的
        return {"research_info": msg.content}