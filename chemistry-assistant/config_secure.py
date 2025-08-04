#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件（安全版本）
注意：此文件中的API密钥已被移除，请使用环境变量或密钥管理器设置密钥

使用方法：
1. 设置环境变量：
   export CHEMISTRY_ASSISTANT_ZHIPU_API_KEY="your_zhipu_key"
   export CHEMISTRY_ASSISTANT_TONGYI_API_KEY="your_tongyi_key"
   
2. 或使用密钥管理器：
   from utils.key_manager import store_api_key
   store_api_key('zhipu', 'your_zhipu_key')
   store_api_key('tongyi', 'your_tongyi_key')
"""


配置文件
包含模型配置、知识库配置、外部API配置等
支持从环境变量和密钥管理器中安全获取API密钥
"""

import os
from typing import Dict, Any, Optional

# 尝试导入安全配置管理器
try:
    from utils.secure_config import SecureConfig
    _secure_config = SecureConfig()
    _use_secure_config = True
except ImportError:
    _secure_config = None
    _use_secure_config = False

def get_api_key(service_name: str, default: str = '') -> str:
    """
    安全获取API密钥
    
    Args:
        service_name (str): 服务名称
        default (str): 默认值
        
    Returns:
        str: API密钥
    """
    if _use_secure_config and _secure_config:
        return _secure_config.get_api_key(service_name, default)
    
    # 回退到环境变量
    env_var_name = f'CHEMISTRY_ASSISTANT_{service_name.upper()}_API_KEY'
    return os.getenv(env_var_name, default)

def get_config_value(key: str, default: Any = None) -> Any:
    """
    安全获取配置值
    
    Args:
        key (str): 配置键
        default (Any): 默认值
        
    Returns:
        Any: 配置值
    """
    if _use_secure_config and _secure_config:
        return _secure_config.get_config_value(key, default)
    
    # 回退到环境变量
    env_var_name = f'CHEMISTRY_ASSISTANT_{key.upper()}'
    env_value = os.getenv(env_var_name)
    
    if env_value is not None:
        # 尝试转换类型
        if isinstance(default, bool):
            return env_value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int):
            try:
                return int(env_value)
            except ValueError:
                return default
        elif isinstance(default, float):
            try:
                return float(env_value)
            except ValueError:
                return default
        else:
            return env_value
    
    return default

# 模型配置
MODEL_CONFIG = {
    # 本地模型配置
    'local': {
        'model_path': './models/local_model',  # 本地模型路径
        'device': 'cpu',  # 运行设备: 'cuda' 或 'cpu'
    },
    
    # 外部API配置
    'openai': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'api_base': get_config_value('openai_api_base', 'https://api.openai.com/v1'),
        'model': get_config_value('openai_model', 'gpt-4'),
    },
    'zhipu': {  # 智谱AI
        'api_key': '',  # 从环境变量或密钥管理器获取
        'model': get_config_value('zhipu_model', 'glm-4'),
    },
    'claude': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'model': get_config_value('claude_model', 'claude-3-opus-20240229'),
    },
    
    # 通义大模型配置
    'tongyi': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'model': get_config_value('tongyi_model', 'qwen-max'),
    },
    
    # 通义视觉模型配置
    'tongyi_vision': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'model': get_config_value('tongyi_vision_model', 'qwen-vl-max'),
    },
    
    # DeepSeek模型配置（通过通义API调用）
    'deepseek': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'model': get_config_value('deepseek_model', 'deepseek-r1'),
    },
    
    # GLM-4-Plus模型配置（用于结果融合）
    'glm4_plus': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'model': get_config_value('glm4_plus_model', 'glm-4-plus'),
    },
    
    # 文心4.5
    'qianfan': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'model': get_config_value('qianfan_model', 'ernie-4.5-turbo-128k'),
    },
    # 嵌入模型
    'embedding': {
        'model_name': 'bge-large-zh-v1.5',  # 本地模型名称（备用）
        'device': 'cpu',
        'use_api': True,  # 是否使用API模式
        'api_provider': 'zhipu',  # API提供商: 'zhipu', 'tongyi', 'baichuan'
        'api_model': 'embedding-3',  # API模型名称
    }
}

# 知识库配置
KNOWLEDGE_CONFIG = {
    'vector_store_path': './data/vector_store',
    'textbooks_path': './data/textbooks',
    'question_bank_path': './data/question_bank',
}

# 外部API配置
EXTERNAL_API_CONFIG = {
    'pubchem': {
        'base_url': get_config_value('pubchem_base_url', 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'),
        'timeout': get_config_value('pubchem_timeout', 30)
    },
    'metaso': {
        'base_url': get_config_value('metaso_base_url', 'https://metaso.cn/api/open/search/v2'),
        'api_key': '',  # 从环境变量或密钥管理器获取
        'search_topic_id': get_config_value('metaso_search_topic_id', '8640179836073414656'),
        'timeout': get_config_value('metaso_timeout', 50)  # 请求超时时间（秒）
    },
    'tongyi_knowledge_app': {
        'api_key': '',  # 从环境变量或密钥管理器获取
        'app_id': get_config_value('tongyi_knowledge_app_id', 'b6f1b931e9c74a41bf605fe1e74fa634'),
        'pipeline_ids': get_config_value('tongyi_knowledge_pipeline_ids', ['elpzmshtgs', 'yjutc6uopj', '9881c0qpvj']),  # 知识库ID列表
        'timeout': get_config_value('tongyi_knowledge_timeout', 30)  # 请求超时时间（秒）
    }
}

# UI配置
UI_CONFIG = {
    'title': get_config_value('ui_title', '化学助手'),
    'description': get_config_value('ui_description', '基于大模型的智能化学问答系统'),
    'theme': get_config_value('ui_theme', 'light'),  # 可选: light, dark
    'port': get_config_value('ui_port', 7860),
    'share': get_config_value('ui_share', False),  # 是否创建公共链接
    'debug': get_config_value('ui_debug', False)
}

# 日志配置
LOG_CONFIG = {
    'log_level': get_config_value('log_level', 'INFO'),  # 日志级别
    'log_file': get_config_value('log_file', './logs/chemistry_assistant.log'),  # 日志文件路径
    'max_file_size': get_config_value('log_max_size', 10 * 1024 * 1024),  # 最大文件大小 (10MB)
    'backup_count': get_config_value('log_backup_count', 5)  # 备份文件数量
}

# 安全配置
SECURITY_CONFIG = {
    'enable_rate_limit': get_config_value('rate_limit_enabled', True),  # 启用API限流
    'rate_limit_rpm': get_config_value('rate_limit_rpm', 60),  # 每分钟请求限制
    'rate_limit_rph': get_config_value('rate_limit_rph', 1000),  # 每小时请求限制
    'max_query_length': get_config_value('max_query_length', 10000),  # 最大查询长度
    'max_image_size_mb': get_config_value('max_image_size_mb', 10),  # 最大图片大小（MB）
    'session_timeout': get_config_value('session_timeout', 30),  # 会话超时时间（分钟）
    'enable_input_validation': get_config_value('input_validation_enabled', True),  # 启用输入验证
    'enable_output_filtering': get_config_value('output_filtering_enabled', True),  # 启用输出过滤
    'master_key_rotation_days': get_config_value('master_key_rotation_days', 90),  # 主密钥轮换周期（天）
}
