#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合检索性能监控组件
用于显示检索性能统计和实时监控信息
"""

import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: str
    query: str
    total_time: float
    confidence_score: float
    sources_count: int
    successful_sources: List[str]
    strategy_used: str
    source_times: Dict[str, float]
    
class PerformanceMonitor:
    """
    性能监控器
    
    功能：
    1. 记录每次检索的性能数据
    2. 计算统计指标
    3. 生成性能报告
    4. 提供实时监控数据
    """
    
    def __init__(self, max_records: int = 1000):
        """
        初始化性能监控器
        
        Args:
            max_records: 最大记录数量
        """
        self.max_records = max_records
        self.records: List[PerformanceMetrics] = []
        self.session_start_time = time.time()
        
    def record_performance(self, 
                          query: str,
                          total_time: float,
                          confidence_score: float,
                          sources_count: int,
                          successful_sources: List[str],
                          strategy_used: str,
                          source_times: Dict[str, float]):
        """
        记录一次检索的性能数据
        
        Args:
            query: 查询文本
            total_time: 总耗时
            confidence_score: 置信度分数
            sources_count: 源数量
            successful_sources: 成功的源列表
            strategy_used: 使用的策略
            source_times: 各源的耗时
        """
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            query=query[:50] + "..." if len(query) > 50 else query,
            total_time=total_time,
            confidence_score=confidence_score,
            sources_count=sources_count,
            successful_sources=successful_sources,
            strategy_used=strategy_used,
            source_times=source_times
        )
        
        self.records.append(metrics)
        
        # 保持记录数量在限制内
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            Dict[str, Any]: 性能摘要数据
        """
        if not self.records:
            return {
                'total_queries': 0,
                'average_response_time': 0.0,
                'average_confidence': 0.0,
                'success_rate': 0.0,
                'most_used_strategy': 'N/A',
                'source_performance': {},
                'session_duration': time.time() - self.session_start_time
            }
        
        # 基本统计
        total_queries = len(self.records)
        avg_response_time = sum(r.total_time for r in self.records) / total_queries
        avg_confidence = sum(r.confidence_score for r in self.records) / total_queries
        
        # 成功率（置信度 > 0.3 视为成功）
        successful_queries = sum(1 for r in self.records if r.confidence_score > 0.3)
        success_rate = successful_queries / total_queries
        
        # 最常用策略
        strategy_counts = {}
        for record in self.records:
            strategy = record.strategy_used
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        most_used_strategy = max(strategy_counts.items(), key=lambda x: x[1])[0] if strategy_counts else 'N/A'
        
        # 各源性能统计
        source_performance = self._calculate_source_performance()
        
        return {
            'total_queries': total_queries,
            'average_response_time': round(avg_response_time, 2),
            'average_confidence': round(avg_confidence, 2),
            'success_rate': round(success_rate * 100, 1),
            'most_used_strategy': most_used_strategy,
            'source_performance': source_performance,
            'session_duration': round(time.time() - self.session_start_time, 1)
        }
    
    def _calculate_source_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        计算各源的性能统计
        
        Returns:
            Dict[str, Dict[str, Any]]: 各源的性能数据
        """
        source_stats = {
            '本地RAG知识库': {'total_calls': 0, 'successful_calls': 0, 'total_time': 0.0, 'avg_time': 0.0},
            'Metaso知识库': {'total_calls': 0, 'successful_calls': 0, 'total_time': 0.0, 'avg_time': 0.0},
            '通义千问知识库': {'total_calls': 0, 'successful_calls': 0, 'total_time': 0.0, 'avg_time': 0.0},
            'PubChem数据库': {'total_calls': 0, 'successful_calls': 0, 'total_time': 0.0, 'avg_time': 0.0}
        }
        
        for record in self.records:
            for source_name in record.successful_sources:
                if source_name in source_stats:
                    source_stats[source_name]['successful_calls'] += 1
            
            for source_name, source_time in record.source_times.items():
                if source_name in source_stats:
                    source_stats[source_name]['total_calls'] += 1
                    source_stats[source_name]['total_time'] += source_time
        
        # 计算平均时间和成功率
        for source_name, stats in source_stats.items():
            if stats['total_calls'] > 0:
                stats['avg_time'] = round(stats['total_time'] / stats['total_calls'], 2)
                stats['success_rate'] = round(stats['successful_calls'] / stats['total_calls'] * 100, 1)
            else:
                stats['success_rate'] = 0.0
        
        return source_stats
    
    def get_recent_performance(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """
        获取最近一段时间的性能数据
        
        Args:
            minutes: 时间范围（分钟）
            
        Returns:
            List[Dict[str, Any]]: 最近的性能记录
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_records = []
        for record in self.records:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time >= cutoff_time:
                recent_records.append(asdict(record))
        
        return recent_records
    
    def get_performance_trends(self) -> Dict[str, List[float]]:
        """
        获取性能趋势数据
        
        Returns:
            Dict[str, List[float]]: 趋势数据
        """
        if len(self.records) < 2:
            return {
                'response_times': [],
                'confidence_scores': [],
                'timestamps': []
            }
        
        # 取最近50条记录进行趋势分析
        recent_records = self.records[-50:]
        
        return {
            'response_times': [r.total_time for r in recent_records],
            'confidence_scores': [r.confidence_score for r in recent_records],
            'timestamps': [r.timestamp for r in recent_records]
        }
    
    def generate_performance_report(self) -> str:
        """
        生成详细的性能报告
        
        Returns:
            str: Markdown格式的性能报告
        """
        summary = self.get_performance_summary()
        source_performance = summary['source_performance']
        
        report = f"""# 📊 综合检索性能报告

## 📈 总体统计
- **总查询次数**: {summary['total_queries']}
- **平均响应时间**: {summary['average_response_time']}秒
- **平均置信度**: {summary['average_confidence']:.2f}
- **成功率**: {summary['success_rate']}%
- **最常用策略**: {summary['most_used_strategy']}
- **会话时长**: {summary['session_duration']:.1f}秒

## 🔍 各知识源性能
"""
        
        for source_name, stats in source_performance.items():
            if stats['total_calls'] > 0:
                report += f"""### {source_name}
- 调用次数: {stats['total_calls']}
- 成功次数: {stats['successful_calls']}
- 成功率: {stats['success_rate']}%
- 平均响应时间: {stats['avg_time']}秒

"""
        
        # 添加最近查询记录
        recent_records = self.get_recent_performance(30)
        if recent_records:
            report += "## 🕒 最近30分钟查询记录\n\n"
            report += "| 时间 | 查询 | 耗时(秒) | 置信度 | 成功源数 |\n"
            report += "|------|------|----------|--------|----------|\n"
            
            for record in recent_records[-10:]:  # 显示最近10条
                timestamp = datetime.fromisoformat(record['timestamp']).strftime('%H:%M:%S')
                report += f"| {timestamp} | {record['query']} | {record['total_time']:.2f} | {record['confidence_score']:.2f} | {len(record['successful_sources'])} |\n"
        
        return report
    
    def export_data(self, filepath: str):
        """
        导出性能数据到文件
        
        Args:
            filepath: 导出文件路径
        """
        export_data = {
            'session_start_time': self.session_start_time,
            'export_time': time.time(),
            'records': [asdict(record) for record in self.records],
            'summary': self.get_performance_summary()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def clear_records(self):
        """
        清空所有记录
        """
        self.records.clear()
        self.session_start_time = time.time()

# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """
    获取全局性能监控器实例
    
    Returns:
        PerformanceMonitor: 性能监控器实例
    """
    return performance_monitor