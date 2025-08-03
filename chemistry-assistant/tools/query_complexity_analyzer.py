#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
查询复杂度分析器
用于评估查询的复杂度并决定检索策略
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass

class QueryComplexity(Enum):
    """查询复杂度级别"""
    SIMPLE = "simple"           # 简单查询：基本事实查询
    MODERATE = "moderate"       # 中等查询：需要一定推理
    COMPLEX = "complex"         # 复杂查询：多步推理、分析
    VERY_COMPLEX = "very_complex"  # 极复杂查询：深度分析、综合推理

@dataclass
class ComplexityAnalysis:
    """复杂度分析结果"""
    complexity: QueryComplexity
    score: float  # 0-1之间的复杂度分数
    reasoning: str  # 分析原因
    features: Dict[str, Any]  # 检测到的特征
    recommended_strategy: str  # 推荐的检索策略

class QueryComplexityAnalyzer:
    """查询复杂度分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_patterns()
        self._setup_keywords()
    
    def _setup_patterns(self):
        """设置正则表达式模式"""
        # 复杂查询模式
        self.complex_patterns = {
            'multi_step': r'(首先|然后|接下来|最后|步骤|过程|如何.*然后|先.*再)',
            'comparison': r'(比较|对比|区别|差异|相同|不同|优缺点|vs|versus)',
            'analysis': r'(分析|解释|原理|机制|为什么|怎样|如何|影响|作用|关系)',
            'synthesis': r'(综合|总结|归纳|整合|结合|考虑.*因素)',
            'evaluation': r'(评价|评估|判断|优劣|好坏|合理性|可行性)',
            'application': r'(应用|实际|实践|案例|例子|举例|实验|操作)',
            'multiple_concepts': r'(和|与|以及|同时|既.*又|不仅.*还|包括.*和)',
            'conditional': r'(如果|假设|当.*时|在.*条件下|情况下)',
            'quantitative': r'(计算|求解|多少|数量|浓度|质量|体积|温度|压力)',
        }
        
        # 简单查询模式
        self.simple_patterns = {
            'definition': r'^(什么是|定义|含义)',
            'basic_fact': r'^(.*是什么|.*的.*是)',
            'yes_no': r'(是否|是不是|对不对|正确吗)',
            'single_word': r'^\w+$',
        }
    
    def _setup_keywords(self):
        """设置关键词库"""
        # 复杂度指示词
        self.complexity_keywords = {
            'high_complexity': {
                '机制': 0.8, '原理': 0.7, '分析': 0.6, '解释': 0.6,
                '推导': 0.8, '证明': 0.8, '设计': 0.7, '优化': 0.7,
                '综合': 0.8, '评价': 0.7, '比较': 0.6, '应用': 0.6,
                '影响因素': 0.8, '相互作用': 0.7, '平衡': 0.6,
                '动力学': 0.8, '热力学': 0.8, '反应机理': 0.9
            },
            'medium_complexity': {
                '计算': 0.5, '求解': 0.5, '方程': 0.5, '公式': 0.4,
                '反应': 0.4, '化合物': 0.3, '性质': 0.4, '结构': 0.4,
                '制备': 0.5, '检验': 0.5, '鉴别': 0.5
            },
            'low_complexity': {
                '是什么': 0.2, '定义': 0.2, '含义': 0.2, '概念': 0.2,
                '名称': 0.1, '符号': 0.1, '分子式': 0.2, '化学式': 0.2
            }
        }
        
        # 化学领域特定复杂度指标
        self.chemistry_complexity = {
            'organic_chemistry': {
                '有机合成': 0.9, '反应机理': 0.9, '立体化学': 0.8,
                '芳香性': 0.7, '共轭': 0.6, '异构': 0.6
            },
            'physical_chemistry': {
                '量子化学': 0.9, '统计热力学': 0.9, '电化学': 0.8,
                '表面化学': 0.8, '胶体': 0.7, '相平衡': 0.7
            },
            'analytical_chemistry': {
                '仪器分析': 0.7, '光谱': 0.6, '色谱': 0.6,
                '质谱': 0.7, '电分析': 0.6, '滴定': 0.4
            }
        }
    
    def analyze_complexity(self, query: str) -> ComplexityAnalysis:
        """分析查询复杂度"""
        try:
            # 基础特征提取
            features = self._extract_features(query)
            
            # 计算复杂度分数
            score = self._calculate_complexity_score(query, features)
            
            # 确定复杂度级别
            complexity = self._determine_complexity_level(score)
            
            # 生成分析原因
            reasoning = self._generate_reasoning(features, score)
            
            # 推荐检索策略
            strategy = self._recommend_strategy(complexity, features)
            
            return ComplexityAnalysis(
                complexity=complexity,
                score=score,
                reasoning=reasoning,
                features=features,
                recommended_strategy=strategy
            )
            
        except Exception as e:
            self.logger.error(f"复杂度分析错误: {e}")
            # 返回默认中等复杂度
            return ComplexityAnalysis(
                complexity=QueryComplexity.MODERATE,
                score=0.5,
                reasoning="分析过程出错，使用默认策略",
                features={},
                recommended_strategy="standard_retrieval"
            )
    
    def _extract_features(self, query: str) -> Dict[str, Any]:
        """提取查询特征"""
        features = {
            'length': len(query),
            'word_count': len(query.split()),
            'question_marks': query.count('？') + query.count('?'),
            'complex_patterns': {},
            'simple_patterns': {},
            'keywords': {},
            'chemistry_domain': {},
            'has_numbers': bool(re.search(r'\d+', query)),
            'has_formulas': bool(re.search(r'[A-Z][a-z]?\d*', query)),
            'has_equations': bool(re.search(r'[=→←↔]', query))
        }
        
        # 检测复杂模式
        for pattern_name, pattern in self.complex_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                features['complex_patterns'][pattern_name] = True
        
        # 检测简单模式
        for pattern_name, pattern in self.simple_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                features['simple_patterns'][pattern_name] = True
        
        # 检测关键词
        for category, keywords in self.complexity_keywords.items():
            for keyword, weight in keywords.items():
                if keyword in query:
                    if category not in features['keywords']:
                        features['keywords'][category] = []
                    features['keywords'][category].append((keyword, weight))
        
        # 检测化学领域特征
        for domain, keywords in self.chemistry_complexity.items():
            for keyword, weight in keywords.items():
                if keyword in query:
                    if domain not in features['chemistry_domain']:
                        features['chemistry_domain'][domain] = []
                    features['chemistry_domain'][domain].append((keyword, weight))
        
        return features
    
    def _calculate_complexity_score(self, query: str, features: Dict[str, Any]) -> float:
        """计算复杂度分数 (0-1)"""
        score = 0.0
        
        # 基础长度权重
        length_score = min(features['length'] / 200, 0.3)  # 最多贡献0.3
        score += length_score
        
        # 词数权重
        word_score = min(features['word_count'] / 50, 0.2)  # 最多贡献0.2
        score += word_score
        
        # 复杂模式权重
        complex_pattern_score = len(features['complex_patterns']) * 0.1
        score += min(complex_pattern_score, 0.4)  # 最多贡献0.4
        
        # 简单模式负权重
        simple_pattern_penalty = len(features['simple_patterns']) * 0.15
        score -= simple_pattern_penalty
        
        # 关键词权重
        for category, keyword_list in features['keywords'].items():
            if category == 'high_complexity':
                for _, weight in keyword_list:
                    score += weight * 0.3
            elif category == 'medium_complexity':
                for _, weight in keyword_list:
                    score += weight * 0.2
            elif category == 'low_complexity':
                for _, weight in keyword_list:
                    score -= weight * 0.2
        
        # 化学领域特征权重
        for domain, keyword_list in features['chemistry_domain'].items():
            for _, weight in keyword_list:
                score += weight * 0.25
        
        # 特殊特征权重
        if features['has_numbers']:
            score += 0.1
        if features['has_formulas']:
            score += 0.15
        if features['has_equations']:
            score += 0.2
        
        # 多问号表示复杂查询
        if features['question_marks'] > 1:
            score += 0.1
        
        # 确保分数在0-1范围内
        return max(0.0, min(1.0, score))
    
    def _determine_complexity_level(self, score: float) -> QueryComplexity:
        """根据分数确定复杂度级别"""
        if score >= 0.8:
            return QueryComplexity.VERY_COMPLEX
        elif score >= 0.6:
            return QueryComplexity.COMPLEX
        elif score >= 0.3:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def _generate_reasoning(self, features: Dict[str, Any], score: float) -> str:
        """生成分析原因"""
        reasons = []
        
        if features['complex_patterns']:
            patterns = list(features['complex_patterns'].keys())
            reasons.append(f"检测到复杂模式: {', '.join(patterns)}")
        
        if features['simple_patterns']:
            patterns = list(features['simple_patterns'].keys())
            reasons.append(f"检测到简单模式: {', '.join(patterns)}")
        
        if features['keywords']:
            for category, keyword_list in features['keywords'].items():
                keywords = [kw for kw, _ in keyword_list]
                reasons.append(f"{category}关键词: {', '.join(keywords)}")
        
        if features['chemistry_domain']:
            for domain, keyword_list in features['chemistry_domain'].items():
                keywords = [kw for kw, _ in keyword_list]
                reasons.append(f"{domain}领域特征: {', '.join(keywords)}")
        
        if features['has_equations']:
            reasons.append("包含化学方程式")
        
        if features['word_count'] > 30:
            reasons.append("查询较长，可能涉及多个概念")
        
        return f"复杂度分数: {score:.2f}. " + "; ".join(reasons) if reasons else f"复杂度分数: {score:.2f}"
    
    def _recommend_strategy(self, complexity: QueryComplexity, features: Dict[str, Any]) -> str:
        """推荐检索策略"""
        if complexity == QueryComplexity.SIMPLE:
            return "basic_vector_search"
        elif complexity == QueryComplexity.MODERATE:
            if features['has_numbers'] or features['has_formulas']:
                return "enhanced_retrieval_with_calculation"
            else:
                return "standard_retrieval_with_rerank"
        elif complexity == QueryComplexity.COMPLEX:
            return "multi_round_retrieval"
        else:  # VERY_COMPLEX
            return "comprehensive_analysis_retrieval"
    
    def get_strategy_description(self, strategy: str) -> str:
        """获取策略描述"""
        descriptions = {
            "basic_vector_search": "基础向量搜索：快速检索最相关的文档",
            "standard_retrieval_with_rerank": "标准检索+重排序：向量检索后使用排序器优化结果",
            "enhanced_retrieval_with_calculation": "增强检索+计算：结合检索和化学计算工具",
            "multi_round_retrieval": "多轮检索：分步检索，逐步深入分析",
            "comprehensive_analysis_retrieval": "综合分析检索：多源检索+外部知识+推理链"
        }
        return descriptions.get(strategy, "未知策略")