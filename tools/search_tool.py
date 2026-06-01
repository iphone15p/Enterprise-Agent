from langchain_community.tools import DuckDuckGoSearchRun

def search_web(query: str) -> str:
    """
    接收一个搜索词，去互联网上搜索，并返回排名前几的网页摘要信息。
    """
    print(f"      🔍 [搜索核心] 正在全网检索: {query}")
    search = DuckDuckGoSearchRun()
    try:
        # 调用 DuckDuckGo 搜索并返回结果
        result = search.invoke(query)
        return result
    except Exception as e:
        return f"搜索失败: {str(e)}"