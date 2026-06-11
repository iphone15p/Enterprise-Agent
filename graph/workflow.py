"""
================================================================================
🧠 AI 智能体协作平台 — LangGraph 工作流核心
================================================================================

这是整个项目的「大脑」，负责：
1. 路由判断：是简单问答还是复杂任务？
2. 简单路径：先查 RAG 文档库 → 没命中就联网搜 → 再不行 LLM 裸答
3. 复杂路径：启动 Agent 管线，但查资料类问题会跳过编码环节

管线流程：
    Router（路由判断）
       │
       ├─ 简单/闲聊 → Chat/RAG Node → END
       │
       └─ 需要搜索/写代码 → Planner（规划）
                                ↓
                             Researcher（百度/B站/DuckDuckGo/内部文档）
                                │
                                ├─ 无需编码？→ END ✅
                                │
                                └─ 需要编码？→ Coder（编码）
                                                  ↓
                                               Executor（执行）
                                                  ↓
                                               Reviewer（审查）
                                                  ├─ PASS → SaveCode（保存+自动打开）→ END ✅
                                                  └─ FAIL → 打回重写（最多2次）
"""

import os
import re
import subprocess
import time
from datetime import datetime
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings
from tools.rag_tool import search_knowledge_base
# DP: 新增导入 — chat_rag_node 的联网搜索兜底，和代码保存功能
from tools.search_tool import search_web
from agents.planner_agent import plan_node
from agents.researcher_agent import research_node
from agents.coder_agent import code_node
from agents.reviewer_agent import review_node
from tools.execute_tool import run_code_safely


# ==================== 共享状态定义 ====================
# 所有 Agent 节点共享同一个 state 字典（类似黑板/白板）
# total=False 表示每个字段都是可选的

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
    model=settings.MODEL_NAME,      # 从 .env 读取模型名
    api_key=settings.API_KEY,       # 从 .env 读取 API Key
    base_url=settings.BASE_URL,     # 从 .env 读取端点地址
    temperature=0.7                 # 控制输出随机性
)

# ==================== ① 路由裁判 ====================
# DP: 重写提示词 — 原来几乎所有请求都走 planner，现在画图/写诗/闲聊走快速通道

def router_judge(state: AgentState) -> Literal["chat_rag", "planner"]:
    """
    用大模型判断用户意图：
    - "chat_rag" → 简单问答/闲聊/查文档/画图/写诗（走快速通道，不写代码）
    - "planner" → 需要搜新闻/查资料/写代码（走 Agent 管线）
    """
    task = state["task"]

    # DP: 路由提示词全部改为中文，分类更精准，避免"写个爱心"也触发编码管线
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个精准的路由分类器。分析用户的输入，只返回一个词：

1. 以下情况返回 chat_rag（走快速通道，不写代码）：
   - 闲聊、问候（"你好"、"哈哈"）
   - 画图、写诗、写信、写文章（"画个爱心"、"写首情诗"）
   - 公司内部规定问答（"迟到怎么罚？"）
   - 普通知识问答、解释概念（"什么是AI？"）
   - 简单数学、翻译、建议咨询

2. 只有以下情况才返回 planner（走编码管线）：
   - 明确要求"写代码"、"写个程序"、"开发"（"帮我写个爬虫"）
   - 需要搜索实时新闻、最新消息（"今天有什么科技新闻"）
   - 要求"创建项目"、"做个网站"、"写个游戏"

只能返回一个词：chat_rag 或 planner。"""),
        ("user", "{input}")
    ])

    t0 = time.time()
    chain = prompt | llm
    response = chain.invoke({"input": task})
    decision = response.content.strip().lower()

    print(f"\n{'='*60}")
    print(f"[Router] 📍 用户输入: {task[:80]}...")
    print(f"[Router] 🧠 LLM 路由判断: {decision}（耗时 {time.time()-t0:.1f}秒）")

    if "planner" in decision:
        print(f"[Router] ➡️  进入多Agent管线（规划→调研→编码→审查）")
        return "planner"
    else:
        print(f"[Router] ➡️  进入简单通道（RAG查文档 / 联网搜索 / 自由对话）")
        return "chat_rag"


# ==================== ② 简单问答节点 ====================
# DP: 新增三层兜底 — RAG → 联网搜索 → LLM 裸答，原来只有 RAG → LLM

def chat_rag_node(state: AgentState) -> dict:
    """
    处理不需要写代码的简单请求（四层智能分流）：
    0. 纯闲聊/问候 → 跳过所有搜索，直接 LLM 聊天
    1. 公司相关？→ 查 RAG 文档库
    2. RAG 没命中 → 联网搜索（DuckDuckGo）
    3. 网络也没结果 → LLM 凭自身知识回答
    """
    t_start = time.time()
    task = state["task"]

    # DP: 闲聊快速通道 — 问候/寒暄不触发任何搜索，直接聊天
    _chat_patterns = ["你好", "嗨", "哈哈", "谢谢", "再见", "拜拜", "早上好", "晚上好",
                      "hello", "hi", "hey", "thanks", "bye", "你是谁", "你叫什么"]
    is_pure_chat = any(p in task.lower() for p in _chat_patterns) and len(task) < 20

    if is_pure_chat:
        print(f"[ChatRAG] 💬 纯闲聊，跳过所有搜索，直接 LLM 聊天...")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个友好幽默的 AI 助手，请用中文简短回复用户的问候。"),
            ("user", "{input}")
        ])
        chain = prompt | llm
        response = chain.invoke({"input": task})
        print(f"[ChatRAG] ⏱️  总耗时: {time.time()-t_start:.1f}秒（闲聊模式）")
        return {"research_info": response.content}

    print(f"\n[ChatRAG] 📍 收到问题: {task[:80]}...")
    print(f"[ChatRAG] 🔍 第一步：查本地知识库...")
    t0 = time.time()
    rag_result = search_knowledge_base(task)
    print(f"[ChatRAG] RAG检索完成（耗时 {time.time()-t0:.1f}秒）: {'命中' if '未找到' not in rag_result else '未命中'}（{len(rag_result)}字符）")

    if "未找到" not in rag_result and "no relevant" not in rag_result.lower():
        # RAG 命中 → 基于文档回答
        print(f"[ChatRAG] ✅ RAG命中，LLM生成回答...")
        t_llm = time.time()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是极客科技的企业 AI 助手。请根据检索到的内部文档回答用户问题。"
                       "使用 Markdown 格式排版，加粗关键词，用列表组织内容。"),
            ("user", "内部文档检索结果：\n{rag_result}\n\n用户问题：{input}")
        ])
        chain = prompt | llm
        response = chain.invoke({"rag_result": rag_result, "input": task})
    else:
        # DP: 新增联网搜索兜底 — RAG 没命中时自动用 DuckDuckGo 搜索
        print(f"[ChatRAG] ❌ RAG未命中，第二步：联网搜索（DuckDuckGo）...")
        web_success = False
        try:
            web_result = search_web(task)
            if web_result and len(str(web_result)) > 20:
                web_success = True
                print(f"[ChatRAG] ✅ 联网搜索成功（{len(str(web_result))}字符）")
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "你是一个专业的 AI 助手。请根据联网搜索结果回答用户问题。"
                               "使用 Markdown 格式。尽量注明信息来源。"),
                    ("user", "联网搜索结果：\n{web_result}\n\n用户问题：{input}")
                ])
                chain = prompt | llm
                response = chain.invoke({"web_result": web_result, "input": task})
        except Exception as e:
            print(f"[ChatRAG] 联网搜索失败: {e}")

        if not web_success:
            print(f"[ChatRAG] ❌ 联网也失败，第三步：LLM 裸答...")
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个友好专业的企业 AI 助手，请简洁地回答用户的问题。"),
                ("user", "{input}")
            ])
            chain = prompt | llm
            response = chain.invoke({"input": task})

    print(f"[ChatRAG] ⏱️  总耗时: {time.time()-t_start:.1f}秒")
    return {"research_info": response.content}


# ==================== ③ 代码执行节点 ====================
# DP: 新增自动剥离 Markdown 标记 + 重试计数器

def execute_node(state: AgentState) -> dict:
    """
    把 Coder 生成的代码扔进沙盒运行。
    自动处理两个问题：
    1. 剥离 Markdown 代码块标记（```python ... ```）→ 避免 SyntaxError
    2. 递增重试计数器 → 防止无限循环
    """
    code = state.get("code", "")
    if not code:
        return {"execution_result": "错误：没有可执行的代码。"}

    # DP: 自动剔除 ```python 和 ``` 包裹，否则 subprocess 会报 SyntaxError
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]       # 去掉开头的 ```python
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]      # 去掉结尾的 ```
        code = "\n".join(lines)

    result = run_code_safely(code)
    retry_count = state.get("retry_count", 0) + 1  # DP: 递增重试计数
    return {"execution_result": result, "retry_count": retry_count}


# ==================== ④ 审查决策 ====================
# DP: 新增 save_code 分支 — 通过后先保存代码再结束

def review_decision(state: AgentState) -> Literal["save_code", "code_node", "__end__"]:
    """
    Reviewer 审查完毕后的分流逻辑：
    - 代码通过（PASS）→ 保存代码到文件 → 结束
    - 重试次数 ≥ 2 → 不再重试，结束
    - 否则 → 打回 Coder 重新写
    """
    feedback = state.get("feedback", "")
    retry_count = state.get("retry_count", 0)

    if "PASS" in feedback:
        print("[Reviewer] 代码审查通过，保存代码文件...")
        return "save_code"          # DP: 新增路径 → 先保存再结束
    if retry_count >= 2:
        print("[Reviewer] 已达最大重试次数，管线结束。")
        return "__end__"

    print(f"[Reviewer] 需要修改（第 {retry_count + 1}/2 次重试），打回 Coder。")
    return "code_node"


# ==================== ④½ 代码保存节点 ====================
# DP: 全新节点 — 审查通过后自动保存代码到 generated_code/ 并打开

def save_code_node(state: AgentState) -> dict:
    """
    审查通过后，把代码保存到 generated_code/ 文件夹。
    自动从 task 中提取文件名，并尝试用系统默认程序打开。
    """
    code = state.get("code", "")
    task = state.get("task", "untitled")

    if not code:
        return {}

    # DP: 再次清理 Markdown 标记（双保险）
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)

    # DP: 创建 output 目录，使用 os.path 保证跨平台兼容
    output_dir = os.path.join(os.getcwd(), "generated_code")
    os.makedirs(output_dir, exist_ok=True)

    # DP: 从任务描述提取文件名 + 时间戳
    safe_name = re.sub(r'[^\w]', '_', task)[:20].strip('_')
    if not safe_name:
        safe_name = "script"
    timestamp = datetime.now().strftime("%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{safe_name}_{timestamp}.py")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    abs_path = os.path.abspath(filename)
    print(f"[SaveCode] ✅ 代码已保存到: {abs_path}（{len(code)} 字符）")

    # DP: 自动用系统默认程序打开（os.startfile 在 Windows 上可打开任何文件）
    try:
        if os.name == "nt":
            os.startfile(abs_path)
            print(f"[SaveCode] 📂 已自动打开文件: {abs_path}")
        elif hasattr(os, 'uname') and os.uname().sysname == "Darwin":
            subprocess.run(["open", abs_path])
        else:
            subprocess.run(["xdg-open", abs_path])
    except Exception as e:
        print(f"[SaveCode] ⚠️  无法自动打开（文件已保存，请手动打开）: {e}")
        print(f"[SaveCode] 文件路径: {abs_path}")

    return {"research_info": f"✅ 代码已保存到 `{abs_path}`，已自动打开编辑器。"}


# ==================== ⑤ 调研后置判断：需要写代码吗？ ====================
# DP: 全新节点 — 查资料类问题跳过编码管线，只让写代码的任务走 Coder

def need_code_decision(state: AgentState) -> Literal["code_node", "__end__"]:
    """
    Researcher 调研完毕后，看看 Planner 的计划是否要求写代码：
    - 计划说"无需编码" → 直接结束，跳过 Coder/Execute/Reviewer
    - 计划说要写代码 → 进入编码管线
    """
    plan = state.get("plan", "")
    if "无需编码" in plan or "SIMPLE_QUERY" in plan:
        print("[Decision] ✅ 计划明确不需要编码，直接结束（跳过编码管线）")
        return "__end__"
    else:
        print("[Decision] 📝 计划要求编写代码，进入编码管线")
        return "code_node"


# ==================== 🏗️ 组装工作流图 ====================

workflow = StateGraph(AgentState)

# 注册所有节点
workflow.add_node("chat_rag_node", chat_rag_node)        # 简单问答 + RAG + 联网搜索
workflow.add_node("plan_node", plan_node)                 # 规划 Agent
workflow.add_node("research_node", research_node)         # 调研 Agent（百度/B站/DuckDuckGo/内部文档）
workflow.add_node("code_node", code_node)                 # 编码 Agent
workflow.add_node("execute_node", execute_node)           # 沙盒执行
workflow.add_node("review_node", review_node)             # 审查 Agent
workflow.add_node("save_code_node", save_code_node)       # DP: 新增 — 保存代码到文件

# 入口：路由裁判 → 分流
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

# DP: 调研后判断（原来是固定走 Coder，现在看情况跳过编码）
workflow.add_conditional_edges(
    "research_node",
    need_code_decision,
    {
        "code_node": "code_node",    # 需要写代码 → 进入编码管线
        "__end__": END               # 不需要 → 直接结束
    }
)

workflow.add_edge("code_node", "execute_node")
workflow.add_edge("execute_node", "review_node")

# DP: 审查后分流（新增 save_code 路径）
workflow.add_conditional_edges(
    "review_node",
    review_decision,
    {
        "save_code": "save_code_node",   # DP: 通过 → 先保存代码
        "code_node": "code_node",        # 打回 Coder 重写
        "__end__": END                   # 达到最大重试 → 结束
    }
)

# DP: 保存完代码 → 结束
workflow.add_edge("save_code_node", END)

# 编译导出 → 供 server_app.py 调用
app_graph = workflow.compile()
