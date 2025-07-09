#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
本地聊天模型
提供微调模型的调用接口
"""

import os
import torch
from config import MODEL_CONFIG

class LocalChatModel:
    """
    本地聊天模型类
    负责加载和调用本地部署的微调模型
    """
    
    def __init__(self):
        """
        初始化本地聊天模型
        """
        self.model_path = MODEL_CONFIG['local']['model_path']
        self.device = MODEL_CONFIG['local']['device']
        
        # 检查CUDA是否可用
        if self.device == 'cuda' and not torch.cuda.is_available():
            print("CUDA不可用，使用CPU")
            self.device = 'cpu'
        
        # 初始化模型（延迟加载）
        self.model = None
        self.tokenizer = None
    
    def _load_model(self):
        """
        加载模型和分词器
        """
        if self.model is not None and self.tokenizer is not None:
            return
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            print(f"正在加载模型: {self.model_path}")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=self.device,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32
            )
            
            print("模型加载完成")
            
        except Exception as e:
            print(f"加载模型出错: {e}")
            # 如果加载失败，使用一个简单的回退机制
            self.model = None
            self.tokenizer = None
    
    def generate(self, prompt, max_length=2048, temperature=0.7):
        """
        生成回答
        
        Args:
            prompt (str): 输入提示
            max_length (int): 最大生成长度
            temperature (float): 温度参数，控制随机性
            
        Returns:
            str: 生成的回答
        """
        # 尝试加载模型
        self._load_model()
        
        # 如果模型加载失败，返回错误信息
        if self.model is None or self.tokenizer is None:
            return "模型加载失败，请检查模型路径和配置"
        
        try:
            # 准备输入
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # 生成回答
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.1
                )
            
            # 解码输出
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除输入提示，只保留生成的部分
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            print(f"生成回答出错: {e}")
            return f"生成回答时出错: {str(e)}"
    
    def chat(self, messages, max_length=2048, temperature=0.7):
        """
        聊天接口
        
        Args:
            messages (list): 消息列表，每个消息是一个字典，包含'role'和'content'字段
            max_length (int): 最大生成长度
            temperature (float): 温度参数，控制随机性
            
        Returns:
            str: 生成的回答
        """
        # 将消息列表转换为提示
        prompt = self._messages_to_prompt(messages)
        
        # 生成回答
        return self.generate(prompt, max_length, temperature)
    
    def _messages_to_prompt(self, messages):
        """
        将消息列表转换为提示
        
        Args:
            messages (list): 消息列表
            
        Returns:
            str: 转换后的提示
        """
        prompt = ""
        
        for message in messages:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                prompt += f"系统: {content}\n\n"
            elif role == 'user':
                prompt += f"用户: {content}\n\n"
            elif role == 'assistant':
                prompt += f"助手: {content}\n\n"
        
        prompt += "助手: "
        
        return prompt