#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自适应检索功能测试脚本
用于验证自适应检索系统的各项功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controller import Controller
from utils.logger import get_logger

logger = get_logger(__name__)

class AdaptiveRetrievalTester:
    """自适应检索功能测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.controller = None
        self.test_results = []
        
    def setup(self):
        """设置测试环境"""
        try:
            # 初始化Controller，启用自适应检索
            self.controller = Controller(use_reranker=True, enable_adaptive=True)
            logger.info("测试环境初始化成功")
            return True
        except Exception as e:
            logger.error(f"测试环境初始化失败: {e}")
            return False
    
    def test_complexity_analysis(self):
        """测试复杂度分析功能"""
        print("\n=== 测试复杂度分析功能 ===")
        
        test_queries = [
            "什么是氢气？",  # 简单查询
            "计算H2O的摩尔质量",  # 中等查询
            "分析苯环的芳香性机理，包括分子轨道理论和共振结构",  # 复杂查询
            "比较不同催化剂对Haber-Bosch反应的影响，并分析反应动力学和热力学因素",  # 非常复杂
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                result = self.controller.analyze_query_complexity(query)
                if result.get('success'):
                    analysis = result['analysis']
                    print(f"\n测试 {i}: {query[:30]}...")
                    print(f"  复杂度: {analysis.get('complexity', 'unknown')}")
                    print(f"  分数: {analysis.get('score', 0):.2f}")
                    print(f"  推荐策略: {analysis.get('recommended_strategy', 'unknown')}")
                    print(f"  分析原因: {analysis.get('reasoning', '无')[:50]}...")
                    
                    self.test_results.append({
                        'test': f'complexity_analysis_{i}',
                        'status': 'PASS',
                        'query': query,
                        'complexity': analysis.get('complexity'),
                        'score': analysis.get('score')
                    })
                else:
                    print(f"\n测试 {i} 失败: {result.get('error', '未知错误')}")
                    self.test_results.append({
                        'test': f'complexity_analysis_{i}',
                        'status': 'FAIL',
                        'error': result.get('error')
                    })
            except Exception as e:
                print(f"\n测试 {i} 异常: {str(e)}")
                self.test_results.append({
                    'test': f'complexity_analysis_{i}',
                    'status': 'ERROR',
                    'error': str(e)
                })
    
    async def test_adaptive_retrieval(self):
        """测试自适应检索功能"""
        print("\n=== 测试自适应检索功能 ===")
        
        test_queries = [
            "氢气的化学式是什么？",  # 简单查询
            "计算碳酸钙CaCO3的摩尔质量",  # 计算查询
            "解释化学平衡的勒夏特列原理及其应用",  # 复杂理论查询
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                print(f"\n测试 {i}: {query}")
                start_time = datetime.now()
                
                result = await self.controller.process_with_adaptive_retrieval(query)
                
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                if result.get('success'):
                    print(f"  ✅ 处理成功")
                    print(f"  执行时间: {execution_time:.2f}秒")
                    
                    retrieval_info = result.get('retrieval_info', {})
                    if retrieval_info:
                        print(f"  使用策略: {retrieval_info.get('strategy_used', 'unknown')}")
                        if 'complexity_analysis' in retrieval_info:
                            analysis = retrieval_info['complexity_analysis']
                            print(f"  复杂度: {analysis.get('complexity', 'unknown')} ({analysis.get('score', 0):.2f})")
                    
                    answer = result.get('answer', '')
                    print(f"  答案长度: {len(answer)} 字符")
                    print(f"  答案预览: {answer[:100]}..." if len(answer) > 100 else f"  答案: {answer}")
                    
                    self.test_results.append({
                        'test': f'adaptive_retrieval_{i}',
                        'status': 'PASS',
                        'query': query,
                        'execution_time': execution_time,
                        'strategy': retrieval_info.get('strategy_used'),
                        'answer_length': len(answer)
                    })
                else:
                    print(f"  ❌ 处理失败: {result.get('error', '未知错误')}")
                    self.test_results.append({
                        'test': f'adaptive_retrieval_{i}',
                        'status': 'FAIL',
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                print(f"  💥 测试异常: {str(e)}")
                self.test_results.append({
                    'test': f'adaptive_retrieval_{i}',
                    'status': 'ERROR',
                    'error': str(e)
                })
    
    def test_performance_report(self):
        """测试性能报告功能"""
        print("\n=== 测试性能报告功能 ===")
        
        try:
            result = self.controller.get_adaptive_performance_report()
            if result.get('success'):
                report = result['report']
                print("  ✅ 性能报告获取成功")
                print(f"  总查询数: {report.get('total_queries', 0)}")
                print(f"  平均响应时间: {report.get('avg_response_time', 0):.2f}秒")
                print(f"  策略使用统计: {report.get('strategy_usage', {})}")
                
                self.test_results.append({
                    'test': 'performance_report',
                    'status': 'PASS',
                    'total_queries': report.get('total_queries', 0),
                    'avg_response_time': report.get('avg_response_time', 0)
                })
            else:
                print(f"  ❌ 性能报告获取失败: {result.get('error', '未知错误')}")
                self.test_results.append({
                    'test': 'performance_report',
                    'status': 'FAIL',
                    'error': result.get('error')
                })
        except Exception as e:
            print(f"  💥 测试异常: {str(e)}")
            self.test_results.append({
                'test': 'performance_report',
                'status': 'ERROR',
                'error': str(e)
            })
    
    def test_system_info(self):
        """测试系统信息功能"""
        print("\n=== 测试系统信息功能 ===")
        
        try:
            system_info = self.controller.get_system_info()
            print("  ✅ 系统信息获取成功")
            print(f"  控制器状态: {system_info.get('controller_status', 'unknown')}")
            print(f"  自适应检索: {'启用' if system_info.get('adaptive_enabled') else '禁用'}")
            print(f"  重排序器: {'启用' if system_info.get('reranker_enabled') else '禁用'}")
            print(f"  可用功能: {len(system_info.get('available_functions', []))}个")
            print(f"  支持特性: {len(system_info.get('supported_features', []))}个")
            
            self.test_results.append({
                'test': 'system_info',
                'status': 'PASS',
                'adaptive_enabled': system_info.get('adaptive_enabled'),
                'reranker_enabled': system_info.get('reranker_enabled'),
                'function_count': len(system_info.get('available_functions', [])),
                'feature_count': len(system_info.get('supported_features', []))
            })
        except Exception as e:
            print(f"  💥 测试异常: {str(e)}")
            self.test_results.append({
                'test': 'system_info',
                'status': 'ERROR',
                'error': str(e)
            })
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("🧪 自适应检索功能测试报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        print(f"\n📊 测试统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过: {passed_tests} ✅")
        print(f"  失败: {failed_tests} ❌")
        print(f"  错误: {error_tests} 💥")
        print(f"  成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "  成功率: 0%")
        
        print(f"\n📋 详细结果:")
        for result in self.test_results:
            status_icon = {'PASS': '✅', 'FAIL': '❌', 'ERROR': '💥'}[result['status']]
            print(f"  {status_icon} {result['test']}: {result['status']}")
            if result['status'] != 'PASS' and 'error' in result:
                print(f"    错误: {result['error']}")
        
        print(f"\n🎯 测试结论:")
        if passed_tests == total_tests:
            print("  🎉 所有测试通过！自适应检索功能运行正常。")
        elif passed_tests > total_tests * 0.8:
            print("  ⚠️ 大部分测试通过，但存在一些问题需要关注。")
        else:
            print("  🚨 多个测试失败，需要检查系统配置和依赖。")
        
        print("\n" + "="*60)

async def main():
    """主测试函数"""
    print("🔍 自适应检索功能测试开始")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = AdaptiveRetrievalTester()
    
    # 设置测试环境
    if not tester.setup():
        print("❌ 测试环境初始化失败，退出测试")
        return
    
    # 执行各项测试
    tester.test_system_info()
    tester.test_complexity_analysis()
    await tester.test_adaptive_retrieval()
    tester.test_performance_report()
    
    # 生成测试报告
    tester.generate_report()

if __name__ == "__main__":
    asyncio.run(main())