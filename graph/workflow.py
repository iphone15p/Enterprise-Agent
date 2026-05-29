from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.planner_agent import plan_node
from agents.coder_agent import code_node
from agents.reviewer_agent import review_node
# 导入刚写的工具
from tools.file_tool import save_code_to_file

class AgentState(TypedDict):
    task: str
    plan: str
    code: str
    feedback: str

# 【新增】交付节点：专门负责存文件
def save_node(state: dict):
    print("\n[交付专员 Saver] 📦 收到最终完美代码，正在打包保存到本地...")
    # 强行调用工具保存文件
    save_code_to_file.invoke({"code": state["code"]})
    return state

workflow = StateGraph(AgentState)

workflow.add_node("Planner", plan_node)
workflow.add_node("Coder", code_node)
workflow.add_node("Reviewer", review_node)
workflow.add_node("Saver", save_node)  # 加入新员工

workflow.set_entry_point("Planner")
workflow.add_edge("Planner", "Coder")
workflow.add_edge("Coder", "Reviewer")
workflow.add_edge("Saver", END)        # 存完文件，项目才真正结束！

# 【修改】路口检查站
def check_feedback(state: dict):
    if state.get("feedback") == "PASS":
        return "save"      # 没问题 -> 交给交付专员存文件
    else:
        return "continue"  # 有问题 -> 打回给程序员

workflow.add_conditional_edges(
    "Reviewer",
    check_feedback,
    {
        "save": "Saver",     # 走向保存节点
        "continue": "Coder"  # 打回重做
    }
)

agent_executor = workflow.compile()