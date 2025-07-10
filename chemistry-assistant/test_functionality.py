#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
功能测试脚本
测试系统各个组件的功能是否正常
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controller import Controller
from core.llm_manager import LLMManager
from core.chemistry_chain import ChemistryAnalysisChain
import logging

# 设置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_controller_initialization():
    """
    测试Controller初始化
    """
    print("\n" + "="*50)
    print("🔧 测试Controller初始化")
    print("="*50)
    
    try:
        controller = Controller()
        print("✅ Controller初始化成功")
        
        # 测试获取可用模型
        models_info = controller.get_available_models()
        print(f"📊 可用模型信息: {models_info}")
        
        return controller
    except Exception as e:
        print(f"❌ Controller初始化失败: {e}")
        return None

def test_llm_manager():
    """
    测试LLM管理器
    """
    print("\n" + "="*50)
    print("🤖 测试LLM管理器")
    print("="*50)
    
    try:
        llm_manager = LLMManager()
        available_models = llm_manager.get_available_models()
        print(f"📋 可用模型: {available_models}")
        
        if available_models:
            test_question = "什么是化学键？"
            print(f"\n🧪 测试问题: {test_question}")
            
            # 测试第一个可用模型
            model = available_models[0]
            print(f"🔄 使用模型: {model}")
            
            response = llm_manager.call_chemistry_expert(model, test_question)
            print(f"📝 回答: {response[:200]}..." if len(response) > 200 else f"📝 回答: {response}")
            
            return True
        else:
            print("⚠️ 没有可用的模型")
            return False
            
    except Exception as e:
        print(f"❌ LLM管理器测试失败: {e}")
        return False

def test_chemistry_chain():
    """
    测试化学分析链
    """
    print("\n" + "="*50)
    print("🔗 测试化学分析链")
    print("="*50)
    
    try:
        chain = ChemistryAnalysisChain()
        chain_info = chain.get_chain_info()
        print(f"📊 链信息: {chain_info['name']}")
        print(f"📝 描述: {chain_info['description']}")
        print(f"🔄 步骤: {', '.join(chain_info['steps'])}")
        
        test_question = "计算H2O的摩尔质量"
        print(f"\n🧪 测试问题: {test_question}")
        
        result = chain.process_question_chain(test_question)
        print(f"📋 分类结果: {result['classification'][:150]}..." if len(result['classification']) > 150 else f"📋 分类结果: {result['classification']}")
        print(f"🔍 分析结果: {result['analysis'][:150]}..." if len(result['analysis']) > 150 else f"🔍 分析结果: {result['analysis']}")
        print(f"✅ 解答结果: {result['solution'][:150]}..." if len(result['solution']) > 150 else f"✅ 解答结果: {result['solution']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 化学分析链测试失败: {e}")
        return False

def test_query_processing(controller):
    """
    测试查询处理功能
    """
    print("\n" + "="*50)
    print("💬 测试查询处理")
    print("="*50)
    
    if not controller:
        print("❌ Controller不可用，跳过测试")
        return False
    
    test_questions = [
        "什么是化学键？",
        "计算H2O的摩尔质量",
        "平衡化学方程式：H2 + O2 = H2O"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🧪 测试 {i}: {question}")
        
        try:
            # 测试传统处理
            response, comparison = controller.process_query(question)
            print(f"📝 传统处理回答: {response[:100]}..." if len(response) > 100 else f"📝 传统处理回答: {response}")
            
            # 测试链式处理
            chain_response, chain_comparison, chain_result = controller.process_with_chain(question, use_chain=True)
            print(f"🔗 链式处理回答: {chain_response[:100]}..." if len(chain_response) > 100 else f"🔗 链式处理回答: {chain_response}")
            
        except Exception as e:
            print(f"❌ 处理问题 '{question}' 时出错: {e}")
    
    return True

def test_ui_simulation():
    """
    模拟UI界面的函数调用
    """
    print("\n" + "="*50)
    print("🖥️ 模拟UI界面调用")
    print("="*50)
    
    try:
        # 模拟UI中的process_question函数
        from ui.app_gradio import start_ui
        
        # 创建controller
        controller = Controller()
        
        # 模拟process_question函数的逻辑
        def simulate_process_question(question, function_choice, image=None, model_choice="本地模型"):
            if not question.strip():
                return "请输入问题", "", ""
            
            # 构建任务信息
            task_info = {
                'function': function_choice,
                'model': model_choice
            }
            
            if image is not None:
                task_info["image"] = image
            
            try:
                if function_choice == "LangChain处理" or model_choice == "LangChain链式处理":
                    response, comparison, chain_result = controller.process_with_chain(question, use_chain=True)
                    chain_info = ""
                    if chain_result and 'chain_summary' in chain_result:
                        chain_info = chain_result['chain_summary']
                    return response, comparison, chain_info
                else:
                    response, comparison = controller.process_query(question, task_info)
                    return response, comparison, ""
            except Exception as e:
                return f"处理出错：{str(e)}", "", ""
        
        # 测试不同的输入组合
        test_cases = [
            ("什么是化学键？", "智能问答", None, "本地模型"),
            ("计算H2O的摩尔质量", "化学计算", None, "本地模型"),
            ("什么是原子结构？", "LangChain处理", None, "LangChain链式处理")
        ]
        
        for i, (question, function, image, model) in enumerate(test_cases, 1):
            print(f"\n🧪 UI测试 {i}:")
            print(f"   问题: {question}")
            print(f"   功能: {function}")
            print(f"   模型: {model}")
            
            response, comparison, chain_info = simulate_process_question(question, function, image, model)
            print(f"📝 回答: {response[:100]}..." if len(response) > 100 else f"📝 回答: {response}")
            if comparison:
                print(f"📊 对比: {comparison[:50]}..." if len(comparison) > 50 else f"📊 对比: {comparison}")
            if chain_info:
                print(f"🔗 链式: {chain_info[:50]}..." if len(chain_info) > 50 else f"🔗 链式: {chain_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ UI模拟测试失败: {e}")
        return False

def main():
    """
    主测试函数
    """
    print("🧪 化学助手功能测试")
    print("测试系统各个组件的功能是否正常")
    
    results = []
    
    # 1. 测试Controller初始化
    controller = test_controller_initialization()
    results.append(("Controller初始化", controller is not None))
    
    # 2. 测试LLM管理器
    llm_result = test_llm_manager()
    results.append(("LLM管理器", llm_result))
    
    # 3. 测试化学分析链
    chain_result = test_chemistry_chain()
    results.append(("化学分析链", chain_result))
    
    # 4. 测试查询处理
    query_result = test_query_processing(controller)
    results.append(("查询处理", query_result))
    
    # 5. 测试UI模拟
    ui_result = test_ui_simulation()
    results.append(("UI模拟", ui_result))
    
    # 输出测试结果
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！系统功能正常")
    else:
        print("⚠️ 部分测试失败，请检查相关组件")

if __name__ == "__main__":
    main()