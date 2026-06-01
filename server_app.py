"""
================================================================================
🧠 AI 智能体协作平台 — FastAPI 服务端
================================================================================

这是项目的「门面」，负责：
1. 提供前端页面（GET /）
2. 接收用户请求，调用 LangGraph 工作流，SSE 流式返回结果（POST /run_agent）
3. 持久化聊天历史到 SQLite（GET /get_chat_history）

启动方式：
    uvicorn server_app:app --host 0.0.0.0 --port 7860
"""

import json
import asyncio
import sqlite3
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.workflow import app_graph   # 👈 导入编译好的 LangGraph 工作流

# 确保 data 目录存在（存放 SQLite 数据库）
os.makedirs("data", exist_ok=True)

DB_PATH = "data/history_messages.sqlite3"

# 启动时自动建表（如果不存在）
with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ui_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,     -- 会话 ID，区分不同对话
            role TEXT,          -- "user" 或 "assistant"
            content TEXT        -- 消息内容
        )
    """)

app = FastAPI()

# 允许跨域（前后端同源时非必需，但保持灵活性）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 鉴权令牌：从环境变量读取，默认 "demo_token"
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "demo_token")


# ==================== 请求模型 ====================

class AgentRequest(BaseModel):
    """POST /run_agent 的 JSON 请求体"""
    task: str = "Write a simple Python script."    # 用户输入
    token: str = ""                                 # 鉴权令牌
    thread_id: str = "default_thread"               # 会话 ID


# ==================== 路由 1：前端页面 ====================

@app.get("/")
async def serve_frontend():
    """返回前端 SPA 页面"""
    return FileResponse("frontend/index.html")


# ==================== 路由 2：运行 Agent（核心接口） ====================

@app.post("/run_agent")
async def run_agent(req: AgentRequest):
    """
    接收用户任务，流式返回 Agent 管线每一步的输出。
    使用 Server-Sent Events (SSE) 协议：data: {...}\n\n
    """

    # 鉴权
    if req.token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token.")

    # 保存用户消息到 SQLite
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO ui_chat_history (thread_id, role, content) VALUES (?, ?, ?)",
            (req.thread_id, "user", req.task)
        )

    async def event_stream(current_task: str, current_thread_id: str):
        """
        SSE 生成器：逐 step 输出 LangGraph 的每一步结果。
        前端收到后通过打字机效果渲染。
        """
        inputs = {"task": current_task}
        config = {
            "recursion_limit": 25,                            # 最多 25 步，防止无限循环
            "configurable": {"thread_id": current_thread_id}  # LangGraph 内置的会话记忆
        }

        final_answer = ""  # 收集最终回复，用于存入数据库

        # 流式调用 LangGraph 工作流
        for step in app_graph.stream(inputs, config=config):
            print(f"[Stream] Step output: {list(step.keys())}")

            # 从每个节点的输出中提取 research_info（最终展示给用户的内容）
            for node_name, node_data in step.items():
                if isinstance(node_data, dict) and "research_info" in node_data:
                    final_answer = node_data["research_info"]

            # 按 SSE 格式输出
            yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        # 工作流结束后，把 AI 最终回复存入 SQLite
        if final_answer:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO ui_chat_history (thread_id, role, content) VALUES (?, ?, ?)",
                    (current_thread_id, "assistant", final_answer)
                )

        # 发送结束信号
        yield f"data: [DONE]\n\n"

    return StreamingResponse(event_stream(req.task, req.thread_id), media_type="text/event-stream")


# ==================== 路由 3：获取聊天历史 ====================

@app.get("/get_chat_history")
async def get_chat_history(thread_id: str):
    """根据会话 ID 返回该会话的所有历史消息"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT role, content FROM ui_chat_history WHERE thread_id = ? ORDER BY id ASC",
            (thread_id,)
        )
        rows = cursor.fetchall()

    return {"history": [{"role": r, "content": c} for r, c in rows]}
