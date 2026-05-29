import os

os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["ALL_PROXY"] = ""

from graph.workflow import agent_executor


def main():
    print("🚀 企业级多智能体系统已启动...\n")
    inputs = {"task": "用 Python 写一个简单的贪吃蛇小游戏"}

    print("🎬 AI 部门开始运作（节点流式输出中）...\n")

    # 【核心修改】将 invoke 换成 stream
    for step in agent_executor.stream(inputs):
        for node_name, state_update in step.items():
            print(f"\n✅ [{node_name}] 员工刚刚完成了工作！白板更新如下：")

            # 遍历打印该员工刚刚写到白板上的内容
            for key, value in state_update.items():
                print(f"[{key}]:\n{value}")
            print("-" * 50)


if __name__ == "__main__":
    main()