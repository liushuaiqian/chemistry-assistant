#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强的综合检索处理器
支持本地RAG、通义、Metaso知识库并行检索，并调用大模型进行知识总结
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .rag_retriever import RAGRetriever
from .knowledge_api import KnowledgeAPI
from core.llm_manager import LLMManager

logger = logging.getLogger(__name__)

@dataclass
class RetrievalSource:
    """检索源信息"""
    name: str
    content: str
    confidence: float
    metadata: Dict[str, Any]
    retrieval_time: float
    success: bool

@dataclass
class ComprehensiveResult:
    """综合检索结果"""
    query: str
    sources: List[RetrievalSource]
    summary: str
    confidence_score: float
    total_time: float
    strategy_used: str
    metadata: Dict[str, Any]

class EnhancedComprehensiveRetriever:
    """
    增强的综合检索处理器
    
    功能特性：
    1. 并行检索多个知识库（本地RAG、通义、Metaso、PubChem）
    2. 智能结果融合和去重
    3. 大模型驱动的知识总结
    4. 动态置信度评估
    5. 性能监控和优化
    """
    
    def __init__(self, llm_manager: LLMManager = None):
        """
        初始化增强综合检索器
        
        Args:
            llm_manager: LLM管理器实例
        """
        self.rag_retriever = RAGRetriever(use_reranker=True)
        self.knowledge_api = KnowledgeAPI()
        self.llm_manager = llm_manager or LLMManager()
        
        # 性能统计
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'average_response_time': 0.0,
            'source_success_rates': {
                'local_rag': 0.0,
                'tongyi': 0.0,
                'metaso': 0.0,
                'pubchem': 0.0
            }
        }
        
        # 配置参数
        self.config = {
            'max_workers': 4,  # 并行检索的最大线程数
            'timeout_per_source': 30,  # 每个源的超时时间（秒）
            'min_confidence_threshold': 0.3,  # 最小置信度阈值
            'max_summary_length': 2000,  # 总结最大长度
            'enable_deduplication': True,  # 启用去重
            'similarity_threshold': 0.8  # 相似度阈值
        }
    
    async def comprehensive_retrieve(self, 
                                   query: str,
                                   enable_local_rag: bool = True,
                                   enable_tongyi: bool = True,
                                   enable_metaso: bool = True,
                                   enable_pubchem: bool = True,
                                   use_llm_summary: bool = True) -> ComprehensiveResult:
        """
        执行综合检索
        
        Args:
            query: 用户查询
            enable_local_rag: 是否启用本地RAG
            enable_tongyi: 是否启用通义知识库
            enable_metaso: 是否启用Metaso知识库
            enable_pubchem: 是否启用PubChem数据库
            use_llm_summary: 是否使用LLM进行总结
            
        Returns:
            ComprehensiveResult: 综合检索结果
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        logger.info(f"开始综合检索: {query[:50]}...")
        
        try:
            # 1. 并行检索多个知识源
            sources = await self._parallel_retrieve(
                query=query,
                enable_local_rag=enable_local_rag,
                enable_tongyi=enable_tongyi,
                enable_metaso=enable_metaso,
                enable_pubchem=enable_pubchem
            )
            
            # 2. 过滤和去重
            filtered_sources = self._filter_and_deduplicate(sources)
            
            # 3. 生成综合总结
            if use_llm_summary and filtered_sources:
                summary = await self._generate_llm_summary(query, filtered_sources)
            else:
                summary = self._generate_simple_summary(filtered_sources)
            
            # 4. 计算整体置信度
            confidence_score = self._calculate_overall_confidence(filtered_sources)
            
            # 5. 构建结果
            total_time = time.time() - start_time
            result = ComprehensiveResult(
                query=query,
                sources=filtered_sources,
                summary=summary,
                confidence_score=confidence_score,
                total_time=total_time,
                strategy_used="enhanced_comprehensive",
                metadata={
                    'sources_count': len(filtered_sources),
                    'successful_sources': [s.name for s in filtered_sources if s.success],
                    'average_source_confidence': sum(s.confidence for s in filtered_sources) / len(filtered_sources) if filtered_sources else 0
                }
            )
            
            # 6. 更新统计信息
            self._update_stats(result)
            
            logger.info(f"综合检索完成，耗时 {total_time:.2f}秒，获得 {len(filtered_sources)} 个有效源")
            return result
            
        except Exception as e:
            logger.error(f"综合检索异常: {str(e)}")
            total_time = time.time() - start_time
            return ComprehensiveResult(
                query=query,
                sources=[],
                summary=f"检索过程中发生错误: {str(e)}",
                confidence_score=0.0,
                total_time=total_time,
                strategy_used="error_fallback",
                metadata={'error': str(e)}
            )
    
    async def _parallel_retrieve(self, 
                               query: str,
                               enable_local_rag: bool,
                               enable_tongyi: bool,
                               enable_metaso: bool,
                               enable_pubchem: bool) -> List[RetrievalSource]:
        """
        并行检索多个知识源
        
        Args:
            query: 查询文本
            enable_*: 各个知识源的启用状态
            
        Returns:
            List[RetrievalSource]: 检索源列表
        """
        tasks = []
        
        # 创建检索任务
        if enable_local_rag:
            tasks.append(self._retrieve_local_rag(query))
        
        if enable_tongyi:
            tasks.append(self._retrieve_tongyi(query))
        
        if enable_metaso:
            tasks.append(self._retrieve_metaso(query))
        
        if enable_pubchem:
            tasks.append(self._retrieve_pubchem(query))
        
        # 并行执行所有任务
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sources = []
            for result in results:
                if isinstance(result, RetrievalSource):
                    sources.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"检索任务异常: {str(result)}")
            return sources
        else:
            return []
    
    async def _retrieve_local_rag(self, query: str) -> RetrievalSource:
        """
        检索本地RAG知识库
        """
        start_time = time.time()
        try:
            # 使用现有的RAG检索器
            local_docs = self.rag_retriever.retrieve_comprehensive(query, textbook_k=3, question_k=2)
            
            if local_docs:
                content = "\n\n".join(local_docs[:3])  # 取前3个结果
                confidence = min(0.8, len(local_docs) * 0.2)  # 基于结果数量计算置信度
                
                return RetrievalSource(
                    name="本地RAG知识库",
                    content=content,
                    confidence=confidence,
                    metadata={
                        'document_count': len(local_docs),
                        'source_types': ['textbook', 'question_bank']
                    },
                    retrieval_time=time.time() - start_time,
                    success=True
                )
            else:
                return RetrievalSource(
                    name="本地RAG知识库",
                    content="",
                    confidence=0.0,
                    metadata={'error': '未找到相关文档'},
                    retrieval_time=time.time() - start_time,
                    success=False
                )
                
        except Exception as e:
            logger.error(f"本地RAG检索异常: {str(e)}")
            return RetrievalSource(
                name="本地RAG知识库",
                content="",
                confidence=0.0,
                metadata={'error': str(e)},
                retrieval_time=time.time() - start_time,
                success=False
            )
    
    async def _retrieve_tongyi(self, query: str) -> RetrievalSource:
        """
        检索通义千问知识库
        """
        start_time = time.time()
        try:
            result = self.knowledge_api.search_tongyi_knowledge(query)
            
            if result.get('success'):
                content = result.get('answer', '')
                confidence = 0.7 if content else 0.0
                
                return RetrievalSource(
                    name="通义千问知识库",
                    content=content,
                    confidence=confidence,
                    metadata={
                        'usage': result.get('usage', {}),
                        'model': 'tongyi'
                    },
                    retrieval_time=time.time() - start_time,
                    success=True
                )
            else:
                return RetrievalSource(
                    name="通义千问知识库",
                    content="",
                    confidence=0.0,
                    metadata={'error': result.get('error', '检索失败')},
                    retrieval_time=time.time() - start_time,
                    success=False
                )
                
        except Exception as e:
            logger.error(f"通义知识库检索异常: {str(e)}")
            return RetrievalSource(
                name="通义千问知识库",
                content="",
                confidence=0.0,
                metadata={'error': str(e)},
                retrieval_time=time.time() - start_time,
                success=False
            )
    
    async def _retrieve_metaso(self, query: str) -> RetrievalSource:
        """
        检索Metaso知识库
        """
        start_time = time.time()
        try:
            result = self.knowledge_api.search_knowledge_base(query)
            
            if result.get('success'):
                content = result.get('answer', '')
                references = result.get('references', [])
                confidence = 0.8 if content else 0.0
                
                return RetrievalSource(
                    name="Metaso知识库",
                    content=content,
                    confidence=confidence,
                    metadata={
                        'references': references,
                        'result_id': result.get('result_id', ''),
                        'balance': result.get('balance', 0)
                    },
                    retrieval_time=time.time() - start_time,
                    success=True
                )
            else:
                return RetrievalSource(
                    name="Metaso知识库",
                    content="",
                    confidence=0.0,
                    metadata={'error': result.get('error', '检索失败')},
                    retrieval_time=time.time() - start_time,
                    success=False
                )
                
        except Exception as e:
            logger.error(f"Metaso知识库检索异常: {str(e)}")
            return RetrievalSource(
                name="Metaso知识库",
                content="",
                confidence=0.0,
                metadata={'error': str(e)},
                retrieval_time=time.time() - start_time,
                success=False
            )
    
    async def _retrieve_pubchem(self, query: str) -> RetrievalSource:
        """
        检索PubChem数据库
        """
        start_time = time.time()
        try:
            # 检查查询是否适合PubChem检索
            chemical_keywords = ['化合物', '分子', '化学式', '摩尔质量', '分子量', '甲烷', '乙烷', '苯', '水', 'H2O', 'CH4', 'C2H6', 'C6H6']
            if not any(keyword in query for keyword in chemical_keywords):
                return RetrievalSource(
                    name="PubChem数据库",
                    content="",
                    confidence=0.0,
                    metadata={'reason': '查询不适合化合物数据库检索'},
                    retrieval_time=time.time() - start_time,
                    success=False
                )
            
            # 尝试提取化合物名称并检索
            compound_keywords = ['甲烷', '乙烷', '苯', '水', 'H2O', 'CH4', 'C2H6', 'C6H6', '乙醇', 'C2H5OH']
            for keyword in compound_keywords:
                if keyword in query:
                    result = self.knowledge_api.get_compound_info(keyword)
                    
                    if result and 'error' not in result:
                        content = f"""化合物信息:
- 化合物名称: {result.get('name', 'N/A')}
- 分子式: {result.get('molecular_formula', 'N/A')}
- 分子量: {result.get('molecular_weight', 'N/A')}
- IUPAC名称: {result.get('iupac_name', 'N/A')}
- SMILES: {result.get('smiles', 'N/A')}"""
                        
                        return RetrievalSource(
                            name="PubChem数据库",
                            content=content,
                            confidence=0.9,
                            metadata={
                                'compound': keyword,
                                'compound_data': result
                            },
                            retrieval_time=time.time() - start_time,
                            success=True
                        )
            
            # 如果没有找到匹配的化合物
            return RetrievalSource(
                name="PubChem数据库",
                content="",
                confidence=0.0,
                metadata={'reason': '未找到匹配的化合物'},
                retrieval_time=time.time() - start_time,
                success=False
            )
            
        except Exception as e:
            logger.error(f"PubChem数据库检索异常: {str(e)}")
            return RetrievalSource(
                name="PubChem数据库",
                content="",
                confidence=0.0,
                metadata={'error': str(e)},
                retrieval_time=time.time() - start_time,
                success=False
            )
    
    def _filter_and_deduplicate(self, sources: List[RetrievalSource]) -> List[RetrievalSource]:
        """
        过滤和去重检索源
        
        Args:
            sources: 原始检索源列表
            
        Returns:
            List[RetrievalSource]: 过滤后的检索源列表
        """
        # 1. 过滤掉失败的和置信度过低的源
        filtered = []
        for source in sources:
            if source.success and source.confidence >= self.config['min_confidence_threshold']:
                filtered.append(source)
        
        # 2. 去重（如果启用）
        if self.config['enable_deduplication'] and len(filtered) > 1:
            deduplicated = []
            for i, source in enumerate(filtered):
                is_duplicate = False
                for j, existing in enumerate(deduplicated):
                    if self._calculate_similarity(source.content, existing.content) > self.config['similarity_threshold']:
                        # 保留置信度更高的源
                        if source.confidence > existing.confidence:
                            deduplicated[j] = source
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    deduplicated.append(source)
            
            return deduplicated
        
        return filtered
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            float: 相似度分数 (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # 简单的基于词汇重叠的相似度计算
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _generate_llm_summary(self, query: str, sources: List[RetrievalSource]) -> str:
        """
        使用LLM生成综合总结
        
        Args:
            query: 原始查询
            sources: 检索源列表
            
        Returns:
            str: LLM生成的总结
        """
        try:
            # 构建总结提示
            sources_text = ""
            for i, source in enumerate(sources, 1):
                sources_text += f"\n### 知识源 {i}: {source.name}\n"
                sources_text += f"置信度: {source.confidence:.2f}\n"
                sources_text += f"内容: {source.content[:500]}...\n"  # 限制长度
            
            summary_prompt = f"""请基于以下多个知识源的信息，为用户问题提供一个综合、准确、结构化的回答。

用户问题：{query}

检索到的知识源信息：{sources_text}

请要求：
1. 综合所有相关信息，提供准确、完整的回答
2. 如果不同知识源有冲突信息，请指出并分析
3. 保持回答的逻辑性和可读性，使用清晰的结构
4. 如果信息不足，请诚实说明
5. 优先使用置信度高的知识源信息
6. 回答长度控制在{self.config['max_summary_length']}字符以内

请提供综合回答："""
            
            # 选择可用的LLM模型
            available_models = self.llm_manager.get_available_models()
            preferred_models = ['qwen', 'tongyi', 'zhipu', 'openai']
            
            selected_model = None
            for model in preferred_models:
                if model in available_models:
                    selected_model = model
                    break
            
            if selected_model:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=summary_prompt)]
                
                summary = self.llm_manager.call_model(
                    selected_model,
                    messages,
                    temperature=0.3
                )
                
                return summary[:self.config['max_summary_length']]  # 确保不超过长度限制
            else:
                logger.warning("没有可用的LLM模型进行总结")
                return self._generate_simple_summary(sources)
                
        except Exception as e:
            logger.error(f"LLM总结生成异常: {str(e)}")
            return self._generate_simple_summary(sources)
    
    def _generate_simple_summary(self, sources: List[RetrievalSource]) -> str:
        """
        生成简单的文本总结（不使用LLM）
        
        Args:
            sources: 检索源列表
            
        Returns:
            str: 简单总结
        """
        if not sources:
            return "抱歉，未能从知识库中找到相关信息。请尝试重新表述您的问题或使用更具体的关键词。"
        
        summary_parts = []
        
        for source in sorted(sources, key=lambda x: x.confidence, reverse=True):
            if source.content:
                summary_parts.append(f"### {source.name}\n{source.content[:300]}...\n")
        
        if summary_parts:
            return "\n".join(summary_parts)
        else:
            return "检索到了相关信息，但内容为空。请尝试使用不同的关键词。"
    
    def _calculate_overall_confidence(self, sources: List[RetrievalSource]) -> float:
        """
        计算整体置信度
        
        Args:
            sources: 检索源列表
            
        Returns:
            float: 整体置信度 (0-1)
        """
        if not sources:
            return 0.0
        
        # 加权平均置信度
        total_weight = 0
        weighted_confidence = 0
        
        for source in sources:
            # 根据源的类型给予不同权重
            weight = {
                '本地RAG知识库': 0.8,
                'Metaso知识库': 0.9,
                '通义千问知识库': 0.7,
                'PubChem数据库': 1.0
            }.get(source.name, 0.5)
            
            weighted_confidence += source.confidence * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _update_stats(self, result: ComprehensiveResult):
        """
        更新性能统计信息
        
        Args:
            result: 综合检索结果
        """
        if result.confidence_score > self.config['min_confidence_threshold']:
            self.stats['successful_queries'] += 1
        
        # 更新平均响应时间
        total_time = self.stats['average_response_time'] * (self.stats['total_queries'] - 1)
        self.stats['average_response_time'] = (total_time + result.total_time) / self.stats['total_queries']
        
        # 更新各源成功率
        for source in result.sources:
            source_key = {
                '本地RAG知识库': 'local_rag',
                'Metaso知识库': 'metaso',
                '通义千问知识库': 'tongyi',
                'PubChem数据库': 'pubchem'
            }.get(source.name)
            
            if source_key and source.success:
                current_rate = self.stats['source_success_rates'][source_key]
                self.stats['source_success_rates'][source_key] = (current_rate + 1.0) / 2
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        success_rate = (self.stats['successful_queries'] / self.stats['total_queries'] 
                       if self.stats['total_queries'] > 0 else 0.0)
        
        return {
            'total_queries': self.stats['total_queries'],
            'success_rate': success_rate,
            'average_response_time': self.stats['average_response_time'],
            'source_success_rates': self.stats['source_success_rates'].copy(),
            'config': self.config.copy()
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新配置参数
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        logger.info(f"配置已更新: {new_config}")