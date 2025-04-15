import asyncio
import time
from fastapi import Request
from app.models import ChatCompletionRequest
from app.utils import create_error_response, update_api_call_stats
from app.utils.logging import log
import app.config.settings as settings
# 客户端断开检测函数
async def check_client_disconnect(http_request: Request, current_api_key: str, request_type: str, model: str):
    """检查客户端是否断开连接"""
    while True:
        if await http_request.is_disconnected():
            extra_log = {'key': current_api_key[:8], 'request_type': request_type, 'model': model, 'error_message': '检测到客户端断开连接'}
            log('info', "客户端连接已中断，等待API请求完成", extra=extra_log)
            return True
        await asyncio.sleep(0.5)

# 客户端断开处理函数
async def handle_client_disconnect(
    gemini_task: asyncio.Task, 
    chat_request: ChatCompletionRequest, 
    request_type: str, 
    current_api_key: str,
    response_cache_manager,
    cache_key: str = None,
    client_ip: str = None,
    model: str = None,
    key: str = None,
):
    try:
        # 等待API任务完成，使用shield防止它被取消
        response_content = await asyncio.shield(gemini_task)
        
        # 检查响应文本是否为空
        if response_content is None or response_content.text == "":
            if response_content is None:
                log('info', "客户端断开后API任务返回None", 
                    extra={'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model})
            else:
                extra_log = {'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model, 'status_code': 204}
                log('info', "客户端断开后Gemini API 返回空响应", extra=extra_log)
            
            # 删除任何现有缓存，因为响应为空
            if cache_key and cache_key in response_cache_manager.cache:
                log('info', f"因空响应，删除缓存: {cache_key[:8]}...", 
                    extra={'cache_operation': 'remove-on-empty', 'request_type': request_type})
                del response_cache_manager.cache[cache_key]
                
            # 返回错误响应而不是None
            return create_error_response(chat_request.model, "AI未返回任何内容，请重试")
        
        # 首先检查是否有现有缓存
        cached_response, cache_hit = response_cache_manager.get(cache_key)
        if cache_hit:
            log('info', f"客户端断开但找到已存在缓存，将删除: {cache_key[:8]}...", 
                extra={'cache_operation': 'disconnect-found-cache', 'request_type': request_type})
            
            # 安全删除缓存
            if cache_key in response_cache_manager.cache:
                del response_cache_manager.cache[cache_key]
            
            # 不返回缓存，而是创建新响应并缓存
        
        # 创建新响应
        from app.utils.response import create_response
        response = create_response(chat_request, response_content)
        update_api_call_stats(settings.api_call_stats,key,model)
        # 客户端已断开，此响应不会实际发送，可以考虑将其缓存以供后续使用
        # 如果确实需要缓存，则可以取消下面的注释
        # cache_response(response, cache_key, client_ip)
        
        return response
    except asyncio.CancelledError:
        # 对于取消异常，仍然尝试继续完成任务
        log('info', "客户端断开后任务被取消，但我们仍会尝试完成", 
            extra={'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model})
        
        # 检查任务是否已经完成
        if gemini_task.done() and not gemini_task.cancelled():
            try:
                response_content = gemini_task.result()
                
                # 首先检查是否有现有缓存
                cached_response, cache_hit = response_cache_manager.get(cache_key)
                if cache_hit:
                    log('info', f"任务被取消但找到已存在缓存，将删除: {cache_key[:8]}...", 
                        extra={'cache_operation': 'cancel-found-cache', 'request_type': request_type})
                    
                    # 安全删除缓存
                    if cache_key in response_cache_manager.cache:
                        del response_cache_manager.cache[cache_key]
                
                # 创建但不缓存响应
                from app.utils.response import create_response
                response = create_response(chat_request, response_content)
                return response
            except Exception as inner_e:
                log('error', f"客户端断开后从已完成任务获取结果失败: {str(inner_e)}", 
                    extra={'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model})
                
                # 删除缓存，因为出现错误
                if cache_key and cache_key in response_cache_manager.cache:
                    log('info', f"因任务获取结果失败，删除缓存: {cache_key[:8]}...", 
                        extra={'cache_operation': 'remove-on-error', 'request_type': request_type})
                    del response_cache_manager.cache[cache_key]
        
        # 创建错误响应而不是返回None
        return create_error_response(chat_request.model, "请求处理过程中发生错误，请重试")
    except Exception as e:
        # 处理API任务异常
        error_msg = str(e)
        extra_log = {'key': current_api_key[:8], 'request_type': request_type, 'model': chat_request.model, 'error_message': error_msg}
        log('error', f"客户端断开后处理API响应时出错: {error_msg}", extra=extra_log)
        
        # 删除缓存，因为出现错误
        if cache_key and cache_key in response_cache_manager.cache:
            log('info', f"因API响应错误，删除缓存: {cache_key[:8]}...", 
                extra={'cache_operation': 'remove-on-error', 'request_type': request_type})
            del response_cache_manager.cache[cache_key]
            
        # 创建错误响应而不是返回None
        return create_error_response(chat_request.model, f"请求处理错误: {error_msg}")