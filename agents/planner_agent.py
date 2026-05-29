from langchain_openai import ChatOpenAI
from core.config import settings

# 给项目经理配一个活跃一点的大脑 (temperature=0.7)
llm = ChatOpenAI(
    api_key=settings.API_KEY, 
    base_url=settings.BASE_URL, 
    model=settings.MODEL_NAME, 
    temperature=0.7
)

def plan_node(state: dict):
    print("[项目经理 Planner] 👨‍💼 正在拆解任务，制定开发计划...")
    task = state["task"]
    
    prompt = f"你是一个资深项目经理。请为以下任务写一个极其简短的开发步骤计划（不要超过5条）：\n任务：{task}\n注意：只输出纯文本计划，不要废话。"
    
    response = llm.invoke(prompt)
    # 将写好的计划更新到共享的 state (白板) 里
    return {"plan": response.content}