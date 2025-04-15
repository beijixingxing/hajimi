from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.models import ErrorResponse
from app.services import GeminiClient
from app.utils import (
    APIKeyManager, 
    test_api_key, 
    format_log_message, 
    log_manager,
    ResponseCacheManager,
    ActiveRequestsManager,
    clean_expired_stats,
    update_api_call_stats,
    check_version,
    schedule_cache_cleanup,
    handle_exception,
    log
)
from app.api import router, init_router, dashboard_router, init_dashboard_router
import app.config.settings as settings
from app.config.safety import SAFETY_SETTINGS, SAFETY_SETTINGS_G2
import os
import json
import asyncio
import time
import logging
from datetime import datetime, timedelta
import sys
import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor

# 设置模板目录
BASE_DIR = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(limit="50M")

# --------------- 全局实例 ---------------

# 初始化API密钥管理器
key_manager = APIKeyManager()
current_api_key = key_manager.get_available_key()

# 创建全局缓存字典，将作为缓存管理器的内部存储
response_cache = {}

# 初始化缓存管理器，使用全局字典作为存储
response_cache_manager = ResponseCacheManager(
    expiry_time=settings.CACHE_EXPIRY_TIME,
    max_entries=settings.MAX_CACHE_ENTRIES,
    remove_after_use=settings.REMOVE_CACHE_AFTER_USE,
    cache_dict=response_cache
)

# 活跃请求池 - 将作为活跃请求管理器的内部存储
active_requests_pool = {}

# 初始化活跃请求管理器
active_requests_manager = ActiveRequestsManager(requests_pool=active_requests_pool)

# --------------- 工具函数 ---------------

def switch_api_key():
    global current_api_key
    key = key_manager.get_available_key() # get_available_key 会处理栈的逻辑
    if key:
        current_api_key = key
        log('info', f"API key 替换为 → {current_api_key[:8]}...", extra={'key': current_api_key[:8], 'request_type': 'switch_key'})
    else:
        log('error', "API key 替换失败，所有API key都已尝试，请重新配置或稍后重试", extra={'key': 'N/A', 'request_type': 'switch_key', 'status_code': 'N/A'})

async def check_key(key):
    """检查单个API密钥是否有效"""
    is_valid = await test_api_key(key)
    status_msg = "有效" if is_valid else "无效"
    log('info', f"API Key {key[:10]}... {status_msg}.")
    return key if is_valid else None

def check_key_in_thread(key):
    """在线程中运行异步检查密钥函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        valid_key = loop.run_until_complete(check_key(key))
        if valid_key:
            # 如果密钥有效，立即添加到可用列表中
            key_manager.api_keys.append(valid_key)
            # 重置密钥栈以包含新的有效密钥
            key_manager._reset_key_stack()
            log('info', f"API Key {valid_key[:8]}... 已添加到可用列表")
        return valid_key
    finally:
        loop.close()

async def check_keys():
    """启动线程池来并行检查所有密钥"""
    # 保存原始密钥列表的副本
    all_keys = key_manager.api_keys.copy()
    # 清空当前密钥列表，将在检查过程中逐个添加有效密钥
    key_manager.api_keys = []
    
    log('info', f"开始在单独线程中检查 {len(all_keys)} 个API密钥...")
    
    # 创建线程池
    with ThreadPoolExecutor(max_workers=min(10, len(all_keys))) as executor:
        # 提交所有密钥检查任务
        future_to_key = {executor.submit(check_key_in_thread, key): key for key in all_keys}
        
        # 等待所有任务完成
        for future in future_to_key:
            try:
                future.result()  # 获取结果但不需要处理，因为check_key_in_thread已经处理了有效密钥
            except Exception as exc:
                log('error', f"检查密钥时发生错误: {exc}")
    
    if not key_manager.api_keys:
        log('error', "没有可用的 API 密钥！", extra={'key': 'N/A', 'request_type': 'startup', 'status_code': 'N/A'})
    
    return key_manager.api_keys

# 设置全局异常处理
sys.excepthook = handle_exception

# --------------- 事件处理 ---------------

@app.on_event("startup")
async def startup_event():
    log('info', "Starting Gemini API proxy...")
    
    # 启动缓存清理定时任务
    schedule_cache_cleanup(response_cache_manager, active_requests_manager)
    
    # 检查版本
    await check_version()
    
    # 先同步检查一个密钥，用于加载可用模型
    all_keys = key_manager.api_keys.copy()
    key_manager.api_keys = []  # 清空当前密钥列表
    
    # 尝试找到一个有效的密钥
    valid_key_found = False
    for key in all_keys:
        is_valid = await test_api_key(key)
        if is_valid:
            key_manager.api_keys.append(key)
            key_manager._reset_key_stack()
            log('info', f"初始检查: API Key {key[:8]}... 有效，已添加到可用列表")
            valid_key_found = True
            
            # 使用这个有效密钥加载可用模型
            try:
                all_models = await GeminiClient.list_available_models(key)
                GeminiClient.AVAILABLE_MODELS = [model.replace(
                    "models/", "") for model in all_models]
                log('info', "Available models loaded.")
            except Exception as e:
                log('warning', f"无法加载可用模型: {str(e)}")
            
            break  # 找到一个有效密钥后就跳出循环
    
    if not valid_key_found:
        log('warning', "初始检查未找到有效密钥，将在后台继续检查")
    
    # 在后台线程中检查剩余的密钥
    remaining_keys = [k for k in all_keys if k not in key_manager.api_keys]
    if remaining_keys:
        def check_remaining_keys():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 创建线程池检查剩余密钥
                with ThreadPoolExecutor(max_workers=min(10, len(remaining_keys))) as executor:
                    future_to_key = {executor.submit(check_key_in_thread, key): key for key in remaining_keys}
                    for future in future_to_key:
                        try:
                            future.result()
                        except Exception as exc:
                            log('error', f"检查密钥时发生错误: {exc}")
            finally:
                loop.close()
                log('info', f"后台密钥检查完成，当前可用密钥数量: {len(key_manager.api_keys)}")
        
        # 启动后台线程检查剩余密钥
        threading.Thread(target=check_remaining_keys, daemon=True).start()
        log('info', f"后台线程已启动，正在检查剩余的 {len(remaining_keys)} 个API密钥...")
    
    # 显示当前可用密钥
    key_manager.show_all_keys()
    log('info', f"当前可用 API 密钥数量：{len(key_manager.api_keys)}")
    log('info', f"最大重试次数设置为：{len(key_manager.api_keys)}")
    
    # 初始化路由器
    init_router(
        key_manager,
        response_cache_manager,
        active_requests_manager,
        SAFETY_SETTINGS,
        SAFETY_SETTINGS_G2,
        current_api_key,
        settings.FAKE_STREAMING,
        settings.FAKE_STREAMING_INTERVAL,
        settings.PASSWORD,
        settings.MAX_REQUESTS_PER_MINUTE,
        settings.MAX_REQUESTS_PER_DAY_PER_IP
    )
    
    # 初始化仪表盘路由器
    init_dashboard_router(
        key_manager,
        response_cache_manager,
        active_requests_manager
    )
    
    # 初始化路由器
    init_router(
        key_manager,
        response_cache_manager,
        active_requests_manager,
        SAFETY_SETTINGS,
        SAFETY_SETTINGS_G2,
        current_api_key,
        settings.FAKE_STREAMING,
        settings.FAKE_STREAMING_INTERVAL,
        settings.PASSWORD,
        settings.MAX_REQUESTS_PER_MINUTE,
        settings.MAX_REQUESTS_PER_DAY_PER_IP
    )
    
    # 初始化仪表盘路由器
    init_dashboard_router(
        key_manager,
        response_cache_manager,
        active_requests_manager
    )

# --------------- 异常处理 ---------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from app.utils import translate_error
    error_message = translate_error(str(exc))
    extra_log_unhandled_exception = {'status_code': 500, 'error_message': error_message}
    log('error', f"Unhandled exception: {error_message}", extra=extra_log_unhandled_exception)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=ErrorResponse(message=str(exc), type="internal_error").dict())

# --------------- 路由 ---------------

# 包含API路由
app.include_router(router)
app.include_router(dashboard_router)

# 挂载静态文件目录
app.mount("/assets", StaticFiles(directory="app/templates/assets"), name="assets")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    根路由 - 返回静态 HTML 文件
    """
    # 直接返回 index.html 文件
    return templates.TemplateResponse("index.html", {"request": request})