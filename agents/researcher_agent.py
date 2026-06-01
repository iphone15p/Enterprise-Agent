"""
================================================================================
🧠 Researcher Agent — AI 情报分析师
================================================================================

职责：根据 Planner 的计划，使用各种工具搜集信息。
拥有的工具（武器库）：
- search_web()          → DuckDuckGo 全网搜索
- search_internal_docs() → 本地 ChromaDB 知识库检索
- search_baidu()        → Playwright 百度抓取
- search_bilibili()     → Playwright B站抓取

工作流程：
1. LLM 收到任务和计划 → 决定用哪些工具
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
    """搜索互联网公开信息、实时新闻等（基于 DuckDuckGo）"""
    search = DuckDuckGoSearchRun()
    return search.run(query)


@tool
def search_internal_docs(query: str) -> str:
    """搜索极客科技内部机密文档（基于 ChromaDB 向量检索）"""
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

    prompt = f"""
You are the AI Research Analyst for "GeekTech" (极客科技).

[Historical Context]:
{history_info if history_info else "No prior context."}

[Project Plan]:
{plan}

[User's Request]:
{task}

Rules:
1. If the user mentions internal company topics (late penalty, benefits, CEO, passwords, internal projects),
   you MUST call `search_internal_docs` first.
2. For general knowledge or real-time info, use `search_web`, `search_baidu`, or `search_bilibili`.
3. Never ask the user for clarification — act autonomously.
"""

    # 第一轮：让 LLM 决定用什么工具
    msg = llm_with_tools.invoke(prompt)

    if msg.tool_calls:
        # 获取第一个工具调用的信息（LangChain 格式）
        tool_name = msg.tool_calls[0]["name"]
        args_dict = msg.tool_calls[0]["args"]
        print(f"      -> [Researcher] Using tool: {tool_name}, args: {args_dict}")

        # 根据工具名称分发调用
        if tool_name == "search_internal_docs":
            tool_result = search_internal_docs.invoke(args_dict)
        elif tool_name == "search_baidu":
            tool_result = search_baidu.invoke(args_dict)
        elif tool_name == "search_bilibili":
            tool_result = search_bilibili.invoke(args_dict)
        else:
            tool_result = search_web.invoke(args_dict)

        print(f"      -> [Researcher] Result preview: {tool_result[:200]}...")

        # 第二轮：让 LLM 把查到的原始资料整理成结构化报告
        final_prompt = f"""
Based on the research results below, answer the user's request.

Research Results (your ONLY factual source):
{tool_result}

User Request: {task}

Rules:
1. Answer strictly based on the provided research — do not fabricate.
2. If the research doesn't cover the answer, say so honestly.
3. Use Markdown formatting with proper headings, bold, and lists where appropriate.
"""
        final_msg = llm.invoke(final_prompt)
        return {"research_info": final_msg.content}

    else:
        # LLM 认为不需要查资料，直接凭知识回答
        print("      -> [Researcher] No tool needed, answering from context.")
        return {"research_info": msg.content}
