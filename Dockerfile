# 1. 选用 Python 3.11 作为基础环境
FROM python:3.11

# 2. 设置工作目录
WORKDIR /code

# 3. 把依赖清单复制进去，并安装
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# 4. 把我们所有的代码复制进去
COPY . /code

# 5. 设置启动命令 (注意这里用 7860 端口，这是 Hugging Face 的规矩)
CMD ["uvicorn", "server_app:app", "--host", "0.0.0.0", "--port", "7860"]