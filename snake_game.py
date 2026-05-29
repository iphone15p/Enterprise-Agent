# -*- coding: utf-8 -*-
"""
hello.py —— 经典的“Hello World”程序（带完整中文注释版）
功能说明：
    本脚本用于演示最基础的Python程序结构与标准输出操作。
    执行后将在控制台打印字符串 "Hello World"，验证Python环境是否正常运行。

开发背景：
    "Hello World" 是编程学习中的传统入门示例，旨在快速验证开发环境配置正确、
    解释器可正常执行代码，并建立对程序基本结构（如print函数、字符串字面量）的直观认知。

注意事项：
    - 文件编码声明为UTF-8（# -*- coding: utf-8 -*-），确保中文注释在所有系统中正确解析；
    - print() 函数是Python 3的标准输出函数，括号不可省略；
    - 输出内容为纯英文字符串，符合国际通用惯例，避免因本地化设置导致的兼容性问题；
    - 本文件不依赖任何外部模块，可直接在任意标准Python 3.x环境中运行（推荐3.6+）。

使用方法：
    1. 将本文件保存为 hello.py（确保扩展名为 .py）；
    2. 打开终端（Windows：cmd/PowerShell；macOS/Linux：Terminal）；
    3. 切换至该文件所在目录（例如：cd /path/to/project）；
    4. 执行命令：python hello.py 或 python3 hello.py；
    5. 观察终端输出是否严格等于（无前后空格）："Hello World"

预期输出（stdout）：
    Hello World

版本信息：
    创建日期：2024年（当前年份）
    Python兼容性：3.6 及以上版本
"""

# 主程序逻辑：调用内置print函数，向标准输出（stdout）打印字符串 "Hello World"
print("Hello World")