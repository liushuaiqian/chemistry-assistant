#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
并行模型演示脚本
展示包含ERNIE-X1-Turbo-32K在内的多模型并行处理功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.chemistry_chain import ChemistryAnalysisChain
import logging
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_parallel_processing():
    """
    演示并行模型处理功能
    """
    print("\n" + "="*80)
    print("🚀 化学助手 - 并行模型处理演示")
    print("="*80)
    print("本演示将展示包含ERNIE-X1-Turbo-32K在内的多模型并行处理能力")
    
    try:
        # 初始化化学分析链
        print("\n🔧 初始化化学分析链...")
        chain = ChemistryAnalysisChain()
        
        # 显示并行模型配置
        print(f"\n📋 并行模型配置:")
        for i, model in enumerate(chain.parallel_models, 1):
            model_names = {
                'tongyi': '通义千问 (qwen-max)',
                'deepseek': 'DeepSeek-R1',
                'qianfan': '文心4.5-Turbo-128K',
                'ernie_x1': 'ERNIE-X1-Turbo-32K'
            }
            print(f"  {i}. {model_names.get(model, model)}")
        
        print(f"\n⚡ 线程池配置: {chain.executor._max_workers} 个工作线程")
        
        # 测试问题列表
        test_questions = [
            "什么是化学平衡？请简要说明其特点。",
            "计算NaCl的摩尔质量，并说明计算过程。",
            "解释酸碱反应的本质，并举例说明。"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n" + "-"*60)
            print(f"📝 测试问题 {i}: {question}")
            print("-"*60)
            
            start_time = time.time()
            
            try:
                # 执行并行处理
                result = chain.process_with_vision(
                    question=question,
                    function_type="智能问答"
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"\n⏱️  总处理时间: {processing_time:.2f} 秒")
                
                # 显示各模型的处理结果
                if 'parallel_results' in result:
                    print("\n📊 各模型处理结果:")
                    for model_name, model_result in result['parallel_results'].items():
                        model_names = {
                            'tongyi': '通义千问',
                            'deepseek': 'DeepSeek-R1',
                            'qianfan': '文心4.5',
                            'ernie_x1': 'ERNIE-X1'
                        }
                        display_name = model_names.get(model_name, model_name)
                        
                        if model_result.get('success', False):
                            answer = model_result.get('answer', '')
                            proc_time = model_result.get('processing_time', 0)
                            print(f"\n  ✅ {display_name}:")
                            print(f"     处理时间: {proc_time:.2f} 秒")
                            print(f"     回答预览: {answer[:100]}...")
                        else:
                            error = model_result.get('error', '未知错误')
                            print(f"\n  ❌ {display_name}: {error}")
                
                # 显示整合结果
                if 'integrated_answer' in result:
                    print(f"\n🎯 整合答案预览:")
                    integrated = result['integrated_answer']
                    print(f"   {integrated[:200]}...")
                
                print(f"\n✅ 问题 {i} 处理完成")
                
            except Exception as e:
                print(f"\n❌ 问题 {i} 处理失败: {str(e)}")
                logger.error(f"问题处理失败: {str(e)}")
        
        print(f"\n" + "="*80)
        print("🎊 并行模型演示完成！")
        print("="*80)
        
        # 显示性能统计
        print("\n📈 性能特点:")
        print("  • 多模型并行处理，提高答案质量")
        print("  • 智能结果整合，综合各模型优势")
        print("  • 容错机制，单个模型失败不影响整体")
        print("  • 新增ERNIE-X1-Turbo-32K，增强处理能力")
        
        print("\n🚀 使用建议:")
        print("  • 在UI界面选择'LangChain处理'功能")
        print("  • 适用于需要深度分析的复杂化学问题")
        print("  • 可获得多角度、高质量的综合答案")
        
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        print(f"\n❌ 演示失败: {str(e)}")
        print("请检查配置和网络连接")

def main():
    """
    主函数
    """
    print("🎉 欢迎使用化学助手并行模型演示")
    print("本演示将展示新集成的ERNIE-X1-Turbo-32K模型的并行处理能力")
    
    # 设置环境变量解决OpenMP警告
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    try:
        demo_parallel_processing()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        print(f"\n❌ 演示失败: {str(e)}")

if __name__ == "__main__":
    main()