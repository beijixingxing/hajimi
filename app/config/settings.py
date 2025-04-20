import os
import pathlib
import logging
from datetime import datetime, timedelta

# 基础目录设置
BASE_DIR = pathlib.Path(__file__).parent.parent

# 流式响应配置
FAKE_STREAMING = os.environ.get("FAKE_STREAMING", "true").lower() in ["true", "1", "yes"]
# 假流式请求的空内容返回间隔（秒）
FAKE_STREAMING_INTERVAL = float(os.environ.get("FAKE_STREAMING_INTERVAL", "1"))

#随机字符串
RANDOM_STRING = os.environ.get("RANDOM_STRING", "true").lower() in ["true", "1", "yes"]
RANDOM_STRING_LENGTH = int(os.environ.get("RANDOM_STRING_LENGTH", "5"))
# 是否启用Vertex AI
ENABLE_VERTEX = os.environ.get("ENABLE_VERTEX", "false").lower() in ["true", "1", "yes"]
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
#GOOGLE_CREDENTIALS_JSON = r''
# 日志配置
logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.access").disabled = True

# 安全配置
PASSWORD = os.environ.get("PASSWORD", "123").strip('"')
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "30"))
MAX_REQUESTS_PER_DAY_PER_IP = int(os.environ.get("MAX_REQUESTS_PER_DAY_PER_IP", "600"))
RETRY_DELAY = 1
MAX_RETRY_DELAY = 16

# 并发请求配置
CONCURRENT_REQUESTS = int(os.environ.get("CONCURRENT_REQUESTS", "1"))  # 默认并发请求数
INCREASE_CONCURRENT_ON_FAILURE = int(os.environ.get("INCREASE_CONCURRENT_ON_FAILURE", "0"))  # 失败时增加的并发数
MAX_CONCURRENT_REQUESTS = int(os.environ.get("MAX_CONCURRENT_REQUESTS", "2"))  # 最大并发请求数

# API密钥使用限制
# 默认每个API密钥每24小时可使用次数
API_KEY_DAILY_LIMIT = int(os.environ.get("API_KEY_DAILY_LIMIT", "100"))

# 缓存配置
CACHE_EXPIRY_TIME = int(os.environ.get("CACHE_EXPIRY_TIME", "1200"))  # 默认20分钟
MAX_CACHE_ENTRIES = int(os.environ.get("MAX_CACHE_ENTRIES", "500"))  # 默认最多缓存500条响应
REMOVE_CACHE_AFTER_USE = os.environ.get("REMOVE_CACHE_AFTER_USE", "true").lower() in ["true", "1", "yes"]

# 请求历史配置
REQUEST_HISTORY_EXPIRY_TIME = int(os.environ.get("REQUEST_HISTORY_EXPIRY_TIME", "600"))  # 默认10分钟
ENABLE_RECONNECT_DETECTION = os.environ.get("ENABLE_RECONNECT_DETECTION", "true").lower() in ["true", "1", "yes"]

search={
    "search_mode":os.environ.get("SEARCH_MODE", "false").lower() in ["true", "1", "yes"],
    "search_prompt":os.environ.get("SEARCH_PROMPT", "（使用搜索工具联网搜索，需要在content中结合搜索内容）").strip('"')
}

version={
    "local_version":"0.0.0",
    "remote_version":"0.0.0",
    "has_update":False
}

# API调用统计
api_call_stats = {
    'last_24h': {
        'total': {},  # 按小时统计过去24小时总调用次数
        'by_endpoint': {}  # 按API端点分类的24小时统计（也用于API密钥统计）
    },
    'hourly': {
        'total': {},  # 按小时统计过去一小时总调用次数
        'by_endpoint': {}  # 按API端点分类的小时统计（也用于API密钥统计）
    },
    'minute': {
        'total': {},  # 按分钟统计过去一分钟总调用次数
        'by_endpoint': {}  # 按API端点分类的分钟统计（也用于API密钥统计）
    }
}

# 客户端IP到最近请求的映射，用于识别重连请求
client_request_history = {}

# 模型屏蔽列表配置
# 默认屏蔽的模型列表
DEFAULT_BLOCKED_MODELS = []

# 从环境变量中读取屏蔽模型列表，如果未设置则使用默认列表
# 环境变量格式应为逗号分隔的模型名称字符串
BLOCKED_MODELS = os.environ.get("BLOCKED_MODELS", ",".join(DEFAULT_BLOCKED_MODELS))
# 将字符串转换为列表
BLOCKED_MODELS = [model.strip() for model in BLOCKED_MODELS.split(",") if model.strip()]