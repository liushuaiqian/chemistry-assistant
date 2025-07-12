#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件
包含模型URL、API密钥等配置项
"""

# 模型配置
MODEL_CONFIG = {
    # 本地模型配置
    'local': {
        'model_path': './models/local_model',  # 本地模型路径
        'device': 'cpu',  # 运行设备: 'cuda' 或 'cpu'
    },
    
    # 外部API配置
    'openai': {
        'api_key': '',  # 填入你的OpenAI API密钥
        'api_base': 'https://api.openai.com/v1',
        'model': 'gpt-4',
    },
    'zhipu': {  # 智谱AI
        'api_key': '971d419f21f84b86b950f12935ab5622.RNM4AQGHjXqvbg9a',  # 质谱AI密钥
        'model': 'glm-4',
    },
    'claude': {
        'api_key': 'sk-tjqouywcqyitthembwmhdhgaqxqsofzbalhwrpdkbtygaqzw',  # 硅基流动密钥
        'model': 'claude-3-opus-20240229',
    },
    
    # 通义大模型配置
    'tongyi': {
        'api_key': 'sk-df1f72de49554dfab781d878a7530a91',  # 阿里云百炼/通义密钥
        'model': 'qwen-max',
    },
    
    # 通义视觉模型配置
    'tongyi_vision': {
        'api_key': 'sk-df1f72de49554dfab781d878a7530a91',  # 阿里云百炼/通义密钥
        'model': 'qwen-vl-max',
    },
    
    # DeepSeek模型配置（通过通义API调用）
    'deepseek': {
        'api_key': 'sk-df1f72de49554dfab781d878a7530a91',  # 阿里云百炼/通义密钥
        'model': 'deepseek-r1',
    },
    
    # GLM-4-Plus模型配置（用于结果融合）
    'glm4_plus': {
        'api_key': '971d419f21f84b86b950f12935ab5622.RNM4AQGHjXqvbg9a',  # 智谱AI密钥
        'model': 'glm-4-plus',
    },
    
    # 向量嵌入模型
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
        'base_url': 'https://pubchem.ncbi.nlm.nih.gov/rest/pug',
    }
}

# UI配置
UI_CONFIG = {
    'web_port': 8501,  # Streamlit默认端口
    'theme': 'light',  # 'light' 或 'dark'
    'title': '化学助手',
}

# 日志配置
LOG_CONFIG = {
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'log_file': './chemistry_assistant.log',
}