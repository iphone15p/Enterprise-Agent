import os
from langchain_core.tools import tool


@tool
def save_code_to_file(code: str, filename: str = "snake_game.py") -> str:
    """
    当测试员(Reviewer)审核通过，且你写出最终完美版本的代码后，必须调用此工具将代码保存到本地。
    """
    # 自动清理大模型输出时可能带有的 ```python 标记
    clean_code = code.replace("```python", "").replace("```", "").strip()

    # 获取当前项目的根目录，并保存文件
    file_path = os.path.join(os.getcwd(), filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(clean_code)

    print(f"\n[系统后台] 💾 触发保存工具！代码已成功生成实体文件：{filename}")
    return f"文件已保存至: {file_path}"