import json
from langchain_core.tools import tool


@tool
def get_weather(city_name: str) -> str:
    """
    当用户询问特定城市的天气时，必须调用此工具获取最新天气数据。
    参数:
        city_name: 需要查询天气的城市名称，例如：北京、上海
    """
    print(f"\n[系统后台] 🔧 工具被唤醒：正在查询数据库中 {city_name} 的天气...")

    mock_database = {
        "北京": "晴朗，气温 25°C，非常适合户外活动。",
        "上海": "大雨，气温 18°C，路面湿滑。",
        "深圳": "台风预警，气温 30°C，请尽量待在室内。"
    }

    result = mock_database.get(city_name, f"未找到 {city_name} 的天气数据。")
    return json.dumps({"city": city_name, "weather_info": result}, ensure_ascii=False)