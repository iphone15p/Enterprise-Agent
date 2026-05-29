import os
from dotenv import load_dotenv

# 自动读取 .env 文件
load_dotenv()

class Settings:
    """全局配置类"""
    API_KEY: str = os.getenv("API_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen-plus")

# 实例化配置对象
settings = Settings()