from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
import time
from app.utils import (
    log_manager,
    ResponseCacheManager,
    ActiveRequestsManager,
    clean_expired_stats
)
import app.config.settings as settings
from app.services import GeminiClient
from app.utils.auth import verify_password
from app.utils.maintenance import api_call_stats_clean

# 创建路由器
dashboard_router = APIRouter(prefix="/api", tags=["dashboard"])

# 全局变量引用，将在init_dashboard_router中设置
key_manager = None
response_cache_manager = None
active_requests_manager = None

def init_dashboard_router(
    key_mgr,
    cache_mgr,
    active_req_mgr
):
    """初始化仪表盘路由器"""
    global key_manager, response_cache_manager, active_requests_manager
    key_manager = key_mgr
    response_cache_manager = cache_mgr
    active_requests_manager = active_req_mgr
    return dashboard_router

@dashboard_router.get("/dashboard-data")
async def get_dashboard_data():
    """获取仪表盘数据的API端点，用于动态刷新"""
    # 先清理过期数据，确保统计数据是最新的
    clean_expired_stats(settings.api_call_stats)
    response_cache_manager.clean_expired()  # 使用管理器清理缓存
    active_requests_manager.clean_completed()  # 使用管理器清理活跃请求
    
    # 获取当前统计数据
    now = datetime.now()
    
    # 计算过去24小时的调用总数
    last_24h_calls = sum(settings.api_call_stats['last_24h']['total'].values())
    
    # 计算过去一小时内的调用总数
    one_hour_ago = now - timedelta(hours=1)
    hourly_calls = 0
    for hour_key, count in settings.api_call_stats['hourly']['total'].items():
        try:
            hour_time = datetime.strptime(hour_key, '%Y-%m-%d %H:00')
            if hour_time >= one_hour_ago:
                hourly_calls += count
        except ValueError:
            continue
    
    # 计算过去一分钟内的调用总数
    one_minute_ago = now - timedelta(minutes=1)
    minute_calls = 0
    for minute_key, count in settings.api_call_stats['minute']['total'].items():
        try:
            minute_time = datetime.strptime(minute_key, '%Y-%m-%d %H:%M')
            if minute_time >= one_minute_ago:
                minute_calls += count
        except ValueError:
            continue
    
    # 获取API密钥使用统计
    api_key_stats = []
    for api_key in key_manager.api_keys:
        # 获取API密钥前8位作为标识
        api_key_id = api_key[:8]
        
        # 计算24小时内的调用次数和按模型分类的调用次数
        calls_24h = 0
        model_stats = {}
        
        if 'by_endpoint' in settings.api_call_stats['last_24h'] and api_key in settings.api_call_stats['last_24h']['by_endpoint']:
            # 遍历所有模型
            for model, model_data in settings.api_call_stats['last_24h']['by_endpoint'][api_key].items():
                model_calls = sum(model_data.values())
                calls_24h += model_calls
                model_stats[model] = model_calls
        
        # 计算使用百分比
        usage_percent = (calls_24h / settings.API_KEY_DAILY_LIMIT) * 100 if settings.API_KEY_DAILY_LIMIT > 0 else 0
        
        # 添加到结果列表
        api_key_stats.append({
            'api_key': api_key_id,
            'calls_24h': calls_24h,
            'limit': settings.API_KEY_DAILY_LIMIT,
            'usage_percent': round(usage_percent, 2),
            'model_stats': model_stats  # 添加按模型分类的统计数据
        })
    
    # 按使用百分比降序排序
    api_key_stats.sort(key=lambda x: x['usage_percent'], reverse=True)
    
    # 获取最近的日志
    recent_logs = log_manager.get_recent_logs(500)  # 获取最近500条日志
    
    # 获取缓存统计
    total_cache = len(response_cache_manager.cache)
    valid_cache = sum(1 for _, data in response_cache_manager.cache.items()
                     if time.time() < data.get('expiry_time', 0))
    cache_by_model = {}
    
    # 分析缓存数据
    for _, cache_data in response_cache_manager.cache.items():
        if time.time() < cache_data.get('expiry_time', 0):
            # 按模型统计缓存
            model = cache_data.get('response', {}).model
            if model:
                if model in cache_by_model:
                    cache_by_model[model] += 1
                else:
                    cache_by_model[model] = 1
    
    # 获取请求历史统计
    history_count = len(settings.client_request_history)
    
    # 获取活跃请求统计
    active_count = len(active_requests_manager.active_requests)
    active_done = sum(1 for task in active_requests_manager.active_requests.values() if task.done())
    active_pending = active_count - active_done
    
    # 返回JSON格式的数据
    return {
        "key_count": len(key_manager.api_keys),
        "model_count": len(GeminiClient.AVAILABLE_MODELS),
        "retry_count": len(key_manager.api_keys),
        "last_24h_calls": last_24h_calls,
        "hourly_calls": hourly_calls,
        "minute_calls": minute_calls,
        "current_time": datetime.now().strftime('%H:%M:%S'),
        "logs": recent_logs,
        "api_key_stats": api_key_stats,
        # 添加配置信息
        "max_requests_per_minute": settings.MAX_REQUESTS_PER_MINUTE,
        "max_requests_per_day_per_ip": settings.MAX_REQUESTS_PER_DAY_PER_IP,
        # 添加版本信息
        "local_version": settings.version["local_version"],
        "remote_version": settings.version["remote_version"],
        "has_update": settings.version["has_update"],
        # 添加流式响应配置
        "fake_streaming": settings.FAKE_STREAMING,
        "fake_streaming_interval": settings.FAKE_STREAMING_INTERVAL,
        # 添加随机字符串配置
        "random_string": settings.RANDOM_STRING,
        "random_string_length": settings.RANDOM_STRING_LENGTH,
        # 添加联网搜索配置
        "search_mode": settings.search["search_mode"],
        "search_prompt": settings.search["search_prompt"],
        # 添加缓存信息
        "cache_entries": total_cache,
        "valid_cache": valid_cache,
        "expired_cache": total_cache - valid_cache,
        "cache_expiry_time": settings.CACHE_EXPIRY_TIME,
        "max_cache_entries": settings.MAX_CACHE_ENTRIES,
        "cache_by_model": cache_by_model,
        "request_history_count": history_count,
        "enable_reconnect_detection": settings.ENABLE_RECONNECT_DETECTION,
        "remove_cache_after_use": settings.REMOVE_CACHE_AFTER_USE,
        # 添加活跃请求池信息
        "active_count": active_count,
        "active_done": active_done,
        "active_pending": active_pending,
        # 添加并发请求配置
        "concurrent_requests": settings.CONCURRENT_REQUESTS,
        "increase_concurrent_on_failure": settings.INCREASE_CONCURRENT_ON_FAILURE,
        "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS
    }

@dashboard_router.post("/reset-stats")
async def reset_stats(password_data: dict):
    """
    重置API调用统计数据
    
    Args:
        password_data (dict): 包含密码的字典
        
    Returns:
        dict: 操作结果
    """
    try:
        if not isinstance(password_data, dict):
            raise HTTPException(status_code=422, detail="请求体格式错误：应为JSON对象")
            
        password = password_data.get("password")
        if not password:
            raise HTTPException(status_code=400, detail="缺少密码参数")
            
        if not isinstance(password, str):
            raise HTTPException(status_code=422, detail="密码参数类型错误：应为字符串")
            
        if not verify_password(password):
            raise HTTPException(status_code=401, detail="密码错误")
        
        # 调用重置函数
        await api_call_stats_clean()
        
        return {"status": "success", "message": "API调用统计数据已重置"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置失败：{str(e)}")
