import json
import asyncio
import sqlite3
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.workflow import app_graph

os.makedirs("data", exist_ok=True)

DB_PATH = "data/history_messages.sqlite3"

with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ui_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            role TEXT,
            content TEXT
        )
    """)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "demo_token")


class AgentRequest(BaseModel):
    task: str = "Write a simple Python script."
    token: str = ""
    thread_id: str = "default_thread"


@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.post("/run_agent")
async def run_agent(req: AgentRequest):
    if req.token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token.")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO ui_chat_history (thread_id, role, content) VALUES (?, ?, ?)",
            (req.thread_id, "user", req.task)
        )

    async def event_stream(current_task: str, current_thread_id: str):
        inputs = {"task": current_task}
        config = {
            "recursion_limit": 25,
            "configurable": {"thread_id": current_thread_id}
        }

        final_answer = ""

        for step in app_graph.stream(inputs, config=config):
            print(f"[Stream] Step output: {list(step.keys())}")

            for node_name, node_data in step.items():
                if isinstance(node_data, dict) and "research_info" in node_data:
                    final_answer = node_data["research_info"]

            yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        if final_answer:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO ui_chat_history (thread_id, role, content) VALUES (?, ?, ?)",
                    (current_thread_id, "assistant", final_answer)
                )

        yield f"data: [DONE]\n\n"

    return StreamingResponse(event_stream(req.task, req.thread_id), media_type="text/event-stream")


@app.get("/get_chat_history")
async def get_chat_history(thread_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT role, content FROM ui_chat_history WHERE thread_id = ? ORDER BY id ASC",
            (thread_id,)
        )
        rows = cursor.fetchall()

    return {"history": [{"role": r, "content": c} for r, c in rows]}
