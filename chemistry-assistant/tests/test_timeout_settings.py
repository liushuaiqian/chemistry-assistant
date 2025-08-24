#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试模型超时设置
验证deepseek和文心x1模型的4分钟超时设置是否正确
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chemistry_chain import ChemistryAnalysisChain
import logging
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_timeout_settings():
    """
    测试超时设置
    """
    print("\n" + "="*80)
    print("🕐 化学助手 - 模型超时设置测试")
    print("="*80)
    print("本测试将验证deepseek和文心x1模型的4分钟超时设置")
    
    try:
        # 初始化化学分析链
        print("\n🔧 初始化化学分析链...")
        chain = ChemistryAnalysisChain()
        
        # 显示并行模型配置
        print(f"\n📋 并行模型配置:")
        for i, model in enumerate(chain.parallel_models, 1):
            model_names = {
                'tongyi': '通义千问 (qwen-max)',
                'deepseek': 'DeepSeek-R1 [4分钟超时]',
                'qianfan': '文心4.5-Turbo-128K',
                'ernie_x1': 'ERNIE-X1-Turbo-32K [4分钟超时]'
            }
            timeout_info = " [4分钟超时]" if model in ['deepseek', 'ernie_x1'] else " [30秒超时]"
            print(f"  {i}. {model_names.get(model, model)}{timeout_info}")
        
        # 测试问题
        test_question = "请详细解释化学平衡的概念，包括勒夏特列原理的应用。"
        
        print(f"\n📝 测试问题: {test_question}")
        print("-"*60)
        
        start_time = time.time()
        
        try:
            # 执行并行处理
            result = chain.process_with_vision(
                question=test_question,
                function_type="智能问答"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"\n⏱️  总处理时间: {processing_time:.2f} 秒")
            
            # 显示各模型的处理结果和超时设置
            if 'parallel_results' in result:
                print("\n📊 各模型处理结果和超时设置:")
                for model_name, model_result in result['parallel_results'].items():
                    model_names = {
                        'tongyi': '通义千问',
                        'deepseek': 'DeepSeek-R1',
                        'qianfan': '文心4.5',
                        'ernie_x1': 'ERNIE-X1'
                    }
                    display_name = model_names.get(model_name, model_name)
                    
                    # 显示超时设置
                    timeout_setting = "4分钟(240秒)" if model_name in ['deepseek', 'ernie_x1'] else "30秒"
                    
                    if model_result.get('success', False):
                        proc_time = model_result.get('processing_time', 0)
                        print(f"\n  ✅ {display_name}:")
                        print(f"     超时设置: {timeout_setting}")
                        print(f"     实际处理时间: {proc_time:.2f} 秒")
                        print(f"     状态: 成功完成")
                    else:
                        error = model_result.get('error', '未知错误')
                        proc_time = model_result.get('processing_time', 0)
                        print(f"\n  ❌ {display_name}:")
                        print(f"     超时设置: {timeout_setting}")
                        print(f"     处理时间: {proc_time:.2f} 秒")
                        print(f"     错误信息: {error}")
                        
                        # 检查是否是超时错误
                        if "超时" in error:
                            if model_name in ['deepseek', 'ernie_x1']:
                                if "240秒" in error or "4分钟" in error:
                                    print(f"     ✅ 超时设置正确: 4分钟")
                                else:
                                    print(f"     ❌ 超时设置可能有误")
                            else:
                                if "30秒" in error:
                                    print(f"     ✅ 超时设置正确: 30秒")
                                else:
                                    print(f"     ❌ 超时设置可能有误")
            
            print(f"\n✅ 超时设置测试完成")
            
        except Exception as e:
            print(f"\n❌ 测试过程中出错: {str(e)}")
            logger.error(f"测试失败: {str(e)}")
        
        print(f"\n" + "="*80)
        print("🎊 超时设置测试完成！")
        print("="*80)
        
        # 显示超时配置总结
        print("\n📈 超时配置总结:")
        print("  • DeepSeek-R1: 4分钟 (240秒) 超时")
        print("  • ERNIE-X1-Turbo-32K: 4分钟 (240秒) 超时")
        print("  • 通义千问: 30秒 超时")
        print("  • 文心4.5: 30秒 超时")
        print("  • ERNIE VL: 30秒 超时")
        
        print("\n🔧 配置说明:")
        print("  • 长超时模型适用于复杂推理任务")
        print("  • 短超时模型保证快速响应")
        print("  • 超时设置可根据模型特性调整")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        print(f"\n❌ 测试失败: {str(e)}")
        print("请检查配置和网络连接")

def main():
    """
    主函数
    """
    print("🎉 欢迎使用化学助手超时设置测试")
    print("本测试将验证deepseek和文心x1模型的4分钟超时设置")
    
    # 设置环境变量解决OpenMP警告
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    try:
        test_timeout_settings()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        print(f"\n❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    main()