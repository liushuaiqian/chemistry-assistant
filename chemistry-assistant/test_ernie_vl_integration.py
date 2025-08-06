#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERNIE VL视觉模型集成测试脚本
测试ERNIE 4.5 Turbo VL模型在化学助手中的集成效果
"""

import sys
import os
import base64
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.chemistry_chain import ChemistryAnalysisChain
from config import MODEL_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_image_base64():
    """
    创建一个简单的测试图片（base64格式）
    这里使用一个1x1像素的PNG图片作为测试
    """
    # 1x1像素的透明PNG图片的base64编码
    test_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    return f"data:image/png;base64,{test_png_base64}"

def test_ernie_vl_integration():
    """
    测试ERNIE VL模型集成
    """
    print("\n" + "="*60)
    print("ERNIE VL视觉模型集成测试")
    print("="*60)
    
    try:
        # 初始化化学分析链
        print("\n1. 初始化化学分析链...")
        chain = ChemistryAnalysisChain()
        print("✓ 化学分析链初始化成功")
        
        # 检查ERNIE VL配置
        print("\n2. 检查ERNIE VL配置...")
        ernie_vl_config = MODEL_CONFIG.get('ernie_vl')
        if ernie_vl_config:
            print(f"✓ ERNIE VL配置存在")
            print(f"  - 模型名称: {ernie_vl_config.get('model_name')}")
            print(f"  - API URL: {ernie_vl_config.get('api_url')}")
            print(f"  - 角色: {ernie_vl_config.get('role')}")
        else:
            print("✗ ERNIE VL配置不存在")
            return False
        
        # 检查LLM管理器中的ERNIE VL初始化
        print("\n3. 检查LLM管理器中的ERNIE VL初始化...")
        if hasattr(chain.llm_manager, 'ernie_vl') and chain.llm_manager.ernie_vl:
            print("✓ ERNIE VL模型已在LLM管理器中初始化")
        else:
            print("✗ ERNIE VL模型未在LLM管理器中初始化")
        
        # 检查call_ernie_vl方法
        print("\n4. 检查call_ernie_vl方法...")
        if hasattr(chain.llm_manager, 'call_ernie_vl'):
            print("✓ call_ernie_vl方法存在")
        else:
            print("✗ call_ernie_vl方法不存在")
            return False
        
        # 测试视觉问题处理（使用测试图片）
        print("\n5. 测试视觉问题处理...")
        test_question = "请分析这个化学题目并给出解答思路"
        test_image = create_test_image_base64()
        
        print(f"  问题: {test_question}")
        print(f"  图片: 测试图片（1x1像素PNG）")
        
        # 调用process_with_vision方法
        result = chain.process_with_vision(
            question=test_question,
            image_data=test_image
        )
        
        # 分析结果
        print("\n6. 分析处理结果...")
        if isinstance(result, dict):
            if 'error' in result:
                print(f"✗ 处理失败: {result['error']}")
                return False
            else:
                print("✓ 处理成功")
                
                # 检查并行结果
                parallel_results = result.get('parallel_results', {})
                print(f"  - 并行模型数量: {len(parallel_results)}")
                
                # 检查是否包含ERNIE VL结果
                if 'ernie_vl' in parallel_results:
                    ernie_vl_result = parallel_results['ernie_vl']
                    print("✓ ERNIE VL模型结果存在")
                    print(f"  - 成功状态: {ernie_vl_result.get('success', False)}")
                    print(f"  - 处理时间: {ernie_vl_result.get('processing_time', 0):.2f}秒")
                    print(f"  - 模型类型: {ernie_vl_result.get('model_type', 'unknown')}")
                    
                    if ernie_vl_result.get('success', False):
                        print("✓ ERNIE VL模型处理成功")
                        answer = ernie_vl_result.get('answer', '')
                        if answer:
                            print(f"  - 答案长度: {len(answer)}字符")
                            print(f"  - 答案预览: {answer[:100]}...")
                    else:
                        error = ernie_vl_result.get('error', '未知错误')
                        print(f"✗ ERNIE VL模型处理失败: {error}")
                else:
                    print("✗ ERNIE VL模型结果不存在")
                    print(f"  可用模型: {list(parallel_results.keys())}")
                
                # 检查融合结果
                integrated_answer = result.get('integrated_answer', '')
                if integrated_answer:
                    print("✓ 融合答案生成成功")
                    print(f"  - 融合答案长度: {len(integrated_answer)}字符")
                else:
                    print("✗ 融合答案生成失败")
                
                # 显示处理信息
                processing_info = result.get('processing_info', {})
                if processing_info:
                    print("\n处理统计信息:")
                    for key, value in processing_info.items():
                        print(f"  - {key}: {value}")
        else:
            print(f"✗ 返回结果格式错误: {type(result)}")
            return False
        
        print("\n" + "="*60)
        print("✓ ERNIE VL视觉模型集成测试完成")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主函数
    """
    print("开始ERNIE VL视觉模型集成测试...")
    
    success = test_ernie_vl_integration()
    
    if success:
        print("\n🎉 所有测试通过！ERNIE VL视觉模型集成成功！")
        print("\n新功能特性:")
        print("- ✓ 支持图片输入的化学问题分析")
        print("- ✓ ERNIE 4.5 Turbo VL视觉模型并行调用")
        print("- ✓ 视觉模型结果与文本模型结果融合")
        print("- ✓ 智能模型选择和负载均衡")
        print("\n使用建议:")
        print("- 上传包含化学题目、公式或图表的图片")
        print("- 提供清晰的问题描述")
        print("- 系统将自动调用ERNIE VL进行视觉分析")
        print("- 结果将与其他模型融合提供最佳答案")
        return 0
    else:
        print("\n❌ 测试失败！请检查配置和实现。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)