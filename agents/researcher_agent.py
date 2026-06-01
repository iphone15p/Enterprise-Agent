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


@tool
def search_web(query: str) -> str:
    """Search the public internet for real-time news and general knowledge."""
    search = DuckDuckGoSearchRun()
    return search.run(query)


@tool
def search_internal_docs(query: str) -> str:
    """Search internal company documents for policies, benefits, and confidential info."""
    return search_knowledge_base(query)


tools = [search_web, search_internal_docs, search_baidu, search_bilibili]
llm_with_tools = llm.bind_tools(tools)


def research_node(state: dict):
    """
    AI Researcher: gathers information using web search and internal docs
    before handing off to the coder.
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

    msg = llm_with_tools.invoke(prompt)

    if msg.tool_calls:
        tool_name = msg.tool_calls[0]["name"]
        args_dict = msg.tool_calls[0]["args"]
        print(f"      -> [Researcher] Using tool: {tool_name}, args: {args_dict}")

        if tool_name == "search_internal_docs":
            tool_result = search_internal_docs.invoke(args_dict)
        elif tool_name == "search_baidu":
            tool_result = search_baidu.invoke(args_dict)
        elif tool_name == "search_bilibili":
            tool_result = search_bilibili.invoke(args_dict)
        else:
            tool_result = search_web.invoke(args_dict)

        print(f"      -> [Researcher] Result preview: {tool_result[:200]}...")

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
        print("      -> [Researcher] No tool needed, answering from context.")
        return {"research_info": msg.content}
