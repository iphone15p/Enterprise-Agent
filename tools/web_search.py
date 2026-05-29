import json
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """
    当用户询问最新新闻、攻略、百科知识或需要联网查询的内容时，必须调用此工具。
    参数:
        query: 搜索关键词，例如：'北京旅游攻略' 或 '大模型最新进展'
    """
    print(f"\n[系统后台] 🌐 搜索工具被唤醒：正在全网搜索关键词 -> {query}")
    
    # 模拟真实搜索引擎返回的网页数据
    mock_search_results = {
        "大模型": "最新资讯：AI 智能体（Agent）技术已经成为各大互联网公司的核心发力点。",
        "旅游攻略": "北京旅游热门推荐：故宫、八达岭长城、颐和园。温馨提示：热门景点建议提前至少 3 天在线预约门票，否则可能无法入园。"
    }
    
    # 根据用户的关键词，返回对应的模拟结果
    result = "未搜索到相关确切信息，请尝试更换关键词。"
    for key, value in mock_search_results.items():
        if key in query:
            result = value
            break
            
    return json.dumps({"query": query, "search_result": result}, ensure_ascii=False)