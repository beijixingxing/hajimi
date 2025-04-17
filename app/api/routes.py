from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from app.models import ChatCompletionRequest, ChatCompletionResponse, ErrorResponse, ModelList
from app.services import GeminiClient
from app.utils import protect_from_abuse,generate_cache_key
from .stream_handlers import process_stream_request
from app.models.schemas import ChatCompletionResponse, Choice, Message 

import app.config.settings as settings
import asyncio
import time
from app.utils.logging import log

# 导入拆分后的模块
from .auth import verify_password
from .request_handlers import process_request

# 创建路由器
router = APIRouter()

# 全局变量引用 - 这些将在main.py中初始化并传递给路由
key_manager = None
response_cache_manager = None
active_requests_manager = None
safety_settings = None
safety_settings_g2 = None
current_api_key = None
FAKE_STREAMING = None
FAKE_STREAMING_INTERVAL = None
PASSWORD = None
MAX_REQUESTS_PER_MINUTE = None
MAX_REQUESTS_PER_DAY_PER_IP = None

# 初始化路由器的函数
def init_router(
    _key_manager,
    _response_cache_manager,
    _active_requests_manager,
    _safety_settings,
    _safety_settings_g2,
    _current_api_key,
    _fake_streaming,
    _fake_streaming_interval,
    _password,
    _max_requests_per_minute,
    _max_requests_per_day_per_ip
):
    global key_manager, response_cache_manager, active_requests_manager
    global safety_settings, safety_settings_g2, current_api_key
    global FAKE_STREAMING, FAKE_STREAMING_INTERVAL
    global PASSWORD, MAX_REQUESTS_PER_MINUTE, MAX_REQUESTS_PER_DAY_PER_IP
    
    key_manager = _key_manager
    response_cache_manager = _response_cache_manager
    active_requests_manager = _active_requests_manager
    safety_settings = _safety_settings
    safety_settings_g2 = _safety_settings_g2
    current_api_key = _current_api_key
    FAKE_STREAMING = _fake_streaming
    FAKE_STREAMING_INTERVAL = _fake_streaming_interval
    PASSWORD = _password
    MAX_REQUESTS_PER_MINUTE = _max_requests_per_minute
    MAX_REQUESTS_PER_DAY_PER_IP = _max_requests_per_day_per_ip

# 自定义密码验证依赖
async def custom_verify_password(request: Request):
    await verify_password(request, settings.PASSWORD)

# API路由
@router.get("/v1/models", response_model=ModelList)
def list_models():
    log('info', "Received request to list models", extra={'request_type': 'list_models', 'status_code': 200})
    filtered_models = [model for model in GeminiClient.AVAILABLE_MODELS if model not in settings.BLOCKED_MODELS]
    return ModelList(data=[{"id": model, "object": "model", "created": 1678888888, "owned_by": "organization-owner"} for model in filtered_models])

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest, http_request: Request, _: None = Depends(custom_verify_password)):
    """处理API请求的主函数，根据需要处理流式或非流式请求"""
    global current_api_key
    
    # 获取客户端IP
    client_ip = http_request.client.host if http_request.client else "unknown"
    # 请求前基本检查
    protect_from_abuse(
        http_request, 
        settings.MAX_REQUESTS_PER_MINUTE, 
        settings.MAX_REQUESTS_PER_DAY_PER_IP)
    if request.model not in GeminiClient.AVAILABLE_MODELS:
        log('error', "无效的模型", 
            extra={'model': request.model, 'status_code': 400})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的模型")

    
    # 流式请求直接处理，不使用缓存
    if request.stream:
        return await process_stream_request(
            request,
            key_manager,
            safety_settings,
            safety_settings_g2,
            settings.api_call_stats,
            settings.FAKE_STREAMING,
            settings.FAKE_STREAMING_INTERVAL
        )
    
    # 生成完整缓存键 - 用于精确匹配
    cache_key = generate_cache_key(request)
    
    # 记录请求缓存键信息
    log('info', f"请求缓存键: {cache_key[:8]}...", 
        extra={'cache_key': cache_key[:8], 'request_type': 'non-stream'})
    
    # 检查精确缓存是否存在且未过期
    cached_response, cache_hit = response_cache_manager.get(cache_key)
    if cache_hit:
        # 精确缓存命中
        log('info', f"精确缓存命中: {cache_key[:8]}...", 
            extra={'cache_operation': 'hit', 'request_type': 'non-stream'})
        
        # 同时清理相关的活跃任务，避免后续请求等待已经不需要的任务
        active_requests_manager.remove_by_prefix(f"cache:{cache_key}")
        
        # 安全删除缓存
        if cache_key in response_cache_manager.cache:
            del response_cache_manager.cache[cache_key]
            log('info', f"缓存使用后已删除: {cache_key[:8]}...", 
                extra={'cache_operation': 'used-and-removed', 'request_type': 'non-stream'})
        
        # 返回缓存响应
        return cached_response
    
    # 构建包含缓存键的活跃请求池键
    pool_key = f"cache:{cache_key}"
    
    # 查找所有使用相同缓存键的活跃任务
    active_task = active_requests_manager.get(pool_key)
    if active_task and not active_task.done():
        log('info', f"发现相同请求的进行中任务", 
            extra={'request_type': 'non-stream', 'model': request.model})
        
        # 等待已有任务完成
        try:
            # 设置超时，避免无限等待
            await asyncio.wait_for(active_task, timeout=180)
            
            # 通过缓存管理器获取已完成任务的结果
            cached_response, cache_hit = response_cache_manager.get(cache_key)
            if cache_hit:
                # 删除缓存
                if cache_key in response_cache_manager.cache:
                    del response_cache_manager.cache[cache_key]
                    log('info', f"使用已完成任务的缓存后删除: {cache_key[:8]}...", 
                        extra={'cache_operation': 'used-and-removed', 'request_type': 'non-stream'})
                
                return cached_response
                
            # 如果缓存已被清除或不存在，使用任务结果
            if active_task.done() and not active_task.cancelled():
                result = active_task.result()
                if result:
                    # 使用原始结果时，我们需要创建一个新的响应对象
                    # 避免使用可能已被其他请求修改的对象
                    try:
                        # 检查是否是字典
                        if isinstance(result, dict):
                            resp_object = result.get('object', 'chat.completion') 
                            resp_model = result.get('model')
                            resp_choices = result.get('choices', []) 
                        elif hasattr(result, 'object') and hasattr(result, 'model') and hasattr(result, 'choices'):
                            resp_object = result.object
                            resp_model = result.model
                            resp_choices = result.choices
                        
                        pydantic_choices = []
                        for choice_data in resp_choices:
                             if isinstance(choice_data, dict):
                                 pydantic_choices.append(Choice(
                                     index=choice_data.get("index", 0),
                                     message=Message(
                                         role=choice_data.get("message", {}).get("role", "assistant"),
                                         content=choice_data.get("message", {}).get("content", "")
                                     ),
                                     finish_reason=choice_data.get("finish_reason")
                                 ))
                             elif isinstance(choice_data, Choice): # If already a Choice object
                                 pydantic_choices.append(choice_data)
                             # else: handle unexpected choice format?

                        new_response = ChatCompletionResponse(
                            id=f"chatcmpl-{int(time.time()*1000)}", 
                            object=resp_object, 
                            created=int(time.time()), 
                            model=resp_model,
                            choices=pydantic_choices 
                            
                        )
                    except (AttributeError, TypeError, ValueError, Exception) as e: # Catch potential errors
                        log('error', f"创建新响应对象失败: {e}", 
                            extra={'request_type': 'non-stream', 'model': request.model, 'result_type': type(result).__name__})
                        # Consider raising HTTPException for clarity
                        raise HTTPException(status_code=500, detail="Internal error processing response.")
                    
                    # 不要缓存此结果，因为它很可能是一个已存在但被使用后清除的缓存
                    return new_response
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            # 任务超时或被取消的情况下，记录日志然后让代码继续执行
            error_type = "超时" if isinstance(e, asyncio.TimeoutError) else "被取消"
            log('warning', f"等待已有任务{error_type}: {pool_key}", 
                extra={'request_type': 'non-stream', 'model': request.model})
            
            # 从活跃请求池移除该任务
            if active_task.done() or active_task.cancelled():
                active_requests_manager.remove(pool_key)
                log('info', f"已从活跃请求池移除{error_type}任务: {pool_key}", 
                    extra={'request_type': 'non-stream'})
     
    # 创建非流式请求处理任务
    process_task = asyncio.create_task(
        process_request(
            request, 
            http_request, 
            "non-stream",
            key_manager,
            response_cache_manager,
            active_requests_manager,
            safety_settings,
            safety_settings_g2,
            settings.api_call_stats,
            cache_key,
            client_ip
        )
    )
    
    # 将任务添加到活跃请求池
    active_requests_manager.add(pool_key, process_task)
    
    # 等待任务完成
    try:
        response = await process_task
        return response
    except Exception as e:
        # 如果任务失败，从活跃请求池中移除
        active_requests_manager.remove(pool_key)
        
        # 检查是否已有缓存的结果（可能是由另一个任务创建的）
        cached_response, cache_hit = response_cache_manager.get(cache_key)
        if cache_hit:
            log('info', f"任务失败但找到缓存，使用缓存结果: {cache_key[:8]}...", 
                extra={'request_type': 'non-stream', 'model': request.model})
            return cached_response
        
        # 重新抛出异常
        raise
