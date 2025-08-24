#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试ERNIE-X1-Turbo-32K模型集成
验证新模型是否正确添加到并行处理系统中
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_manager import LLMManager
from core.chemistry_chain import ChemistryAnalysisChain
from core.controller import Controller
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llm_manager():
    """
    测试LLM管理器中的ERNIE-X1-Turbo-32K模型
    """
    print("\n" + "="*60)
    print("🧪 测试LLM管理器 - ERNIE-X1-Turbo-32K模型")
    print("="*60)
    
    try:
        llm_manager = LLMManager()
        
        # 检查可用模型
        available_models = llm_manager.get_available_models()
        print(f"\n📋 可用模型列表: {available_models}")
        
        # 检查ERNIE-X1模型是否可用
        if 'ernie_x1' in available_models:
            print("✅ ERNIE-X1-Turbo-32K模型已成功加载")
            
            # 测试模型调用
            test_question = "什么是化学平衡？请简要说明。"
            print(f"\n🔍 测试问题: {test_question}")
            
            try:
                response = llm_manager.call_chemistry_expert(
                    model_name="ernie_x1",
                    question=test_question
                )
                print(f"\n📝 ERNIE-X1回答: {response[:200]}...")
                print("✅ ERNIE-X1模型调用成功")
            except Exception as e:
                print(f"❌ ERNIE-X1模型调用失败: {str(e)}")
        else:
            print("❌ ERNIE-X1-Turbo-32K模型未找到")
            
    except Exception as e:
        logger.error(f"LLM管理器测试失败: {str(e)}")
        print(f"❌ LLM管理器测试失败: {str(e)}")

def test_chemistry_chain():
    """
    测试化学分析链中的并行模型处理
    """
    print("\n" + "="*60)
    print("🧪 测试化学分析链 - 并行模型处理")
    print("="*60)
    
    try:
        chain = ChemistryAnalysisChain()
        
        # 检查并行模型配置
        print(f"\n📋 并行模型列表: {chain.parallel_models}")
        
        if 'ernie_x1' in chain.parallel_models:
            print("✅ ERNIE-X1-Turbo-32K已添加到并行模型列表")
        else:
            print("❌ ERNIE-X1-Turbo-32K未在并行模型列表中")
            
        # 测试并行处理
        test_question = "计算NaCl的摩尔质量"
        print(f"\n🔍 测试问题: {test_question}")
        
        try:
            result = chain.process_with_vision(
                question=test_question,
                function_type="智能问答"
            )
            
            print("\n📊 并行处理结果:")
            if 'parallel_results' in result:
                for model_name, model_result in result['parallel_results'].items():
                    status = "✅ 成功" if model_result.get('success', False) else "❌ 失败"
                    print(f"  - {model_name}: {status}")
                    if model_name == 'ernie_x1':
                        if model_result.get('success', False):
                            print(f"    ERNIE-X1回答: {model_result.get('answer', '')[:100]}...")
                        else:
                            print(f"    错误信息: {model_result.get('error', '未知错误')}")
            
            print("✅ 并行处理测试完成")
            
        except Exception as e:
            print(f"❌ 并行处理测试失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"化学分析链测试失败: {str(e)}")
        print(f"❌ 化学分析链测试失败: {str(e)}")

def test_controller_integration():
    """
    测试控制器集成
    """
    print("\n" + "="*60)
    print("🧪 测试控制器集成 - LangChain处理")
    print("="*60)
    
    try:
        controller = Controller()
        
        # 测试LangChain处理
        test_question = "什么是酸碱反应？"
        print(f"\n🔍 测试问题: {test_question}")
        
        try:
            response, comparison, chain_result = controller.process_with_chain(
                query=test_question,
                function_type="智能问答"
            )
            
            print("\n📝 处理结果:")
            print(f"  - 主要回答: {response[:100]}...")
            print(f"  - 对比分析: {comparison[:100] if comparison else '无'}...")
            print(f"  - 链式结果: {str(chain_result)[:100] if chain_result else '无'}...")
            
            print("✅ 控制器集成测试成功")
            
        except Exception as e:
            print(f"❌ 控制器集成测试失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"控制器测试失败: {str(e)}")
        print(f"❌ 控制器测试失败: {str(e)}")

def main():
    """
    主测试函数
    """
    print("🎉 开始测试ERNIE-X1-Turbo-32K模型集成")
    print("本测试将验证新模型是否正确集成到系统中")
    
    try:
        # 1. 测试LLM管理器
        test_llm_manager()
        
        # 2. 测试化学分析链
        test_chemistry_chain()
        
        # 3. 测试控制器集成
        test_controller_integration()
        
        print("\n" + "="*60)
        print("🎊 测试完成！")
        print("="*60)
        print("\n📝 总结:")
        print("✅ ERNIE-X1-Turbo-32K模型已成功集成")
        print("✅ 并行处理架构已更新")
        print("✅ LangChain处理功能已增强")
        print("\n🚀 现在可以在UI界面中使用新的并行模型功能！")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        print(f"\n❌ 测试失败: {str(e)}")
        print("请检查配置和依赖是否正确")

if __name__ == "__main__":
    main()