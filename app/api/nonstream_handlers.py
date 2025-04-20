import asyncio
from fastapi import HTTPException, status, Request
from app.models import ChatCompletionRequest
from app.services import GeminiClient
from app.utils import cache_response, update_api_call_stats,handle_api_error
from app.utils.logging import log
from .client_disconnect import check_client_disconnect, handle_client_disconnect
from .gemini_handlers import run_gemini_completion
import app.config.settings as settings
import random
from typing import Literal

# 非流式请求处理函数
async def process_nonstream_request(
    chat_request: ChatCompletionRequest, 
    http_request: Request, 
    request_type: str,
    contents,
    system_instruction,
    current_api_key: str,
    response_cache_manager,
    active_requests_manager,
    safety_settings,
    safety_settings_g2,
    api_call_stats,
    cache_key: str = None,
    client_ip: str = None
):
    """处理非流式API请求"""
    gemini_client = GeminiClient(current_api_key)
    
    # 创建任务
    gemini_task = asyncio.create_task(
        run_gemini_completion(
            gemini_client,
            chat_request,
            contents,
            system_instruction,
            request_type,
            current_api_key,
            safety_settings,
            safety_settings_g2
        )
    )
    
    disconnect_task = asyncio.create_task(
        check_client_disconnect(
            http_request,
            current_api_key,
            request_type,
            chat_request.model
        )
    )

    try:
        # 先等待看是否API任务先完成，或者客户端先断开连接
        done, pending = await asyncio.wait(
            [gemini_task, disconnect_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        if disconnect_task in done:
            # 客户端已断开连接，但我们仍继续完成API请求以便缓存结果
            result = await handle_client_disconnect(
                gemini_task,
                chat_request,
                request_type,
                current_api_key,
                response_cache_manager,
                cache_key,
                client_ip,
                chat_request.model,
                current_api_key
            )
            return (result, "success" if result else "empty")

        else:
            # API任务先完成，取消断开检测任务
            disconnect_task.cancel()
            
            # 获取响应内容
            response_content = await gemini_task
            
            # 检查响应内容是否为空
            if not response_content or not response_content.text:
                log('warning', f"非流式请求: API密钥 {current_api_key[:8]}... 返回空响应",
                    extra={'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model})
                return (None, "empty")
            
            # 检查缓存是否已经存在，如果存在则不再创建新缓存
            cached_response, cache_hit = response_cache_manager.get(cache_key)
            if cache_hit:
                log('info', f"缓存已存在，直接返回: {cache_key[:8]}...", 
                    extra={'cache_operation': 'use-existing', 'request_type': request_type})
                
                # 安全删除缓存
                if cache_key in response_cache_manager.cache:
                    del response_cache_manager.cache[cache_key]
                    log('info', f"缓存使用后已删除: {cache_key[:8]}...", 
                        extra={'cache_operation': 'used-and-removed', 'request_type': request_type})
                
                return (cached_response, "success")
            
            # 创建响应
            from app.utils.response import create_response
            response = create_response(chat_request, response_content)
            
            update_api_call_stats(settings.api_call_stats, endpoint=current_api_key, model=chat_request.model)
            # 缓存响应
            cache_response(response, cache_key, client_ip, response_cache_manager, endpoint=current_api_key,model=chat_request.model)
            
            # 立即删除缓存，确保只能使用一次
            if cache_key and cache_key in response_cache_manager.cache:
                del response_cache_manager.cache[cache_key]
                log('info', f"缓存创建后立即删除: {cache_key[:8]}...", 
                    extra={'request_type': request_type})
            
            # 返回响应
            return (response, "success")

    except asyncio.CancelledError:
        extra_log = {'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model, 'error_message':"请求被取消"}
        log('info', "请求取消", extra=extra_log)
        
        # 在请求被取消时先检查缓存中是否已有结果
        cached_response, cache_hit = response_cache_manager.get(cache_key)
        if cache_hit:
            log('info', f"请求取消但找到有效缓存，使用缓存响应: {cache_key[:8]}...", 
                extra={'cache_operation': 'use-cache-on-cancel', 'request_type': request_type})
            
            # 安全删除缓存
            if cache_key in response_cache_manager.cache:
                del response_cache_manager.cache[cache_key]
                log('info', f"缓存使用后已删除: {cache_key[:8]}...", 
                    extra={'cache_operation': 'used-and-removed', 'request_type': request_type})
            
            return (cached_response, "success")
            
        # 尝试完成正在进行的API请求
        if not gemini_task.done():
            log('info', "请求取消但API请求尚未完成，继续等待...", 
                extra={'key': current_api_key[:8], 'request_type': request_type})
            
            # 使用shield确保任务不会被取消
            response_content = await asyncio.shield(gemini_task)
            
            # 检查响应内容是否为空
            if not response_content or not response_content.text:
                log('warning', f"非流式请求(取消后): API密钥 {current_api_key[:8]}... 返回空响应",
                    extra={'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model})
                return (None, "empty")
            update_api_call_stats(settings.api_call_stats, endpoint=current_api_key, model=chat_request.model)
            # 创建响应
            from app.utils.response import create_response
            response = create_response(chat_request, response_content)
            
            # 不缓存这个响应，直接返回
            return (response, "success")
        else:
            # 任务已完成，获取结果
            response_content = gemini_task.result()
            
            # 检查响应内容是否为空
            if not response_content or not response_content.text:
                log('warning', f"非流式请求(已完成): API密钥 {current_api_key[:8]}... 返回空响应",
                    extra={'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model})
                return (None, "empty")
            
            # 创建响应
            from app.utils.response import create_response
            response = create_response(chat_request, response_content)
            
            # 不缓存这个响应，直接返回
            return (response, "success")

    except HTTPException as e:
        if e.status_code == status.HTTP_408_REQUEST_TIMEOUT:
            extra_log = {'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model, 
                        'status_code': 408, 'error_message': '客户端连接中断'}
            log('error', "客户端连接中断，终止后续重试", extra=extra_log)
            raise  
        else:
            raise
    except Exception as e:
        # 其他异常，返回None以便并发请求可以继续尝试其他密钥
        log('error', f"非流式请求异常: {str(e)[:8]}", 
            extra={'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model})
        return (None, "error")
    
    
# route 中发起请求的处理函数
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