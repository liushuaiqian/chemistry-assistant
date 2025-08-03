#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文本排序器
基于gte-rerank-v2模型提供文本排序功能
"""

import dashscope
from http import HTTPStatus
from typing import List, Dict, Any, Optional, Tuple
from config import MODEL_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

class TextReranker:
    """
    文本排序器类
    使用gte-rerank-v2模型对候选文档进行精确排序
    """
    
    def __init__(self):
        """
        初始化文本排序器
        """
        # 获取通义API密钥
        self.api_key = MODEL_CONFIG.get('tongyi', {}).get('api_key', '')
        if not self.api_key:
            logger.warning("未找到通义API密钥，文本排序功能将不可用")
            self.available = False
        else:
            # 设置API密钥
            dashscope.api_key = self.api_key
            self.available = True
            logger.info("文本排序器初始化成功")
        
        self.model_name = "gte-rerank-v2"
    
    def rerank_documents(self, 
                        query: str, 
                        documents: List[str], 
                        top_n: int = 10,
                        return_documents: bool = True) -> Optional[Dict[str, Any]]:
        """
        对文档进行重新排序
        
        Args:
            query (str): 查询文本
            documents (List[str]): 候选文档列表
            top_n (int): 返回前N个结果
            return_documents (bool): 是否返回文档内容
            
        Returns:
            Optional[Dict[str, Any]]: 排序结果，包含相关性分数和文档
        """
        if not self.available:
            logger.error("文本排序器不可用，请检查API密钥配置")
            return None
        
        if not documents:
            logger.warning("文档列表为空")
            return None
        
        try:
            logger.info(f"开始对{len(documents)}个文档进行排序，查询: {query[:50]}...")
            
            resp = dashscope.TextReRank.call(
                model=self.model_name,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
                return_documents=return_documents
            )
            
            if resp.status_code == HTTPStatus.OK:
                logger.info(f"文档排序成功，返回{len(resp.output['results'])}个结果")
                return resp.output
            else:
                logger.error(f"文档排序失败: {resp.code} - {resp.message}")
                return None
                
        except Exception as e:
            logger.error(f"文档排序过程中发生错误: {str(e)}")
            return None
    
    def rerank_with_scores(self, 
                          query: str, 
                          documents: List[str], 
                          top_n: int = 10) -> List[Tuple[str, float]]:
        """
        对文档进行排序并返回文档和分数的元组列表
        
        Args:
            query (str): 查询文本
            documents (List[str]): 候选文档列表
            top_n (int): 返回前N个结果
            
        Returns:
            List[Tuple[str, float]]: (文档, 相关性分数) 的列表
        """
        result = self.rerank_documents(query, documents, top_n, return_documents=True)
        
        if not result or 'results' not in result:
            return []
        
        ranked_docs = []
        for item in result['results']:
            doc_text = item['document']['text']
            score = item['relevance_score']
            ranked_docs.append((doc_text, score))
        
        return ranked_docs
    
    def rerank_langchain_docs(self, 
                             query: str, 
                             langchain_docs: List[Any], 
                             top_n: int = 10) -> List[Any]:
        """
        对LangChain文档对象进行排序
        
        Args:
            query (str): 查询文本
            langchain_docs (List[Any]): LangChain文档对象列表
            top_n (int): 返回前N个结果
            
        Returns:
            List[Any]: 排序后的LangChain文档对象列表
        """
        if not langchain_docs:
            return []
        
        # 提取文档内容
        doc_texts = [doc.page_content for doc in langchain_docs]
        
        # 进行排序
        result = self.rerank_documents(query, doc_texts, top_n, return_documents=False)
        
        if not result or 'results' not in result:
            return langchain_docs[:top_n]  # 如果排序失败，返回原始顺序的前N个
        
        # 根据排序结果重新组织文档
        ranked_docs = []
        for item in result['results']:
            original_index = item['index']
            if original_index < len(langchain_docs):
                ranked_docs.append(langchain_docs[original_index])
        
        return ranked_docs
    
    def is_available(self) -> bool:
        """
        检查排序器是否可用
        
        Returns:
            bool: 是否可用
        """
        return self.available
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            'model_name': self.model_name,
            'available': self.available,
            'description': 'gte-rerank-v2是通义实验室研发的多语言文本统一排序模型',
            'capabilities': ['文本排序', '语义相关性评分', '多语言支持']
        }

# 测试函数
def test_text_reranker():
    """
    测试文本排序器功能
    """
    reranker = TextReranker()
    
    if not reranker.is_available():
        print("文本排序器不可用，请检查API密钥配置")
        return
    
    # 测试数据
    query = "什么是化学键"
    documents = [
        "化学键是原子间相互结合的作用力，包括离子键、共价键和金属键",
        "量子力学是研究微观粒子运动规律的物理学分支",
        "共价键是原子间通过共享电子对形成的化学键",
        "离子键是正负离子间的静电相互作用"
    ]
    
    print(f"查询: {query}")
    print(f"候选文档数量: {len(documents)}")
    
    # 测试排序
    ranked_docs = reranker.rerank_with_scores(query, documents, top_n=3)
    
    print("\n排序结果:")
    for i, (doc, score) in enumerate(ranked_docs, 1):
        print(f"{i}. 分数: {score:.4f}")
        print(f"   文档: {doc}")
        print()

if __name__ == '__main__':
    test_text_reranker()