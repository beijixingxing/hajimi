import time
import hashlib
import json
from typing import Dict, Any, Optional
import logging
from app.utils.logging import log
logger = logging.getLogger("my_logger")

class ResponseCacheManager:
    """管理API响应缓存的类"""
    
    def __init__(self, expiry_time: int, max_entries: int, remove_after_use: bool = True, 
                cache_dict: Dict[str, Dict[str, Any]] = None):
        self.cache = cache_dict if cache_dict is not None else {}  # 使用传入的缓存字典或创建新字典
        self.expiry_time = expiry_time
        self.max_entries = max_entries
        self.remove_after_use = remove_after_use
    
    def get(self, cache_key: str):
        """获取缓存项，如果存在且未过期"""
        now = time.time()
        if cache_key in self.cache and now < self.cache[cache_key].get('expiry_time', 0):
            cached_item = self.cache[cache_key]
            
            # 获取响应但先不删除
            response = cached_item['response']
            
            # 返回响应
            return response, True
        
        return None, False
    
    def store(self, cache_key: str, response, client_ip: str = None):
        """存储响应到缓存"""
        now = time.time()
        self.cache[cache_key] = {
            'response': response,
            'expiry_time': now + self.expiry_time,
            'created_at': now,
            'client_ip': client_ip
        }
        
        log('info', f"响应已缓存: {cache_key[:8]}...", 
            extra={'cache_operation': 'store', 'request_type': 'non-stream'})
        
        # 如果缓存超过限制，清理最旧的
        self.clean_if_needed()
    
    def clean_expired(self):
        """清理所有过期的缓存项"""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if now > v.get('expiry_time', 0)]
        
        for key in expired_keys:
            del self.cache[key]
            log('info', f"清理过期缓存: {key[:8]}...", extra={'cache_operation': 'clean'})
    
    def clean_if_needed(self):
        """如果缓存数量超过限制，清理最旧的项目"""
        if len(self.cache) <= self.max_entries:
            return
        
        # 按创建时间排序
        sorted_keys = sorted(self.cache.keys(),
                           key=lambda k: self.cache[k].get('created_at', 0))
        
        # 计算需要删除的数量
        to_remove = len(self.cache) - self.max_entries
        
        # 删除最旧的项
        for key in sorted_keys[:to_remove]:
            del self.cache[key]
            log('info', f"缓存容量限制，删除旧缓存: {key[:8]}...", extra={'cache_operation': 'limit'})

def generate_cache_key(chat_request) -> str:
    """生成请求的唯一缓存键"""
    # 创建包含请求关键信息的字典
    request_data = {
        'model': chat_request.model, 
        'messages': []
    }
    
    # 添加消息内容
    for msg in chat_request.messages:
        if isinstance(msg.content, str):
            message_data = {'role': msg.role, 'content': msg.content}
            request_data['messages'].append(message_data)
        elif isinstance(msg.content, list):
            content_list = []
            for item in msg.content:
                if item.get('type') == 'text':
                    content_list.append({'type': 'text', 'text': item.get('text')})
                # 对于图像数据，我们只使用标识符而不是全部数据
                elif item.get('type') == 'image_url':
                    image_data = item.get('image_url', {}).get('url', '')
                    if image_data.startswith('data:image/'):
                        # 对于base64图像，使用前32字符作为标识符
                        content_list.append({'type': 'image_url', 'hash': hashlib.md5(image_data[:32].encode()).hexdigest()})
                    else:
                        content_list.append({'type': 'image_url', 'url': image_data})
            request_data['messages'].append({'role': msg.role, 'content': content_list})
    
    # 将字典转换为JSON字符串并计算哈希值
    json_data = json.dumps(request_data, sort_keys=True)
    return hashlib.md5(json_data.encode()).hexdigest()

def cache_response(response, cache_key, client_ip, response_cache_manager, endpoint=None,model=None):
    """
    将响应存入缓存
    
    参数:
    - response: 响应对象
    - cache_key: 缓存键
    - client_ip: 客户端IP
    - response_cache_manager: 缓存管理器
    - api_key: API密钥，用于更新API密钥使用统计
    """
    if not cache_key:
        return
        
    # 先检查缓存是否已存在
    existing_cache = cache_key in response_cache_manager.cache
    
    if existing_cache:
        log('info', f"缓存已存在，跳过存储: {cache_key[:8]}...",
            extra={'cache_operation': 'skip-existing', 'request_type': 'non-stream'})
    else:
        response_cache_manager.store(cache_key, response, client_ip)
        log('info', f"API响应已缓存: {cache_key[:8]}...",
            extra={'cache_operation': 'store-new', 'request_type': 'non-stream'})