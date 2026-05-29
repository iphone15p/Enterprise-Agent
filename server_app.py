print("================ 我是真正的 server_app.py！我被执行了！================")
from fastapi import FastAPI
# 1. 实例化一个 FastAPI 房子（后端服务器）
app = FastAPI()
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from graph.workflow import agent_executor



# 2. 核心知识点：配置跨域 (CORS)
# 因为等会儿我们的前端 HTML 网页和后端不在同一个端口，默认会被浏览器拦截。
# 加上这段代码，就是给服务器发了一张“通行证”，允许任何前端来访问我们。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. 核心知识点：生成器函数 (yield)
async def event_stream(task: str):
    """
    这个函数负责盯着 AI 团队，他们每做完一步，就立刻把数据“吐”给前端
    """
    inputs = {"task": task}
    config = {"recursion_limit": 10}  # 依然保留我们的防破产机制

    # agent_executor.stream 会一步步产出结果
    for step in agent_executor.stream(inputs, config=config):
        # 【重点】SSE 协议规定，流式数据必须以 "data: " 开头，以 "\n\n" 结尾！
        # 我们把字典转换成 JSON 字符串传输出去
        yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
        # 稍微停顿0.1秒，防止数据跑得太快，前端渲染卡顿
        await asyncio.sleep(0.1)
        # event_stream（负责生产）：里面的 yield 负责把 LangGraph 的每一个状态一节一节地切出来。
    # 当全部执行完毕后，给前端发送一个暗号 "[DONE]"，告诉它结束了
    yield f"data: [DONE]\n\n"


# 4. 开放一扇 API 大门，提供给前端调用
@app.get("/run_agent")
async def run_agent(task: str = "写一个输出 Hello World 的 Python 脚本"):
    # 当有人访问 /run_agent 时，返回我们上面写的流式数据
    return StreamingResponse(event_stream(task), media_type="text/event-stream")