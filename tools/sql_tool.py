"""
数据库查询工具
用于执行 SQL 查询操作
"""
import sqlite3
from typing import List, Dict, Any, Optional


class SQLTool:
    """数据库查询工具类"""
    
    def __init__(self, database_url: str = "sqlite:///./app.db"):
        """
        初始化数据库工具
        
        Args:
            database_url: 数据库连接URL
        """
        # 简化处理，实际应该解析 database_url
        self.database_path = database_url.replace("sqlite:///", "")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询
        
        Args:
            query: SQL 查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # 如果是 SELECT 查询
            if query.strip().upper().startswith("SELECT"):
                results = [dict(row) for row in cursor.fetchall()]
                conn.close()
                return results
            else:
                conn.commit()
                conn.close()
                return []
                
        except Exception as e:
            return [{"error": str(e)}]
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        批量执行 SQL 语句
        
        Args:
            query: SQL 查询语句
            params_list: 参数列表
            
        Returns:
            受影响的行数
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            row_count = cursor.rowcount
            conn.close()
            return row_count
        except Exception as e:
            raise Exception(f"批量执行失败: {str(e)}")


def query_database(query: str, params: tuple = ()) -> str:
    """
    查询数据库的便捷函数
    
    Args:
        query: SQL 查询语句
        params: 查询参数
        
    Returns:
        格式化的查询结果字符串
    """
    tool = SQLTool()
    results = tool.execute_query(query, params)
    
    if not results:
        return "查询结果为空"
    
    if "error" in results[0]:
        return f"查询失败: {results[0]['error']}"
    
    # 格式化输出结果
    output = "查询结果:\n"
    for i, row in enumerate(results, 1):
        output += f"\n第 {i} 行:\n"
        for key, value in row.items():
            output += f"  {key}: {value}\n"
    
    return output


# 测试代码
if __name__ == "__main__":
    # 示例：创建表并查询
    print(query_database("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"))
    print(query_database("INSERT OR IGNORE INTO users (id, name) VALUES (1, '张三')"))
    print(query_database("SELECT * FROM users"))
