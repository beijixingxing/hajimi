import sys,asyncio
#from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # 替换为异步调度器
from app.utils.logging import log
from app.utils.stats import clean_expired_stats
from app.utils import check_version
from zoneinfo import ZoneInfo
from app.config import settings
import copy  # 添加copy模块导入

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    全局异常处理函数
    
    处理未捕获的异常，并记录到日志中
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.excepthook(exc_type, exc_value, exc_traceback)
        return
    from app.utils.error_handling import translate_error
    error_message = translate_error(str(exc_value))
    log('error', f"未捕获的异常: {error_message}", status_code=500, error_message=error_message)
'''
def schedule_cache_cleanup(response_cache_manager, active_requests_manager):
    """
    设置定期清理缓存和活跃请求的定时任务
    顺便定时检查更新
    Args:
        response_cache_manager: 响应缓存管理器实例
        active_requests_manager: 活跃请求管理器实例
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(response_cache_manager.clean_expired, 'interval', minutes=1)  # 每分钟清理过期缓存
    scheduler.add_job(active_requests_manager.clean_completed, 'interval', seconds=30)  # 每30秒清理已完成的活跃请求
    scheduler.add_job(active_requests_manager.clean_long_running, 'interval', minutes=5, args=[300])  # 每5分钟清理运行超过5分钟的任务
    scheduler.add_job(clean_expired_stats, 'interval', minutes=5,args=[api_call_stats])  # 每5分钟清理过期的统计数据
    scheduler.add_job(check_version, 'interval', minutes=1)  # 每4小时检查更新
    scheduler.start()
    
    return scheduler

'''
def schedule_cache_cleanup(response_cache_manager, active_requests_manager):
    """
    设置定期清理缓存和活跃请求的定时任务
    顺便定时检查更新
    Args:
        response_cache_manager: 响应缓存管理器实例
        active_requests_manager: 活跃请求管理器实例
    """
    beijing_tz = ZoneInfo("Asia/Shanghai")
    scheduler = AsyncIOScheduler(timezone=beijing_tz)  # 使用 AsyncIOScheduler 替代 BackgroundScheduler
    
    # 添加任务时直接传递异步函数（无需额外包装）
    scheduler.add_job(response_cache_manager.clean_expired, 'interval', minutes=1)
    scheduler.add_job(active_requests_manager.clean_completed, 'interval', seconds=30)
    scheduler.add_job(active_requests_manager.clean_long_running, 'interval', minutes=5, args=[300])
    scheduler.add_job(clean_expired_stats, 'interval', minutes=5, args=[settings.api_call_stats])
    scheduler.add_job(check_version, 'interval', hours=4)
    scheduler.add_job(api_call_stats_clean, 'cron', hour=15,minute=0) 
    scheduler.start()
    return scheduler

async def api_call_stats_clean():
    """
    每天定时重置API调用统计数据
    
    将settings.api_call_stats重置为初始空结构
    """
    from app.utils.logging import log
    
    try:
        # 记录重置前的状态
        log('info', "开始重置API调用统计数据")
        
        # 创建一个全新的空结构
        new_stats = {
            'last_24h': {
                'total': {},
                'by_endpoint': {}
            },
            'hourly': {
                'total': {},
                'by_endpoint': {}
            },
            'minute': {
                'total': {},
                'by_endpoint': {}
            }
        }
        
        # 使用深拷贝确保完全替换原结构
        settings.api_call_stats = copy.deepcopy(new_stats)
        
        # 验证重置是否成功
        if (settings.api_call_stats['last_24h']['total'] == {} and 
            settings.api_call_stats['hourly']['total'] == {} and 
            settings.api_call_stats['minute']['total'] == {}):
            log('info', "API调用统计数据已成功重置")
        else:
            log('error', "API调用统计数据重置可能未完全成功")
            
    except Exception as e:
        log('error', f"重置API调用统计数据时发生错误: {str(e)}")
        raise