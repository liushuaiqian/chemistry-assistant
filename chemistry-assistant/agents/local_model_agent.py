#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
本地模型Agent
负责调用微调后的本地模型
"""

from models.local_chat_model import LocalChatModel

class LocalModelAgent:
    """
    本地模型Agent类
    负责调用微调后的本地模型处理查询
    """
    
    def __init__(self):
        """
        初始化本地模型Agent
        """
        self.model = LocalChatModel()
        self.name = "本地模型Agent"
    
    def process(self, query, task_info, context=None):
        """
        处理用户查询
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            context (dict, optional): 上下文信息，包含其他Agent的处理结果
            
        Returns:
            str: 处理结果
        """
        # 构建提示
        prompt = self._build_prompt(query, task_info, context)
        
        # 调用模型生成回答
        response = self.model.generate(prompt)
        
        return response
    
    def _build_prompt(self, query, task_info, context):
        """
        构建模型提示
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            context (dict, optional): 上下文信息
            
        Returns:
            str: 构建的提示
        """
        prompt = f"""你是一个专业的化学助手，请回答以下化学问题。
        
        问题: {query}
        """
        
        # 如果有上下文信息，添加到提示中
        if context:
            prompt += "\n\n相关信息:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
        
        # 如果有检测到的实体，添加到提示中
        if 'detected_entities' in task_info and task_info['detected_entities']:
            prompt += "\n检测到的实体:\n"
            for entity in task_info['detected_entities']:
                prompt += f"- {entity['type']}: {entity['value']}\n"
        
        prompt += "\n请提供准确、专业的回答："
        
        return prompt