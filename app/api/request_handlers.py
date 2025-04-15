import asyncio
import json
import random
from typing import Literal
from fastapi import HTTPException, Request, status
from app.models import ChatCompletionRequest
from app.services import GeminiClient
from app.utils import handle_api_error
from app.utils.logging import log
from .nonstream_handlers import process_nonstream_request
import app.config.settings as settings

# 请求处理函数
async def process_request(
    chat_request: ChatCompletionRequest, 
    http_request: Request, 
    request_type: Literal['stream', 'non-stream'], 
    key_manager,
    response_cache_manager,
    active_requests_manager,
    safety_settings,
    safety_settings_g2,
    api_call_stats,
    cache_key: str = None, 
    client_ip: str = None
):
    """处理非流式请求"""
    global current_api_key

    # 转换消息格式
    contents, system_instruction = GeminiClient.convert_messages(
        GeminiClient, chat_request.messages,model=chat_request.model)    
    # 非流式请求处理 - 使用并发请求
    
    # 重置已尝试的密钥
    key_manager.reset_tried_keys_for_request()
    # 设置初始并发数
    current_concurrent = settings.CONCURRENT_REQUESTS
    
    # 获取所有可用的API密钥
    all_keys = key_manager.api_keys.copy()
    random.shuffle(all_keys)
    # 如果可用密钥数量小于并发数，则使用所有可用密钥
    if len(all_keys) < current_concurrent:
        current_concurrent = len(all_keys)
    
    # 尝试使用不同API密钥，直到所有密钥都尝试过
    while all_keys:
        # 获取当前批次的密钥
        current_batch = all_keys[:current_concurrent]
        all_keys = all_keys[current_concurrent:]
        
        # 创建并发任务
        tasks = []
        for api_key in current_batch:
            # 记录当前尝试的密钥信息
            log('info', f"并发请求使用密钥: {api_key[:8]}...", 
                extra={'key': api_key[:8], 'request_type': request_type, 'model': chat_request.model})
            
            # 创建任务
            task = asyncio.create_task(
                process_nonstream_request(
                    chat_request,
                    http_request,
                    request_type,
                    contents,
                    system_instruction,
                    api_key,
                    response_cache_manager,
                    active_requests_manager,
                    safety_settings,
                    safety_settings_g2,
                    api_call_stats,
                    cache_key,
                    client_ip
                )
            )
            tasks.append((api_key, task))
        
        # 等待所有任务完成
        done, pending = await asyncio.wait(
            [task for _, task in tasks],
            return_when=asyncio.ALL_COMPLETED
        )
        
        # 检查是否有成功的响应
        success = False
        for api_key, task in tasks:
            if task in done:
                try:
                    result, status = task.result()
                    if status == "success" and result:  # 如果有成功响应内容
                        success = True
                        log('info', f"并发请求成功，使用密钥: {api_key[:8]}...", 
                            extra={'key': api_key[:8], 'request_type': request_type, 'model': chat_request.model})
                        return result
                except Exception as e:
                    # 使用统一的API错误处理函数
                    error_result = await handle_api_error(
                        e, 
                        api_key, 
                        key_manager, 
                        request_type, 
                        chat_request.model, 
                        0
                    )
                    
                    # 如果需要删除缓存，清除缓存
                    if error_result.get('remove_cache', False) and cache_key and cache_key in response_cache_manager.cache:
                        log('info', f"因API错误，删除缓存: {cache_key[:8]}...", 
                            extra={'cache_operation': 'remove-on-error', 'request_type': request_type})
                        del response_cache_manager.cache[cache_key]
        
        # 如果所有请求都失败或返回空响应，增加并发数并继续尝试
        if not success and all_keys:
            # 增加并发数，但不超过最大并发数
            current_concurrent = min(current_concurrent + settings.INCREASE_CONCURRENT_ON_FAILURE, settings.MAX_CONCURRENT_REQUESTS)
            log('info', f"所有并发请求失败或返回空响应，增加并发数至: {current_concurrent}", 
                extra={'request_type': request_type, 'model': chat_request.model})
    
    # 如果所有尝试都失败
    msg = "所有API密钥均请求失败,请稍后重试"
    log('error', "API key 替换失败，所有API key都已尝试，请重新配置或稍后重试", extra={'request_type': 'switch_key'})
    
    # 非流式请求使用标准HTTP异常
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)