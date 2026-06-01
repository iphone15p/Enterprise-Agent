import os
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings
# 🌟【已修复】：完美导入你真实的 RAG 检索函数名
from tools.rag_tool import search_knowledge_base


# 1. 定义标准状态账本
class AgentState(TypedDict):
    task: str  # 用户输入
    research_info: str  # AI 回答


# 🌟【已修复】：彻底切换为阿里云通义千问 qwen-plus 专属配置
# 提示：推荐在电脑环境变量中配置 DASHSCOPE_API_KEY，或者直接把密码写在下面引号里
llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.MODEL_NAME,
    temperature=0.7
)


# ================= 🧭 意图路由裁判 =================
def router_judge(state: AgentState) -> Literal["chat", "rag"]:
    """
    裁判节点：用大模型判断用户是要闲聊（chat）还是查公司机密（rag）
    """
    task = state["task"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个高精度的路由裁判。请分析用户的输入，将其分类为以下两类之一：

        1. 如果用户是在进行日常问候、闲聊、开玩笑或发送无意义乱码（例如："你好"、"哈吉米"、"我就完了"），请返回：chat
        2. 如果用户是在明确询问关于公司内部机密、规章制度、考勤、迟到惩罚等文档内容，请返回：rag

        注意：你只能返回 'chat' 或 'rag' 这几个英文字母，绝对不能包含任何其他标点或空格。"""),
        ("user", "{input}")
    ])

    chain = prompt | llm
    response = chain.invoke({"input": task})
    decision = response.content.strip().lower()

    if "rag" in decision:
        print("🔮 [路由决策] ➡️ 导向 RAG 检索通道（查阅公司文档）")
        return "rag"
    else:
        print("🔮 [路由决策] ➡️ 导向 自由闲聊通道（不查文档）")
        return "chat"


# ================= 🏪 执行节点 1：自由闲聊通道 =================
def chat_node(state: AgentState) -> dict:
    """
    闲聊节点：qwen-plus 直接陪聊，不碰向量库
    """
    task = state["task"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个幽默、有情商的 AI 助手。现在用户正在找你闲聊。请根据用户的输入进行轻松、自然的回复。"),
        ("user", "{input}")
    ])

    chain = prompt | llm
    response = chain.invoke({"input": task})
    return {"research_info": response.content}


# ================= 📂 执行节点 2：RAG 检索通道 =================
def rag_node(state: AgentState) -> dict:
    """
    RAG 节点：调用你写好的本地知识库引擎，去翻本地的 chroma_db
    """
    task = state["task"]

    # 🌟【已修复】：调用你真正的本地库检索函数
    rag_result = search_knowledge_base(task)

    return {"research_info": rag_result}


# ================= 🏗️ 组装持久化工作流 =================

workflow = StateGraph(AgentState)

# 挂载节点
workflow.add_node("chat_node", chat_node)
workflow.add_node("rag_node", rag_node)

# 设置条件分流入口
workflow.set_conditional_entry_point(
    router_judge,
    {
        "chat": "chat_node",
        "rag": "rag_node"
    }
)

# 汇聚出口
workflow.add_edge("chat_node", END)
workflow.add_edge("rag_node", END)

# 编译导出大脑
app_graph = workflow.compile() # 把所有功能组装一起给外部调用