import os
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings
from tools.rag_tool import search_knowledge_base
from agents.planner_agent import plan_node
from agents.researcher_agent import research_node
from agents.coder_agent import code_node
from agents.reviewer_agent import review_node
from tools.execute_tool import run_code_safely


class AgentState(TypedDict, total=False):
    task: str
    research_info: str
    plan: str
    code: str
    execution_result: str
    feedback: str
    retry_count: int


llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.7
)


def router_judge(state: AgentState) -> Literal["chat_rag", "planner"]:
    """
    Route user input: simple Q&A → chat_rag, complex task → multi-agent pipeline.
    """
    task = state["task"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a precise routing classifier. Analyze the user's input:

1. Return "chat_rag" if the user is: greeting, casual chat, simple Q&A,
   asking about company policy/docs (e.g. "what's the late penalty?", "company benefits?").
2. Return "planner" if the user is asking for: code development, software engineering,
   complex multi-step tasks (e.g. "write a snake game", "build a web scraper").

Reply with ONLY one word: chat_rag or planner."""),
        ("user", "{input}")
    ])

    chain = prompt | llm
    response = chain.invoke({"input": task})
    decision = response.content.strip().lower()

    if "planner" in decision:
        print("[Router] -> Multi-Agent Pipeline (Planner → Researcher → Coder → Reviewer)")
        return "planner"
    else:
        print("[Router] -> Simple Q&A / RAG")
        return "chat_rag"


def chat_rag_node(state: AgentState) -> dict:
    """
    Handle simple queries: try RAG first, fallback to direct LLM chat.
    """
    task = state["task"]
    rag_result = search_knowledge_base(task)

    if "未找到" not in rag_result and "no relevant" not in rag_result.lower():
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional enterprise AI assistant. Answer the user's question "
                       "based on the retrieved internal documents. Use Markdown formatting."),
            ("user", "Retrieved documents:\n{rag_result}\n\nUser question: {input}")
        ])
        chain = prompt | llm
        response = chain.invoke({"rag_result": rag_result, "input": task})
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a friendly and professional enterprise AI assistant. "
                       "Answer the user's question concisely."),
            ("user", "{input}")
        ])
        chain = prompt | llm
        response = chain.invoke({"input": task})

    return {"research_info": response.content}


def execute_node(state: AgentState) -> dict:
    """Execute code produced by the coder agent in a sandbox."""
    code = state.get("code", "")
    if not code:
        return {"execution_result": "Error: No code to execute."}
    result = run_code_safely(code)
    return {"execution_result": result}


def review_decision(state: AgentState) -> Literal["code_node", "__end__"]:
    """
    After review: if PASS or max retries reached → end.
    Otherwise → loop back to coder for a fix.
    """
    feedback = state.get("feedback", "")
    retry_count = state.get("retry_count", 0)

    if "PASS" in feedback:
        print("[Reviewer] Code passed review. Done.")
        return "__end__"
    if retry_count >= 2:
        print("[Reviewer] Max retries reached. Ending pipeline.")
        return "__end__"

    print(f"[Reviewer] Revision needed (attempt {retry_count + 1}/2). Sending back to Coder.")
    return "code_node"


# ==================== Build the StateGraph ====================

workflow = StateGraph(AgentState)

workflow.add_node("chat_rag_node", chat_rag_node)
workflow.add_node("plan_node", plan_node)
workflow.add_node("research_node", research_node)
workflow.add_node("code_node", code_node)
workflow.add_node("execute_node", execute_node)
workflow.add_node("review_node", review_node)

workflow.set_conditional_entry_point(
    router_judge,
    {
        "chat_rag": "chat_rag_node",
        "planner": "plan_node"
    }
)

# Simple path
workflow.add_edge("chat_rag_node", END)

# Multi-agent pipeline: Planner → Researcher → Coder → Execute → Reviewer
workflow.add_edge("plan_node", "research_node")
workflow.add_edge("research_node", "code_node")
workflow.add_edge("code_node", "execute_node")
workflow.add_edge("execute_node", "review_node")

workflow.add_conditional_edges(
    "review_node",
    review_decision,
    {
        "code_node": "code_node",
        "__end__": END
    }
)

app_graph = workflow.compile()
