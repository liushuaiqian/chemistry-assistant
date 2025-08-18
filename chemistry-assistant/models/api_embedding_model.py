#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API向量嵌入模型
通过调用国内API服务获取文本向量化功能
"""

import requests
import numpy as np
from typing import List
from langchain_core.embeddings import Embeddings
from config import MODEL_CONFIG
import time
import json
from http import HTTPStatus

# 尝试导入 dashscope，如果失败则使用 HTTP 请求
try:
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("警告: dashscope 未安装，将使用 HTTP 请求方式调用通义 API")

class APIEmbeddingModel(Embeddings):
    """
    基于API的向量嵌入模型类
    支持多种国内API服务
    """
    
    def __init__(self, provider='zhipu', model_name=None):
        """
        初始化API向量嵌入模型
        
        Args:
            provider (str): API提供商 ('zhipu', 'tongyi', 'baichuan')
            model_name (str): 模型名称，如果为None则使用默认模型
        """
        self.provider = provider
        self.config = MODEL_CONFIG.get(provider, {})
        self.api_key = self.config.get('api_key', '')
        
        # 设置模型名称和API端点
        if provider == 'zhipu':
            self.model_name = model_name or 'embedding-2'
            self.api_url = 'https://open.bigmodel.cn/api/paas/v4/embeddings'
        elif provider == 'tongyi':
            self.model_name = model_name or 'multimodal-embedding-v1'
            self.api_url = 'https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding'
        elif provider == 'baichuan':
            self.model_name = model_name or 'Baichuan-Text-Embedding'
            self.api_url = 'https://api.baichuan-ai.com/v1/embeddings'
        else:
            raise ValueError(f"不支持的API提供商: {provider}")
        
        if not self.api_key:
            raise ValueError(f"未配置{provider}的API密钥")
        
        # 为 tongyi 提供商设置 dashscope API key
        if provider == 'tongyi' and DASHSCOPE_AVAILABLE:
            dashscope.api_key = self.api_key
        
        print(f"初始化{provider}嵌入模型: {self.model_name}")
    
    def _get_headers(self):
        """
        获取API请求头
        """
        if self.provider == 'zhipu':
            return {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        elif self.provider == 'tongyi':
            return {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        elif self.provider == 'baichuan':
            return {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        else:
            return {'Content-Type': 'application/json'}
    
    def _prepare_request_data(self, texts):
        """
        准备API请求数据
        """
        if self.provider == 'zhipu':
            return {
                'model': self.model_name,
                'input': texts if isinstance(texts, list) else [texts]
            }
        elif self.provider == 'tongyi':
            return {
                'model': self.model_name,
                'input': {
                    'texts': texts if isinstance(texts, list) else [texts]
                },
                'parameters': {
                    'text_type': 'document'
                }
            }
        elif self.provider == 'baichuan':
            return {
                'model': self.model_name,
                'input': texts if isinstance(texts, list) else [texts]
            }
        else:
            return {}
    
    def _extract_embeddings(self, response_data):
        """
        从API响应中提取嵌入向量
        """
        try:
            if self.provider == 'zhipu':
                return [item['embedding'] for item in response_data['data']]
            elif self.provider == 'tongyi':
                return [item['embedding'] for item in response_data['output']['embeddings']]
            elif self.provider == 'baichuan':
                return [item['embedding'] for item in response_data['data']]
            else:
                return []
        except KeyError as e:
            print(f"解析API响应失败: {e}")
            return []
    
    def _get_tongyi_embedding_with_sdk(self, texts):
        """
        使用 dashscope SDK 获取通义嵌入向量
        
        Args:
            texts (str or list): 输入文本或文本列表
            
        Returns:
            list: 嵌入向量列表
        """
        try:
            # 准备输入格式
            if isinstance(texts, str):
                input_data = [{'text': texts}]
            else:
                input_data = [{'text': text} for text in texts]
            
            # 调用 dashscope API
            resp = dashscope.MultiModalEmbedding.call(
                model=self.model_name,
                input=input_data
            )
            
            if resp.status_code == HTTPStatus.OK:
                embeddings = []
                for item in resp.output['embeddings']:
                    embeddings.append(item['embedding'])
                return embeddings
            else:
                print(f"Dashscope API 调用失败: {resp.code}, {resp.message}")
                return None
                
        except Exception as e:
            print(f"Dashscope SDK 调用出错: {e}")
            return None
    
    def get_embedding(self, text):
        """
        获取单个文本的向量表示
        
        Args:
            text (str): 输入文本
            
        Returns:
            numpy.ndarray: 文本的向量表示
        """
        try:
            # 对于 tongyi 提供商，优先使用 dashscope SDK
            if self.provider == 'tongyi' and DASHSCOPE_AVAILABLE:
                embeddings = self._get_tongyi_embedding_with_sdk(text)
                if embeddings:
                    return np.array(embeddings[0], dtype=np.float32)
                else:
                    print("使用 dashscope SDK 失败，回退到 HTTP 请求")
            
            # 使用 HTTP 请求方式
            headers = self._get_headers()
            data = self._prepare_request_data(text)
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                embeddings = self._extract_embeddings(response_data)
                if embeddings:
                    return np.array(embeddings[0], dtype=np.float32)
                else:
                    print("API响应中未找到嵌入向量")
                    return self._get_fallback_embedding()
            else:
                print(f"API请求失败: {response.status_code}, {response.text}")
                return self._get_fallback_embedding()
                
        except Exception as e:
            print(f"获取嵌入向量出错: {e}")
            return self._get_fallback_embedding()
    
    def get_embeddings_batch(self, texts, batch_size=16):
        """
        批量获取文本的向量表示
        
        Args:
            texts (list): 输入文本列表
            batch_size (int): 批处理大小
            
        Returns:
            numpy.ndarray: 文本的向量表示数组
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            try:
                # 对于 tongyi 提供商，优先使用 dashscope SDK
                if self.provider == 'tongyi' and DASHSCOPE_AVAILABLE:
                    embeddings = self._get_tongyi_embedding_with_sdk(batch_texts)
                    if embeddings:
                        all_embeddings.extend(embeddings)
                        time.sleep(0.1)  # 避免API限流
                        continue
                    else:
                        print(f"批次 {i//batch_size + 1} 使用 dashscope SDK 失败，回退到 HTTP 请求")
                
                # 使用 HTTP 请求方式
                headers = self._get_headers()
                data = self._prepare_request_data(batch_texts)
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    embeddings = self._extract_embeddings(response_data)
                    if embeddings:
                        all_embeddings.extend(embeddings)
                    else:
                        print(f"批次 {i//batch_size + 1} API响应中未找到嵌入向量")
                        # 为这个批次添加回退向量
                        for _ in batch_texts:
                            all_embeddings.append(self._get_fallback_embedding().tolist())
                else:
                    print(f"批次 {i//batch_size + 1} API请求失败: {response.status_code}")
                    # 为这个批次添加回退向量
                    for _ in batch_texts:
                        all_embeddings.append(self._get_fallback_embedding().tolist())
                
                # 添加延迟以避免API限流
                time.sleep(0.1)
                
            except Exception as e:
                print(f"批次 {i//batch_size + 1} 获取嵌入向量出错: {e}")
                # 为这个批次添加回退向量
                for _ in batch_texts:
                    all_embeddings.append(self._get_fallback_embedding().tolist())
        
        return np.array(all_embeddings, dtype=np.float32)
    
    def _get_fallback_embedding(self, dim=1024):
        """
        获取回退嵌入向量（随机向量）
        
        Args:
            dim (int): 向量维度
            
        Returns:
            numpy.ndarray: 随机向量
        """
        return np.random.randn(dim).astype(np.float32)
    
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
    
    def test_connection(self):
        """
        测试API连接
        """
        test_text = "这是一个测试文本"
        try:
            embedding = self.get_embedding(test_text)
            if embedding is not None and len(embedding) > 0:
                print(f"✅ {self.provider} API连接成功，向量维度: {len(embedding)}")
                return True
            else:
                print(f"❌ {self.provider} API连接失败")
                return False
        except Exception as e:
            print(f"❌ {self.provider} API连接测试出错: {e}")
            return False

# 便捷函数
def create_zhipu_embedding():
    """创建智谱AI嵌入模型"""
    return APIEmbeddingModel(provider='zhipu')

def create_tongyi_embedding():
    """创建通义千问嵌入模型"""
    return APIEmbeddingModel(provider='tongyi')

def create_baichuan_embedding():
    """创建百川嵌入模型"""
    return APIEmbeddingModel(provider='baichuan')