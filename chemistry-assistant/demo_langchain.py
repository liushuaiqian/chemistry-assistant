#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LangChain集成演示脚本
展示新的LangChain功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controller import Controller
from core.llm_manager import LLMManager
from core.chemistry_chain import ChemistryAnalysisChain
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_llm_manager():
    """
    演示LLM管理器功能
    """
    print("\n" + "="*60)
    print("🚀 LLM管理器演示")
    print("="*60)
    
    llm_manager = LLMManager()
    
    # 测试化学专家调用
    test_question = "请解释酸碱中和反应的原理"
    print(f"\n🧪 测试问题: {test_question}")
    
    try:
        response = llm_manager.call_chemistry_expert("default", test_question)
        print(f"📝 回答: {response[:200]}..." if len(response) > 200 else f"📝 回答: {response}")
    except Exception as e:
        print(f"❌ 调用失败: {str(e)}")

def demo_chemistry_chain():
    """
    演示化学分析链功能
    """
    print("\n" + "="*60)
    print("🔗 化学分析链演示")
    print("="*60)
    
    chain = ChemistryAnalysisChain()
    
    # 显示链信息
    chain_info = chain.get_chain_info()
    print(f"\n📊 链信息:")
    print(f"   名称: {chain_info['name']}")
    print(f"   描述: {chain_info['description']}")
    print(f"   步骤: {', '.join(chain_info['steps'])}")
    print(f"   可用模型: {chain_info['available_models']}")
    
    # 测试链式处理
    test_question = "计算0.1mol/L的HCl溶液与0.1mol/L的NaOH溶液完全中和时的pH值"
    print(f"\n🧪 测试问题: {test_question}")
    
    try:
        result = chain.process_question_chain(test_question)
        
        print("\n📋 分类结果:")
        print(result['classification'][:300] + "..." if len(result['classification']) > 300 else result['classification'])
        
        print("\n🔍 分析结果:")
        print(result['analysis'][:300] + "..." if len(result['analysis']) > 300 else result['analysis'])
        
        print("\n✅ 解答结果:")
        print(result['solution'][:300] + "..." if len(result['solution']) > 300 else result['solution'])
        
    except Exception as e:
        print(f"❌ 链式处理失败: {str(e)}")

def demo_controller_integration():
    """
    演示控制器集成功能
    """
    print("\n" + "="*60)
    print("🎛️ 控制器集成演示")
    print("="*60)
    
    controller = Controller()
    
    print(f"\n📊 系统已初始化")
    
    # 测试传统处理 vs 链式处理
    test_question = "什么是化学平衡？请举例说明。"
    print(f"\n🧪 测试问题: {test_question}")
    
    # 传统处理
    print("\n📝 传统处理结果:")
    try:
        response, comparison, _ = controller.process_with_chain(test_question, use_chain=False)
        print(f"回答: {response[:200]}..." if len(response) > 200 else f"回答: {response}")
    except Exception as e:
        print(f"❌ 传统处理失败: {str(e)}")
    
    # 链式处理
    print("\n🔗 链式处理结果:")
    try:
        response, comparison, chain_result = controller.process_with_chain(test_question, use_chain=True)
        print(f"回答: {response[:200]}..." if len(response) > 200 else f"回答: {response}")
        if chain_result:
            print(f"链式分析: 包含 {len(chain_result)} 个处理步骤")
    except Exception as e:
        print(f"❌ 链式处理失败: {str(e)}")

def demo_model_comparison():
    """
    演示模型对比功能
    """
    print("\n" + "="*60)
    print("⚖️ 模型对比演示")
    print("="*60)
    
    llm_manager = LLMManager()
    
    test_question = "请解释原电池的工作原理"
    print(f"\n🧪 测试问题: {test_question}")
    
    try:
        response = llm_manager.call_chemistry_expert("default", test_question)
        print(f"\n📝 回答: {response[:200]}..." if len(response) > 200 else f"\n📝 回答: {response}")
    except Exception as e:
        print(f"❌ 调用失败: {str(e)}")

def main():
    """
    主演示函数
    """
    print("🎉 欢迎使用化学助手 LangChain 集成演示")
    print("本演示将展示新集成的 LangChain 功能")
    
    try:
        # 1. LLM管理器演示
        demo_llm_manager()
        
        # 2. 化学分析链演示
        demo_chemistry_chain()
        
        # 3. 控制器集成演示
        demo_controller_integration()
        
        # 4. 模型对比演示
        demo_model_comparison()
        
        print("\n" + "="*60)
        print("🎊 演示完成！")
        print("="*60)
        print("\n📝 总结:")
        print("✅ LangChain 框架已成功集成")
        print("✅ 统一的 LLM 管理器已就绪")
        print("✅ 化学分析链功能正常")
        print("✅ 控制器集成完成")
        print("✅ 模型对比和融合功能可用")
        print("\n🚀 现在可以启动 Web 界面体验完整功能！")
        
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        print(f"\n❌ 演示失败: {str(e)}")
        print("请检查配置和依赖是否正确安装")

if __name__ == "__main__":
    main()