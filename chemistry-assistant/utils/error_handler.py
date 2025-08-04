#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误处理模块
提供统一的错误处理和恢复机制
"""

import logging
import traceback
from functools import wraps

class ErrorHandler:
    """
    错误处理器
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    def safe_execute(self, func, *args, **kwargs):
        """
        安全执行函数
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"执行 {func.__name__} 时发生错误: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def retry_on_failure(self, max_retries=3, delay=1):
        """
        失败重试装饰器
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            self.logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
                            raise
                        else:
                            self.logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{delay}秒后重试: {e}")
                            time.sleep(delay)
                
            return wrapper
        return decorator
    
    def graceful_degradation(self, fallback_func=None):
        """
        优雅降级装饰器
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.logger.warning(f"函数 {func.__name__} 执行失败，启用降级模式: {e}")
                    if fallback_func:
                        return fallback_func(*args, **kwargs)
                    return None
            return wrapper
        return decorator

# 全局错误处理器实例
error_handler = ErrorHandler()
