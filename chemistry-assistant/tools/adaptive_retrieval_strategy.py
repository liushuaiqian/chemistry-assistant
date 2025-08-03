#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自适应检索策略管理器
根据查询复杂度动态调整检索策略
"""

import logging
import asyncio
from typing import Dict, Any, List, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass
from .query_complexity_analyzer import QueryComplexityAnalyzer, QueryComplexity, ComplexityAnalysis

if TYPE_CHECKING:
    from .rag_retriever import RAGRetriever
    from .chemistry_solver import ChemistrySolver

@dataclass
class RetrievalResult:
    """检索结果"""
    documents: List[str]
    strategy_used: str
    complexity_analysis: ComplexityAnalysis
    retrieval_steps: List[Dict[str, Any]]
    total_time: float
    confidence_score: float

class AdaptiveRetrievalStrategy:
    """自适应检索策略管理器"""
    
    def __init__(self, rag_retriever: 'RAGRetriever', chemistry_solver: Optional['ChemistrySolver'] = None):
        """
        初始化自适应检索策略管理器
        
        Args:
            rag_retriever: RAG检索器实例
            chemistry_solver: 化学计算工具（可选）
        """
        self.logger = logging.getLogger(__name__)
        self.complexity_analyzer = QueryComplexityAnalyzer()
        self.rag_retriever = rag_retriever
        self.chemistry_solver = chemistry_solver or ChemistrySolver()
        
        # 策略配置
        self.strategy_config = {
            "basic_vector_search": {
                "max_docs": 3,
                "use_rerank": False,
                "timeout": 5.0
            },
            "standard_retrieval_with_rerank": {
                "max_docs": 5,
                "use_rerank": True,
                "timeout": 10.0
            },
            "enhanced_retrieval_with_calculation": {
                "max_docs": 5,
                "use_rerank": True,
                "include_calculation": True,
                "timeout": 15.0
            },
            "multi_round_retrieval": {
                "rounds": 3,
                "docs_per_round": 3,
                "use_rerank": True,
                "timeout": 20.0
            },
            "comprehensive_analysis_retrieval": {
                "max_docs": 10,
                "use_rerank": True,
                "include_external": True,
                "include_reasoning": True,
                "timeout": 30.0
            }
        }
        
        # 性能统计
        self.performance_stats = {
            "total_queries": 0,
            "strategy_usage": {},
            "average_response_time": {},
            "success_rate": {}
        }
    
    async def adaptive_retrieve(self, query: str, user_feedback: Optional[Dict] = None) -> RetrievalResult:
        """
        自适应检索主入口
        
        Args:
            query: 用户查询
            user_feedback: 用户反馈（用于学习调整）
        
        Returns:
            RetrievalResult: 检索结果
        """
        import time
        start_time = time.time()
        
        try:
            # 1. 分析查询复杂度
            complexity_analysis = self.complexity_analyzer.analyze_complexity(query)
            
            # 2. 根据复杂度选择策略
            strategy = complexity_analysis.recommended_strategy
            
            # 3. 应用用户反馈调整（如果有）
            if user_feedback:
                strategy = self._adjust_strategy_with_feedback(strategy, user_feedback)
            
            # 4. 执行检索策略
            documents, retrieval_steps = await self._execute_strategy(query, strategy, complexity_analysis)
            
            # 5. 计算置信度
            confidence_score = self._calculate_confidence(documents, complexity_analysis, retrieval_steps)
            
            # 6. 更新性能统计
            total_time = time.time() - start_time
            self._update_performance_stats(strategy, total_time, len(documents) > 0)
            
            return RetrievalResult(
                documents=documents,
                strategy_used=strategy,
                complexity_analysis=complexity_analysis,
                retrieval_steps=retrieval_steps,
                total_time=total_time,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"自适应检索错误: {e}")
            # 降级到基础检索
            return await self._fallback_retrieval(query, start_time)
    
    async def _execute_strategy(self, query: str, strategy: str, complexity_analysis: ComplexityAnalysis) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        执行具体的检索策略
        
        Args:
            query: 查询文本
            strategy: 策略名称
            complexity_analysis: 复杂度分析结果
        
        Returns:
            Tuple[List[str], List[Dict[str, Any]]]: (文档列表, 检索步骤)
        """
        retrieval_steps = []
        
        if strategy == "basic_vector_search":
            return await self._basic_vector_search(query, retrieval_steps)
        
        elif strategy == "standard_retrieval_with_rerank":
            return await self._standard_retrieval_with_rerank(query, retrieval_steps)
        
        elif strategy == "enhanced_retrieval_with_calculation":
            return await self._enhanced_retrieval_with_calculation(query, retrieval_steps)
        
        elif strategy == "multi_round_retrieval":
            return await self._multi_round_retrieval(query, complexity_analysis, retrieval_steps)
        
        elif strategy == "comprehensive_analysis_retrieval":
            return await self._comprehensive_analysis_retrieval(query, complexity_analysis, retrieval_steps)
        
        else:
            # 未知策略，降级到标准检索
            self.logger.warning(f"未知策略 {strategy}，降级到标准检索")
            return await self._standard_retrieval_with_rerank(query, retrieval_steps)
    
    async def _basic_vector_search(self, query: str, retrieval_steps: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        基础向量搜索策略
        """
        config = self.strategy_config["basic_vector_search"]
        
        step = {
            "step": "basic_vector_search",
            "description": "执行基础向量搜索",
            "start_time": asyncio.get_event_loop().time()
        }
        
        try:
            # 快速向量检索，不使用重排序
            docs = self.rag_retriever.retrieve_comprehensive(
                query, 
                textbook_k=config["max_docs"]//2, 
                question_k=config["max_docs"]//2,
                rerank_top_n=None if not config["use_rerank"] else config["max_docs"]
            )
            
            step["success"] = True
            step["documents_found"] = len(docs)
            
        except Exception as e:
            self.logger.error(f"基础向量搜索错误: {e}")
            docs = []
            step["success"] = False
            step["error"] = str(e)
        
        step["end_time"] = asyncio.get_event_loop().time()
        retrieval_steps.append(step)
        
        return docs, retrieval_steps
    
    async def _standard_retrieval_with_rerank(self, query: str, retrieval_steps: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        标准检索+重排序策略
        """
        config = self.strategy_config["standard_retrieval_with_rerank"]
        
        step = {
            "step": "standard_retrieval_with_rerank",
            "description": "执行标准检索并重排序",
            "start_time": asyncio.get_event_loop().time()
        }
        
        try:
            # 使用重排序的综合检索
            docs = self.rag_retriever.retrieve_comprehensive(
                query,
                textbook_k=config["max_docs"]//2 + 1,
                question_k=config["max_docs"]//2,
                rerank_top_n=config["max_docs"]
            )
            
            step["success"] = True
            step["documents_found"] = len(docs)
            step["rerank_used"] = self.rag_retriever.use_reranker
            
        except Exception as e:
            self.logger.error(f"标准检索错误: {e}")
            docs = []
            step["success"] = False
            step["error"] = str(e)
        
        step["end_time"] = asyncio.get_event_loop().time()
        retrieval_steps.append(step)
        
        return docs, retrieval_steps
    
    async def _enhanced_retrieval_with_calculation(self, query: str, retrieval_steps: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        增强检索+计算策略
        """
        config = self.strategy_config["enhanced_retrieval_with_calculation"]
        
        # 步骤1: 标准检索
        docs, retrieval_steps = await self._standard_retrieval_with_rerank(query, retrieval_steps)
        
        # 步骤2: 化学计算增强
        calc_step = {
            "step": "chemistry_calculation",
            "description": "执行化学计算增强",
            "start_time": asyncio.get_event_loop().time()
        }
        
        try:
            # 尝试提取化学计算需求
            calculation_results = await self._perform_chemistry_calculations(query)
            
            if calculation_results:
                # 将计算结果添加到文档中
                calc_doc = f"化学计算结果：\n{calculation_results}"
                docs.insert(0, calc_doc)  # 插入到开头
                
                calc_step["success"] = True
                calc_step["calculation_performed"] = True
                calc_step["results"] = calculation_results
            else:
                calc_step["success"] = True
                calc_step["calculation_performed"] = False
                calc_step["note"] = "未检测到需要计算的内容"
            
        except Exception as e:
            self.logger.error(f"化学计算错误: {e}")
            calc_step["success"] = False
            calc_step["error"] = str(e)
        
        calc_step["end_time"] = asyncio.get_event_loop().time()
        retrieval_steps.append(calc_step)
        
        return docs, retrieval_steps
    
    async def _multi_round_retrieval(self, query: str, complexity_analysis: ComplexityAnalysis, retrieval_steps: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        多轮检索策略
        """
        config = self.strategy_config["multi_round_retrieval"]
        all_docs = []
        
        # 分解查询为多个子查询
        sub_queries = self._decompose_query(query, complexity_analysis)
        
        for round_num, sub_query in enumerate(sub_queries[:config["rounds"]], 1):
            step = {
                "step": f"multi_round_retrieval_round_{round_num}",
                "description": f"第{round_num}轮检索: {sub_query}",
                "sub_query": sub_query,
                "start_time": asyncio.get_event_loop().time()
            }
            
            try:
                # 每轮检索
                round_docs = self.rag_retriever.retrieve_comprehensive(
                    sub_query,
                    textbook_k=config["docs_per_round"]//2 + 1,
                    question_k=config["docs_per_round"]//2,
                    rerank_top_n=config["docs_per_round"]
                )
                
                # 去重并添加到总结果中
                for doc in round_docs:
                    if doc not in all_docs:
                        all_docs.append(doc)
                
                step["success"] = True
                step["documents_found"] = len(round_docs)
                step["total_unique_docs"] = len(all_docs)
                
            except Exception as e:
                self.logger.error(f"第{round_num}轮检索错误: {e}")
                step["success"] = False
                step["error"] = str(e)
            
            step["end_time"] = asyncio.get_event_loop().time()
            retrieval_steps.append(step)
        
        # 最终重排序（如果文档过多）
        if len(all_docs) > 8 and self.rag_retriever.use_reranker:
            final_step = {
                "step": "final_rerank",
                "description": "对多轮检索结果进行最终重排序",
                "start_time": asyncio.get_event_loop().time()
            }
            
            try:
                if self.rag_retriever.text_reranker and self.rag_retriever.text_reranker.is_available():
                    ranked_results = self.rag_retriever.text_reranker.rerank_with_scores(
                        query, all_docs, top_n=8
                    )
                    all_docs = [doc for doc, score in ranked_results]
                    
                    final_step["success"] = True
                    final_step["final_doc_count"] = len(all_docs)
                else:
                    all_docs = all_docs[:8]  # 简单截断
                    final_step["success"] = True
                    final_step["note"] = "重排序器不可用，使用截断"
                
            except Exception as e:
                self.logger.error(f"最终重排序错误: {e}")
                all_docs = all_docs[:8]  # 降级处理
                final_step["success"] = False
                final_step["error"] = str(e)
            
            final_step["end_time"] = asyncio.get_event_loop().time()
            retrieval_steps.append(final_step)
        
        return all_docs, retrieval_steps
    
    async def _comprehensive_analysis_retrieval(self, query: str, complexity_analysis: ComplexityAnalysis, retrieval_steps: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        综合分析检索策略
        """
        config = self.strategy_config["comprehensive_analysis_retrieval"]
        
        # 步骤1: 多轮检索
        docs, retrieval_steps = await self._multi_round_retrieval(query, complexity_analysis, retrieval_steps)
        
        # 步骤2: 化学计算增强
        calc_step = {
            "step": "comprehensive_calculation",
            "description": "综合化学计算分析",
            "start_time": asyncio.get_event_loop().time()
        }
        
        try:
            calculation_results = await self._perform_chemistry_calculations(query)
            if calculation_results:
                calc_doc = f"综合化学计算分析：\n{calculation_results}"
                docs.insert(0, calc_doc)
                calc_step["success"] = True
                calc_step["calculation_performed"] = True
            else:
                calc_step["success"] = True
                calc_step["calculation_performed"] = False
        except Exception as e:
            calc_step["success"] = False
            calc_step["error"] = str(e)
        
        calc_step["end_time"] = asyncio.get_event_loop().time()
        retrieval_steps.append(calc_step)
        
        # 步骤3: 外部知识注入（模拟）
        external_step = {
            "step": "external_knowledge_injection",
            "description": "外部知识源检索",
            "start_time": asyncio.get_event_loop().time()
        }
        
        try:
            # 这里可以集成外部API或知识库
            external_knowledge = self._get_external_knowledge(query, complexity_analysis)
            if external_knowledge:
                docs.append(f"外部知识补充：\n{external_knowledge}")
                external_step["success"] = True
                external_step["knowledge_added"] = True
            else:
                external_step["success"] = True
                external_step["knowledge_added"] = False
        except Exception as e:
            external_step["success"] = False
            external_step["error"] = str(e)
        
        external_step["end_time"] = asyncio.get_event_loop().time()
        retrieval_steps.append(external_step)
        
        return docs, retrieval_steps
    
    async def _perform_chemistry_calculations(self, query: str) -> Optional[str]:
        """
        执行化学计算
        """
        try:
            # 检测是否需要摩尔质量计算
            if any(keyword in query for keyword in ['摩尔质量', '分子量', '相对分子质量', 'Mr']):
                # 尝试提取化学式
                import re
                formulas = re.findall(r'[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*', query)
                if formulas:
                    results = []
                    for formula in formulas:
                        try:
                            molar_mass = self.chemistry_solver.calculate_molar_mass(formula)
                            results.append(f"{formula}的摩尔质量: {molar_mass:.2f} g/mol")
                        except:
                            continue
                    return "\n".join(results) if results else None
            
            # 检测是否需要方程式平衡
            if any(keyword in query for keyword in ['平衡', '配平', '化学方程式']):
                # 这里可以添加方程式平衡逻辑
                return "化学方程式平衡功能正在开发中"
            
            return None
            
        except Exception as e:
            self.logger.error(f"化学计算错误: {e}")
            return None
    
    def _decompose_query(self, query: str, complexity_analysis: ComplexityAnalysis) -> List[str]:
        """
        分解复杂查询为多个子查询
        """
        sub_queries = [query]  # 默认包含原查询
        
        # 基于复杂度特征分解查询
        features = complexity_analysis.features
        
        # 如果包含多个概念，尝试分解
        if 'multiple_concepts' in features.get('complex_patterns', {}):
            # 简单的关键词分解
            keywords = []
            for category in features.get('keywords', {}).values():
                keywords.extend([kw for kw, _ in category])
            
            for keyword in keywords[:2]:  # 最多取前2个关键词
                sub_queries.append(f"{keyword}相关知识")
        
        # 如果是比较类查询，分解为单独概念
        if 'comparison' in features.get('complex_patterns', {}):
            # 提取比较的对象
            import re
            comparison_objects = re.findall(r'([A-Za-z\u4e00-\u9fa5]+)(?:和|与|及)([A-Za-z\u4e00-\u9fa5]+)', query)
            for obj1, obj2 in comparison_objects:
                sub_queries.extend([obj1, obj2])
        
        return list(set(sub_queries))  # 去重
    
    def _get_external_knowledge(self, query: str, complexity_analysis: ComplexityAnalysis) -> Optional[str]:
        """
        获取外部知识（模拟实现）
        """
        # 这里可以集成外部API，如Wikipedia、化学数据库等
        # 目前返回模拟数据
        if complexity_analysis.complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            return f"针对复杂查询'{query}'的外部知识补充：建议查阅相关专业文献和数据库"
        return None
    
    def _adjust_strategy_with_feedback(self, strategy: str, feedback: Dict[str, Any]) -> str:
        """
        根据用户反馈调整策略
        """
        # 简单的反馈学习机制
        if feedback.get('satisfaction', 0) < 3:  # 满意度低
            # 升级策略
            strategy_hierarchy = [
                "basic_vector_search",
                "standard_retrieval_with_rerank", 
                "enhanced_retrieval_with_calculation",
                "multi_round_retrieval",
                "comprehensive_analysis_retrieval"
            ]
            
            current_index = strategy_hierarchy.index(strategy) if strategy in strategy_hierarchy else 0
            if current_index < len(strategy_hierarchy) - 1:
                return strategy_hierarchy[current_index + 1]
        
        return strategy
    
    def _calculate_confidence(self, documents: List[str], complexity_analysis: ComplexityAnalysis, retrieval_steps: List[Dict[str, Any]]) -> float:
        """
        计算检索结果的置信度
        """
        confidence = 0.5  # 基础置信度
        
        # 文档数量影响
        if documents:
            doc_score = min(len(documents) / 5, 0.3)  # 最多贡献0.3
            confidence += doc_score
        else:
            confidence -= 0.3
        
        # 检索步骤成功率影响
        successful_steps = sum(1 for step in retrieval_steps if step.get('success', False))
        total_steps = len(retrieval_steps)
        if total_steps > 0:
            success_rate = successful_steps / total_steps
            confidence += success_rate * 0.2
        
        # 复杂度匹配度影响
        if complexity_analysis.complexity == QueryComplexity.SIMPLE and len(documents) > 0:
            confidence += 0.1  # 简单查询有结果就加分
        elif complexity_analysis.complexity == QueryComplexity.VERY_COMPLEX and len(retrieval_steps) > 2:
            confidence += 0.1  # 复杂查询多步骤处理加分
        
        return max(0.0, min(1.0, confidence))
    
    def _update_performance_stats(self, strategy: str, response_time: float, success: bool):
        """
        更新性能统计
        """
        self.performance_stats["total_queries"] += 1
        
        # 策略使用统计
        if strategy not in self.performance_stats["strategy_usage"]:
            self.performance_stats["strategy_usage"][strategy] = 0
        self.performance_stats["strategy_usage"][strategy] += 1
        
        # 响应时间统计
        if strategy not in self.performance_stats["average_response_time"]:
            self.performance_stats["average_response_time"][strategy] = []
        self.performance_stats["average_response_time"][strategy].append(response_time)
        
        # 成功率统计
        if strategy not in self.performance_stats["success_rate"]:
            self.performance_stats["success_rate"][strategy] = {"success": 0, "total": 0}
        self.performance_stats["success_rate"][strategy]["total"] += 1
        if success:
            self.performance_stats["success_rate"][strategy]["success"] += 1
    
    async def _fallback_retrieval(self, query: str, start_time: float) -> RetrievalResult:
        """
        降级检索策略
        """
        import time
        
        try:
            docs = self.rag_retriever.retrieve_comprehensive(query, textbook_k=2, question_k=2)
            
            fallback_analysis = ComplexityAnalysis(
                complexity=QueryComplexity.MODERATE,
                score=0.5,
                reasoning="降级处理",
                features={},
                recommended_strategy="basic_vector_search"
            )
            
            return RetrievalResult(
                documents=docs,
                strategy_used="fallback_basic_search",
                complexity_analysis=fallback_analysis,
                retrieval_steps=[{"step": "fallback", "success": True}],
                total_time=time.time() - start_time,
                confidence_score=0.3
            )
            
        except Exception as e:
            self.logger.error(f"降级检索也失败: {e}")
            return RetrievalResult(
                documents=[],
                strategy_used="failed",
                complexity_analysis=ComplexityAnalysis(
                    complexity=QueryComplexity.SIMPLE,
                    score=0.0,
                    reasoning="检索失败",
                    features={},
                    recommended_strategy="basic_vector_search"
                ),
                retrieval_steps=[{"step": "fallback", "success": False, "error": str(e)}],
                total_time=time.time() - start_time,
                confidence_score=0.0
            )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        获取性能报告
        """
        report = {
            "total_queries": self.performance_stats["total_queries"],
            "strategy_distribution": {},
            "average_response_times": {},
            "success_rates": {}
        }
        
        # 策略分布
        total = self.performance_stats["total_queries"]
        for strategy, count in self.performance_stats["strategy_usage"].items():
            report["strategy_distribution"][strategy] = {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0
            }
        
        # 平均响应时间
        for strategy, times in self.performance_stats["average_response_time"].items():
            if times:
                report["average_response_times"][strategy] = sum(times) / len(times)
        
        # 成功率
        for strategy, stats in self.performance_stats["success_rate"].items():
            if stats["total"] > 0:
                report["success_rates"][strategy] = stats["success"] / stats["total"] * 100
        
        return report