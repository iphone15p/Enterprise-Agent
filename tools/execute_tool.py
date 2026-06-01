import subprocess
import sys
import os


def run_code_safely(input_data: str) -> str:
    """在沙盒中运行 Python 代码，并捕获输出结果"""
    try:
        # ✨ 终极拦截：判断传进来的是“文件路径”还是“一整坨代码”
        # 如果是以 .py 结尾，且确实是个存在的文件，那它传的就是路径
        if input_data.endswith(".py") and len(input_data) < 255 and os.path.exists(input_data):
            run_file = input_data
        else:
            # 否则，绝对是大模型把代码字符串硬塞进来了！我们自动帮它存入临时文件！
            run_file = "temp_execution.py"
            with open(run_file, "w", encoding="utf-8") as f:
                f.write(input_data)

        # 上帝模式符咒：强迫 Windows 100% 使用 UTF-8 编码
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        # 运行我们处理好的文件
        result = subprocess.run(
            [sys.executable, run_file],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=15
        )

        stdout_str = result.stdout.strip() if result.stdout else "（无内容）"
        stderr_str = result.stderr.strip() if result.stderr else "（无具体报错）"

        if result.returncode == 0:
            return f"✅ 运行成功！终端输出结果: \n{stdout_str}"
        else:
            return f"❌ 运行失败，存在语法或逻辑错误！错误信息: \n{stderr_str}"

    except subprocess.TimeoutExpired:
        return "❌ 运行失败！代码执行超时（超过15秒），可能陷入了死循环。"
    except Exception as e:
        return f"❌ 执行工具发生严重系统异常: {str(e)}"