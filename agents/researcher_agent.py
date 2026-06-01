"""
================================================================================
🧠 Researcher Agent — AI 情报分析师
================================================================================

职责：根据 Planner 的计划，使用各种工具搜集信息。
拥有的工具（武器库）：
- search_web()          → DuckDuckGo 全网搜索
- search_internal_docs() → 本地 ChromaDB 知识库检索
- search_baidu()        → Playwright 百度抓取（中文实时信息最强）
- search_bilibili()     → Playwright B站抓取（视频/直播/游戏攻略）

工作流程：
1. LLM 收到任务和计划 → 决定用哪个工具
2. 执行工具调用 → 获取原始资料
3. LLM 整理资料 → 输出结构化报告给 Coder
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from tools.rag_tool import search_knowledge_base
from tools.browser_tool import search_baidu, search_bilibili
from core.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
)


# ==================== 工具定义 ====================

@tool
def search_web(query: str) -> str:
    """搜索互联网公开信息、实时新闻等（基于 DuckDuckGo，适合英文/通用搜索）"""
    search = DuckDuckGoSearchRun()
    return search.run(query)


@tool
def search_internal_docs(query: str) -> str:
    """搜索极客科技内部机密文档（基于 ChromaDB 向量检索，公司规定/福利/密码等）"""
    return search_knowledge_base(query)


# 把所有工具绑定到 LLM，让模型可以自主决定调用哪个
tools = [search_web, search_internal_docs, search_baidu, search_bilibili]
llm_with_tools = llm.bind_tools(tools)


# ==================== 调研节点 ====================

def research_node(state: dict):
    """
    被 LangGraph 工作流调用的入口函数。
    输入：state["task"]、state["plan"]
    输出：{"research_info": "..."} → 调研报告，传给 Coder
    """
    task = state.get("task", "")
    plan = state.get("plan", "")
    history_info = state.get("research_info", "")

    # 判断任务类型：简单问答/搜索（必须搜） vs 编码任务（搜不搜看情况）
    is_simple = "无需编码" in plan or "SIMPLE_QUERY" in plan

    if is_simple:
        # 简单问答/搜索类 → 必须搜索，获取最新信息
        prompt = f"""
你是"极客科技"的专属 AI 情报分析师。

【用户需求】：
{task}

🚨 工具选择规则（必须严格遵守）：

1. 中文新闻、实时热点、国内动态 → 调用 `search_baidu`
2. 视频、直播、游戏攻略、UP主 → 调用 `search_bilibili`
3. 公司内部规定、迟到惩罚、福利 → 调用 `search_internal_docs`
4. 纯英文问题或以上工具都失败 → 用 `search_web` 兜底

⚠️ 死命令：必须先搜再回答，严禁凭自己的知识直接回答！
"""
    else:
        # 编码任务 → 搜不搜让 LLM 自己判断，不强制
        prompt = f"""
你是"极客科技"的专属 AI 情报分析师。

【项目计划】：
{plan}

【用户需求】：
{task}

根据计划判断是否需要搜索：
- 如果计划中需要最新 API 文档、技术资料 → 调用相应工具搜索
- 如果只是纯算法/逻辑代码（如"写个斐波那契函数"）→ 可以不搜，直接回答

可用工具：search_baidu(中文)、search_bilibili(视频)、search_internal_docs(内部文档)、search_web(通用)
"""


    # 第一轮：让 LLM 决定用什么工具
    print(f"\n{'='*60}")
    print(f"[Researcher] 🧠 LLM 正在决定使用哪个搜索工具...")
    print(f"[Researcher] 用户需求: {task[:100]}...")
    msg = llm_with_tools.invoke(prompt)

    if msg.tool_calls:
        # 获取第一个工具调用的信息（LangChain 格式）
        tool_name = msg.tool_calls[0]["name"]
        args_dict = msg.tool_calls[0]["args"]
        print(f"[Researcher] ✅ LLM 决定调用: {tool_name}")
        print(f"[Researcher] 搜索关键词: {args_dict}")
        print(f"[Researcher] ⏳ 正在执行搜索，请稍候...")

        # 根据工具名称分发调用
        if tool_name == "search_internal_docs":
            tool_result = search_internal_docs.invoke(args_dict)
        elif tool_name == "search_baidu":
            tool_result = search_baidu.invoke(args_dict)
        elif tool_name == "search_bilibili":
            tool_result = search_bilibili.invoke(args_dict)
        else:
            tool_result = search_web.invoke(args_dict)

        print(f"[Researcher] ✅ 搜索完成！")
        print(f"[Researcher] 原始搜索结果（完整内容，共 {len(str(tool_result))} 字符）:")
        print(f"{'─'*60}")
        print(tool_result)
        print(f"{'─'*60}")

        # 判断是否需要 LLM 二次整理（编码任务需要，简单查询跳过省时间）
        is_simple = "无需编码" in plan or "SIMPLE_QUERY" in plan

        if is_simple:
            # 简单查询：跳过 LLM 总结，直接返回原始搜索结果（省 3~8 秒）
            print(f"[Researcher] ⚡ 简单查询，跳过LLM总结，直接返回搜索结果！")
            return {"research_info": tool_result}
        else:
            # 编码任务：让 LLM 整理成结构化报告，方便 Coder 理解
            print(f"[Researcher] 📝 编码任务，LLM正在整理搜索结果...")
            final_prompt = f"""
你是极客科技的情报分析师。请根据以下搜索结果回答用户问题。

搜索结果（你唯一的事实来源，严禁编造）：
{tool_result}

用户问题：{task}

要求：
1. 严格基于搜索结果回答，不要自己编造任何信息。
2. 如果搜索结果不包含答案，请诚实地说"搜索结果中未找到相关信息"。
3. 使用 Markdown 格式排版：用标题、加粗、列表让答案清晰易读。
4. 尽量注明信息来源。
"""
            final_msg = llm.invoke(final_prompt)
            return {"research_info": final_msg.content}

    else:
        # LLM 认为不需要工具，但仍然要求它搜索（兜底）
        print("      -> [Researcher] LLM未调用工具，强制要求重新搜索...")
        # 强制用 DuckDuckGo 搜一次作为兜底
        try:
            fallback_result = search_web.invoke({"query": task})
            final_prompt = f"""
你是极客科技的情报分析师。

强制搜索结果：
{fallback_result}

用户问题：{task}

请基于上述搜索结果回答。使用 Markdown 格式。
"""
            final_msg = llm.invoke(final_prompt)
            return {"research_info": final_msg.content}
        except Exception as e:
            print(f"      -> [Researcher] 兜底搜索也失败了: {e}")
            return {"research_info": msg.content}
