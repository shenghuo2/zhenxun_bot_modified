"""
撤回记录插件配置
"""

# 仅监控这些群的消息和撤回事件
MONITORED_GROUP_IDS: list[int] = [
    1040437158,  
    555741990,
    912045649,
    955100916,
]

# `#撤回查询` 默认返回条数
DEFAULT_QUERY_LIMIT: int = 10

# `#撤回查询` 最大返回条数
MAX_QUERY_LIMIT: int = 50
