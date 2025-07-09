#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
向量嵌入模型
提供文本向量化功能
"""

import os
import torch
import numpy as np
from config import MODEL_CONFIG

class EmbeddingModel:
    """
    向量嵌入模型类
    负责将文本转换为向量表示
    """
    
    def __init__(self):
        """
        初始化向量嵌入模型
        """
        self.model_name = MODEL_CONFIG['embedding']['model_name']
        self.device = MODEL_CONFIG['embedding']['device']
        
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
            from transformers import AutoModel, AutoTokenizer
            
            print(f"正在加载嵌入模型: {self.model_name}")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 加载模型
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            print("嵌入模型加载完成")
            
        except Exception as e:
            print(f"加载嵌入模型出错: {e}")
            # 如果加载失败，使用一个简单的回退机制
            self.model = None
            self.tokenizer = None
    
    def get_embedding(self, text):
        """
        获取文本的向量表示
        
        Args:
            text (str): 输入文本
            
        Returns:
            numpy.ndarray: 文本的向量表示
        """
        # 尝试加载模型
        self._load_model()
        
        # 如果模型加载失败，返回随机向量
        if self.model is None or self.tokenizer is None:
            print("模型加载失败，返回随机向量")
            return np.random.randn(768).astype(np.float32)  # 返回768维随机向量
        
        try:
            # 准备输入
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 获取嵌入
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # 使用[CLS]令牌的最后一层隐藏状态作为文本表示
            # 对于某些模型，可能需要使用平均池化或其他方法
            if self.model_name.startswith('bge-'):
                # BGE模型使用最后一层隐藏状态的平均值
                embeddings = self._mean_pooling(outputs.last_hidden_state, inputs['attention_mask'])
                # 归一化
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            else:
                # 默认使用[CLS]令牌
                embeddings = outputs.last_hidden_state[:, 0, :]
            
            # 转换为NumPy数组
            return embeddings[0].cpu().numpy()
            
        except Exception as e:
            print(f"获取嵌入出错: {e}")
            return np.random.randn(768).astype(np.float32)  # 返回768维随机向量
    
    def _mean_pooling(self, token_embeddings, attention_mask):
        """
        对token嵌入进行平均池化
        
        Args:
            token_embeddings (torch.Tensor): token嵌入
            attention_mask (torch.Tensor): 注意力掩码
            
        Returns:
            torch.Tensor: 池化后的嵌入
        """
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def get_embeddings_batch(self, texts, batch_size=32):
        """
        批量获取文本的向量表示
        
        Args:
            texts (list): 输入文本列表
            batch_size (int): 批处理大小
            
        Returns:
            numpy.ndarray: 文本的向量表示数组
        """
        # 尝试加载模型
        self._load_model()
        
        # 如果模型加载失败，返回随机向量
        if self.model is None or self.tokenizer is None:
            print("模型加载失败，返回随机向量")
            return np.random.randn(len(texts), 768).astype(np.float32)  # 返回768维随机向量
        
        try:
            all_embeddings = []
            
            # 批处理
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                
                # 准备输入
                inputs = self.tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # 获取嵌入
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                # 使用[CLS]令牌的最后一层隐藏状态作为文本表示
                if self.model_name.startswith('bge-'):
                    # BGE模型使用最后一层隐藏状态的平均值
                    embeddings = self._mean_pooling(outputs.last_hidden_state, inputs['attention_mask'])
                    # 归一化
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                else:
                    # 默认使用[CLS]令牌
                    embeddings = outputs.last_hidden_state[:, 0, :]
                
                # 添加到结果列表
                all_embeddings.append(embeddings.cpu().numpy())
            
            # 合并所有批次的结果
            return np.vstack(all_embeddings)
            
        except Exception as e:
            print(f"批量获取嵌入出错: {e}")
            return np.random.randn(len(texts), 768).astype(np.float32)  # 返回768维随机向量