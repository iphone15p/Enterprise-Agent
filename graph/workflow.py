"""
================================================================================
🧠 AI 智能体协作平台 — LangGraph 工作流核心
================================================================================

这是整个项目的「大脑」，负责：
1. 路由判断：是简单问答还是复杂任务？
2. 简单路径：直接调 LLM 或查 RAG 文档库
3. 复杂路径：启动四 Agent 协作管线

管线流程：
    Router（路由判断）
       │
       ├─ 简单/闲聊 → Chat/RAG Node → END
       │
       └─ 复杂任务 → Planner（规划）
                        ↓
                     Researcher（调研）
                        ↓
                     Coder（编码）
                        ↓
                     Executor（执行）→ 代码跑通了吗？
                        ↓
                     Reviewer（审查）
                        ├─ PASS → END ✅
                        └─ FAIL → 打回 Coder 重写（最多 2 次）
"""

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


# ==================== 共享状态定义 ====================
# 所有 Agent 节点共享同一个 state 字典（类似黑板/白板）
# total=False 表示每个字段都是可选的，不需要所有节点都填

class AgentState(TypedDict, total=False):
    task: str              # 用户原始输入
    research_info: str     # AI 回复 / 调研结果（最终展示给用户的内容）
    plan: str              # Planner 制定的执行计划
    code: str              # Coder 生成的代码
    execution_result: str  # Executor 的沙盒运行结果
    feedback: str          # Reviewer 的审查意见
    retry_count: int       # 当前重试次数（最多 2 次）


# ==================== LLM 实例 ====================
# 使用阿里云 DashScope 的通义千问（qwen-plus），通过 OpenAI 兼容接口调用

llm = ChatOpenAI(
    api_key=settings.API_KEY,       # 从 .env 读取
    base_url=settings.BASE_URL,     # DashScope 兼容端点
    model=settings.MODEL_NAME,      # 默认 qwen-plus
    temperature=0.7
)


# ==================== ① 路由裁判 ====================

def router_judge(state: AgentState) -> Literal["chat_rag", "planner"]:
    """
    用大模型判断用户意图：
    - "chat_rag" → 简单问答/闲聊/查文档（走快速通道）
    - "planner" → 复杂工程任务（走四 Agent 管线）
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


# ==================== ② 简单问答节点 ====================

def chat_rag_node(state: AgentState) -> dict:
    """
    处理不需要写代码的简单请求：
    1. 先查本地知识库（RAG），看看公司文档里有没有答案
    2. 找不到就用 LLM 直接回答
    """
    task = state["task"]
    rag_result = search_knowledge_base(task)

    if "未找到" not in rag_result and "no relevant" not in rag_result.lower():
        # RAG 命中 → 基于文档回答
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional enterprise AI assistant. Answer the user's question "
                       "based on the retrieved internal documents. Use Markdown formatting."),
            ("user", "Retrieved documents:\n{rag_result}\n\nUser question: {input}")
        ])
        chain = prompt | llm
        response = chain.invoke({"rag_result": rag_result, "input": task})
    else:
        # RAG 未命中 → 自由对话
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a friendly and professional enterprise AI assistant. "
                       "Answer the user's question concisely."),
            ("user", "{input}")
        ])
        chain = prompt | llm
        response = chain.invoke({"input": task})

    return {"research_info": response.content}


# ==================== ③ 代码执行节点 ====================

def execute_node(state: AgentState) -> dict:
    """
    把 Coder 生成的代码扔进沙盒运行。
    自动处理两个常见问题：
    1. 剥离 Markdown 代码块标记（```python ... ```）
    2. 递增重试计数器（防止无限循环）
    """
    code = state.get("code", "")
    if not code:
        return {"execution_result": "Error: No code to execute."}

    # 自动剔除 ```python 和 ``` 包裹
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]       # 去掉开头的 ```python
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]      # 去掉结尾的 ```
        code = "\n".join(lines)

    result = run_code_safely(code)
    retry_count = state.get("retry_count", 0) + 1
    return {"execution_result": result, "retry_count": retry_count}


# ==================== ④ 审查决策 ====================

def review_decision(state: AgentState) -> Literal["code_node", "__end__"]:
    """
    Reviewer 审查完毕后的分流逻辑：
    - 代码通过（PASS）→ 结束
    - 重试次数 ≥ 2 → 不再重试，结束
    - 否则 → 打回 Coder 重新写
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


# ==================== 🏗️ 组装工作流图 ====================

workflow = StateGraph(AgentState)

# 注册所有节点
workflow.add_node("chat_rag_node", chat_rag_node)        # 简单问答
workflow.add_node("plan_node", plan_node)                 # 规划 Agent
workflow.add_node("research_node", research_node)         # 调研 Agent
workflow.add_node("code_node", code_node)                 # 编码 Agent
workflow.add_node("execute_node", execute_node)           # 沙盒执行
workflow.add_node("review_node", review_node)             # 审查 Agent

# 入口：路由裁判 → 分流到简单或复杂路径
workflow.set_conditional_entry_point(
    router_judge,
    {
        "chat_rag": "chat_rag_node",   # → 简单路径
        "planner": "plan_node"         # → 复杂路径
    }
)

# 简单路径：直接回答 → 结束
workflow.add_edge("chat_rag_node", END)

# 复杂路径：规划 → 调研 → 编码 → 执行 → 审查
workflow.add_edge("plan_node", "research_node")
workflow.add_edge("research_node", "code_node")
workflow.add_edge("code_node", "execute_node")
workflow.add_edge("execute_node", "review_node")

# 审查后的条件跳转：通过→结束，未通过→重写
workflow.add_conditional_edges(
    "review_node",
    review_decision,
    {
        "code_node": "code_node",    # 打回 Coder 重写
        "__end__": END               # 结束
    }
)

# 编译导出 → 供 server_app.py 调用
app_graph = workflow.compile()
