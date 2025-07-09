#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志模块
提供日志记录功能
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from config import LOG_CONFIG

def setup_logger(name='chemistry_assistant'):
    """
    设置日志记录器
    
    Args:
        name (str): 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 获取日志配置
    log_level = getattr(logging, LOG_CONFIG['log_level'])
    log_file = LOG_CONFIG['log_file']
    
    # 创建日志目录（如果不存在）
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除现有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 创建文件处理器（滚动日志文件）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 设置格式化器
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认日志记录器
logger = setup_logger()

def get_logger(name=None):
    """
    获取日志记录器
    
    Args:
        name (str, optional): 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    if name:
        return setup_logger(name)
    return logger