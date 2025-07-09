#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
辅助函数模块
提供各种通用辅助函数
"""

import os
import re
import json
import time
import hashlib
from datetime import datetime
from .logger import get_logger

# 获取日志记录器
logger = get_logger('helpers')

def ensure_dir(directory):
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory (str): 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"创建目录: {directory}")

def load_json(file_path):
    """
    加载JSON文件
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        dict: JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件出错 {file_path}: {e}")
        return {}

def save_json(data, file_path):
    """
    保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        file_path (str): 文件路径
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        ensure_dir(directory)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"保存JSON文件: {file_path}")
    except Exception as e:
        logger.error(f"保存JSON文件出错 {file_path}: {e}")

def load_text(file_path):
    """
    加载文本文件
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载文本文件出错 {file_path}: {e}")
        return ""

def save_text(text, file_path):
    """
    保存文本到文件
    
    Args:
        text (str): 文本内容
        file_path (str): 文件路径
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        ensure_dir(directory)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"保存文本文件: {file_path}")
    except Exception as e:
        logger.error(f"保存文本文件出错 {file_path}: {e}")

def generate_id():
    """
    生成唯一ID
    
    Returns:
        str: 唯一ID
    """
    # 使用时间戳和随机数生成唯一ID
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    random_str = hashlib.md5(f"{timestamp}{time.time()}".encode()).hexdigest()[:8]
    return f"{timestamp}-{random_str}"

def extract_chemical_formulas(text):
    """
    从文本中提取化学式
    
    Args:
        text (str): 输入文本
        
    Returns:
        list: 提取的化学式列表
    """
    # 匹配化学式的正则表达式
    pattern = r'([A-Z][a-z]?\d*)+'
    return re.findall(pattern, text)

def extract_numbers(text):
    """
    从文本中提取数字
    
    Args:
        text (str): 输入文本
        
    Returns:
        list: 提取的数字列表
    """
    # 匹配数字的正则表达式（包括整数和小数）
    pattern = r'\d+(?:\.\d+)?'
    return [float(x) for x in re.findall(pattern, text)]

def format_time(seconds):
    """
    格式化时间（秒）为人类可读格式
    
    Args:
        seconds (float): 秒数
        
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds %= 60
        return f"{int(minutes)}分{seconds:.2f}秒"
    else:
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"{int(hours)}时{int(minutes)}分{seconds:.2f}秒"

def truncate_text(text, max_length=100, suffix='...'):
    """
    截断文本
    
    Args:
        text (str): 输入文本
        max_length (int): 最大长度
        suffix (str): 后缀
        
    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix

def is_valid_chemical_formula(formula):
    """
    检查是否为有效的化学式
    
    Args:
        formula (str): 化学式
        
    Returns:
        bool: 是否有效
    """
    # 简单的化学式验证正则表达式
    pattern = r'^([A-Z][a-z]?\d*)+$'
    return bool(re.match(pattern, formula))

def is_valid_equation(equation):
    """
    检查是否为有效的化学方程式
    
    Args:
        equation (str): 化学方程式
        
    Returns:
        bool: 是否有效
    """
    # 简单的化学方程式验证正则表达式
    pattern = r'^([A-Z][a-z]?\d*)+(?:[\s+]+([A-Z][a-z]?\d*)+)*\s*(?:=|->|→|⟶)\s*([A-Z][a-z]?\d*)+(?:[\s+]+([A-Z][a-z]?\d*)+)*$'
    return bool(re.match(pattern, equation))