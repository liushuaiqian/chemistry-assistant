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
from typing import List
from langchain_core.embeddings import Embeddings

class EmbeddingModel(Embeddings):
    """
    向量嵌入模型类
    负责将文本转换为向量表示
    """
    
    def __init__(self):
        """
        初始化向量嵌入模型
        """
        self.embedding_config = MODEL_CONFIG['embedding']
        self.use_api = self.embedding_config.get('use_api', False)
        
        if self.use_api:
            # 使用API模式
            from .api_embedding_model import APIEmbeddingModel
            api_provider = self.embedding_config.get('api_provider', 'zhipu')
            api_model = self.embedding_config.get('api_model', 'embedding-2')
            print(f"使用API嵌入模型: {api_provider} - {api_model}")
            self.api_model = APIEmbeddingModel(provider=api_provider, model_name=api_model)
        else:
            # 使用本地模型
            self.model_name = self.embedding_config['model_name']
            self.device = self.embedding_config['device']
            
            # 检查CUDA是否可用
            if self.device == 'cuda' and not torch.cuda.is_available():
                print("CUDA不可用，使用CPU")
                self.device = 'cpu'
            
            # 初始化模型（延迟加载）
            self.model = None
            self.tokenizer = None
            self.api_model = None
    
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
        if self.use_api and self.api_model:
            # 使用API模式
            return self.api_model.get_embedding(text)
        else:
            # 使用本地模型
            return self._get_local_embedding(text)
    
    def _get_local_embedding(self, text):
        """
        使用本地模型获取文本的向量表示
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
        if self.use_api and self.api_model:
            # 使用API模式，调整批处理大小以适应API限制
            api_batch_size = min(batch_size, 16)  # API通常有更小的批处理限制
            return self.api_model.get_embeddings_batch(texts, api_batch_size)
        else:
            # 使用本地模型
            return self._get_local_embeddings_batch(texts, batch_size)
    
    def _get_local_embeddings_batch(self, texts, batch_size=32):
        """
        使用本地模型批量获取文本的向量表示
        """
        # 尝试加载模型
        self._load_model()
        
        # 如果模型加载失败，返回随机向量
        if self.model is None or self.tokenizer is None:
            print("模型加载失败，返回随机向量")
            return np.random.randn(len(texts), 768).astype(np.float32)

        try:
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                inputs = self.tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = self.model(**inputs)
                if self.model_name.startswith('bge-'):
                    embeddings = self._mean_pooling(outputs.last_hidden_state, inputs['attention_mask'])
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                else:
                    embeddings = outputs.last_hidden_state[:, 0, :]
                all_embeddings.append(embeddings.cpu().numpy())
            return np.vstack(all_embeddings)
        except Exception as e:
            print(f"批量获取嵌入出错: {e}")
            return np.random.randn(len(texts), 768).astype(np.float32)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        LangChain兼容的文档嵌入方法
        """
        embeddings = self.get_embeddings_batch(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        LangChain兼容的查询嵌入方法
        """
        embedding = self.get_embedding(text)
        return embedding.tolist()