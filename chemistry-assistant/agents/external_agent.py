#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
外部模型Agent
负责调用OpenAI/通义/Claude等外部API
"""

import os
import requests
import json
from config import MODEL_CONFIG
from core.llm_manager import LLMManager

class ExternalAgent:
    """
    外部模型Agent类
    负责调用外部API处理复杂或专业的化学问题
    """
    
    def __init__(self, provider='openai'):
        """
        初始化外部模型Agent
        
        Args:
            provider (str): 外部API提供商，可选值: 'openai', 'zhipu', 'claude', 'tongyi'
        """
        self.provider = provider
        self.name = f"{provider.capitalize()}外部Agent"
        
        # 初始化LLM管理器
        self.llm_manager = LLMManager()
        
        # 加载配置（保留用于回退调用）
        self.config = MODEL_CONFIG.get(provider, {})
        self.api_key = self.config.get('api_key', os.environ.get(f"{provider.upper()}_API_KEY", ""))
        self.model = self.config.get('model', '')
        self.api_base = self.config.get('api_base', '')
    
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
        try:
            # 优先使用LangChain LLM管理器
            if self.llm_manager.is_model_available(self.provider):
                # 构建上下文信息
                context_str = ""
                if context:
                    context_str = f"上下文信息: {context}"
                
                return self.llm_manager.call_chemistry_expert(self.provider, query, context_str)
            else:
                # 回退到原始API调用方式
                return self._process_fallback(query, task_info, context)
                
        except Exception as e:
            return f"处理查询时出错: {str(e)}"
    
    def _process_fallback(self, query, task_info, context=None):
        """
        回退处理方式
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            context (dict, optional): 上下文信息
            
        Returns:
            str: 处理结果
        """
        # 构建提示
        prompt = self._build_prompt(query, task_info, context)
        
        # 根据不同的提供商调用不同的API
        if self.provider == 'openai':
            response = self._call_openai_api(prompt)
        elif self.provider == 'zhipu':
            response = self._call_zhipu_api(prompt)
        elif self.provider == 'claude':
            response = self._call_claude_api(prompt)
        elif self.provider == 'tongyi':
            response = self._call_tongyi_api(prompt)
        else:
            response = "不支持的外部API提供商"
        
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
        prompt = f"""你是一个专业的化学助手，请回答以下化学问题。请提供详细、准确的回答，并在适当的情况下引用相关的化学原理、公式或反应方程式。
        
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
    
    def _call_openai_api(self, prompt):
        """
        调用OpenAI API
        
        Args:
            prompt (str): 提示文本
            
        Returns:
            str: API响应
        """
        if not self.api_key:
            return "错误: 未设置OpenAI API密钥"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                # 正确提取OpenAI格式API的响应内容
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    else:
                        return f"API响应格式异常: 缺少message.content"
                else:
                    return f"API响应格式异常: 缺少choices"
            else:
                return f"API错误: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"调用OpenAI API时出错: {str(e)}"
    
    def _call_zhipu_api(self, prompt):
        """
        调用智谱AI API
        
        Args:
            prompt (str): 提示文本
            
        Returns:
            str: API响应
        """
        if not self.api_key:
            return "错误: 未设置智谱AI API密钥"
        
        try:
            # 智谱AI API调用
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                # 正确提取智谱AI API的响应内容
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    else:
                        return f"API响应格式异常: 缺少message.content"
                else:
                    return f"API响应格式异常: 缺少choices"
            else:
                return f"API错误: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"调用智谱AI API时出错: {str(e)}"
    
    def _call_claude_api(self, prompt):
        """
        调用Claude API
        
        Args:
            prompt (str): 提示文本
            
        Returns:
            str: API响应
        """
        if not self.api_key:
            return "错误: 未设置Claude API密钥"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                return f"API错误: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"调用Claude API时出错: {str(e)}"
    
    def _call_tongyi_api(self, prompt):
        """
        调用通义大模型API
        
        Args:
            prompt (str): 提示文本
            
        Returns:
            str: API响应
        """
        if not self.api_key:
            return "错误: 未设置通义大模型API密钥"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "input": {
                    "messages": [{"role": "user", "content": prompt}]
                },
                "parameters": {
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "result_format": "text"
                }
            }
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                # 正确提取通义千问API的响应内容
                if "output" in result and "text" in result["output"]:
                    return result["output"]["text"]
                elif "output" in result and "choices" in result["output"]:
                    # 某些版本的API可能使用choices格式
                    return result["output"]["choices"][0]["message"]["content"]
                else:
                    return f"API响应格式异常: {result}"
            else:
                return f"API错误: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"调用通义大模型API时出错: {str(e)}"