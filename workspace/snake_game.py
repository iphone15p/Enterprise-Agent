# 用户偏好记忆模块
class UserMemory:
    def __init__(self):
        self.data = {}
    
    def store_preference(self, key, value):
        self.data[key] = value
    
    def retrieve_preference(self, key):
        return self.data.get(key)
    
    def verify_storage(self, key, expected_value):
        return self.data.get(key) == expected_value

# 初始化记忆模块
user_memory = UserMemory()

# 1. 确认用户偏好
preference_key = "favorite_animal"
preference_value = "水豚"

# 2. 存储记忆
user_memory.store_preference(preference_key, preference_value)

# 3. 验证存储
is_verified = user_memory.verify_storage(preference_key, "水豚")

# 4. 设定生命周期：长期记忆（无自动过期，仅内存驻留；如需持久化可扩展为文件/DB）
# 当前设计为长期有效，不设 TTL

# 5. 完成确认：静默结束