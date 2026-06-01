# 强制销毁缓存重构 2026
print("================ 我是真正的 server_app.py！我被执行了！================")

import json
import asyncio
import sqlite3
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
# 🌟 核心导入线：把 workflow 编译出来的核心大脑拿过来用
from graph.workflow import app_graph

# 🌟 新增：如果不存在 data 文件夹，就自动创建一个
os.makedirs("data", exist_ok=True)

# 🌟 修改路径：把原本的 "history_messages.sqlite3" 全部改到 data 文件夹里
DB_PATH = "data/history_messages.sqlite3"

# 自动创建一张只存纯文本的极轻量聊天记录表
with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ui_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            role TEXT,
            content TEXT
        )
    """)
# 1. 实例化一个 FastAPI 房子
app = FastAPI()

# 2. 签发 CORS 跨域通行证
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MY_SECRET_TOKEN = "dq67_nb_888"


# 3. 根目录路由
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")


# 4. 运行 Agent 的主接口
@app.get("/run_agent")
async def run_agent(
        task: str = Query("写一个获取今天国内实时热点新闻的 Python 爬虫..."),
        token: str = Query(None),
        thread_id: str = Query("default_thread")
):
    if token != MY_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="🚨 密码错误！")

    # 🌟【保存逻辑 1】：用户一说话，立刻把用户的问题存入 SQL 历史表
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO ui_chat_history (thread_id, role, content) VALUES (?, ?, ?)",
            (thread_id, "user", task)
        )

    async def event_stream(current_task: str, current_thread_id: str):
        inputs = {"task": current_task}

        # 🌟 强行锁死 thread_id！不管前端怎么乱传时间戳，我们在后端都认准这一个记忆库！
        config = {
            "recursion_limit": 10,
            # ✅ 新代码：让大模型的上下文记忆与前端的侧边栏窗口完全一一对应
            "configurable": {"thread_id": current_thread_id}  # 👈 直接写死它！
        }

        final_answer = "" # 🌟【新增】：初始化一个变量，用来装 AI 最终吐出的完整回答

        # 🌟 这里正在使用的就是上面导入的 agent_executor，绝对不会再报未定义了！
        for step in app_graph.stream(inputs, config=config):
            # 🌟 新增：拦截并偷看大模型到底传回了什么数据！
            print(f"\n📦 抓包偷看最终数据: {step}")

            # 🌟【保存逻辑 2】：在流式输出过程中，动态拦截并抓取 AI 的最终研究结论
            for node_name, node_data in step.items():
                if isinstance(node_data, dict) and "research_info" in node_data:
                    final_answer = node_data["research_info"] # 抓到了就更新给变量

            yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        # 🌟【保存逻辑 3】：当整个 Agent 工作流全部迭代完毕后，把抓到的最终回答砸进数据库
        if final_answer:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO ui_chat_history (thread_id, role, content) VALUES (?, ?, ?)",
                    (current_thread_id, "assistant", final_answer)
                )

        yield f"data: [DONE]\n\n"

    return StreamingResponse(event_stream(task, thread_id), media_type="text/event-stream")


@app.get("/get_chat_history")
async def get_chat_history(thread_id: str):
    # 🌟【已修复】：把原先硬编码的 "history_messages.sqlite3" 替换为统一的变量 DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT role, content FROM ui_chat_history WHERE thread_id = ? ORDER BY id ASC",
            (thread_id,)
        )
        rows = cursor.fetchall()

    return {"history": [{"role": r, "content": c} for r, c in rows]}