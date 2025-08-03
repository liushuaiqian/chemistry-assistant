#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Metaso知识库API集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controller import Controller
from tools.knowledge_api import KnowledgeAPI
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_knowledge_api_direct():
    """直接测试KnowledgeAPI"""
    print("\n=== 测试KnowledgeAPI直接调用 ===")
    
    try:
        # 初始化知识库API
        knowledge_api = KnowledgeAPI()
        
        # 测试Metaso知识库搜索
        query = "请总结知识库中关于甲烷的主要内容"
        print(f"\n查询: {query}")
        
        result = knowledge_api.search_knowledge_base(query)
        
        if result.get('success'):
            print("\n✅ Metaso知识库搜索成功!")
            print(f"答案长度: {len(result.get('answer', ''))}")
            print(f"参考文献数量: {len(result.get('references', []))}")
            print(f"结果ID: {result.get('result_id', '')}")
            print(f"会话ID: {result.get('session_id', '')}")
            print(f"余额: {result.get('balance', 0)}")
            
            # 显示答案前500字符
            answer = result.get('answer', '')
            if answer:
                print(f"\n答案预览: {answer[:500]}...")
            
            # 显示参考文献
            references = result.get('references', [])
            if references:
                print(f"\n参考文献:")
                for i, ref in enumerate(references[:3], 1):
                    print(f"  {i}. {ref.get('title', '未知标题')} (第{ref.get('page', 'N/A')}页)")
        else:
            print(f"❌ Metaso知识库搜索失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 直接测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

def test_comprehensive_knowledge():
    """测试综合知识获取"""
    print("\n=== 测试综合知识获取 ===")
    
    try:
        knowledge_api = KnowledgeAPI()
        
        # 测试化合物查询
        query = "甲烷"
        print(f"\n查询化合物: {query}")
        
        result = knowledge_api.get_comprehensive_info(query)
        
        print(f"\n综合答案长度: {len(result.get('combined_answer', ''))}")
        
        # 显示Metaso结果
        metaso_result = result.get('metaso_result')
        if metaso_result and metaso_result.get('success'):
            print("\n✅ Metaso知识库结果获取成功")
            print(f"  答案长度: {len(metaso_result.get('answer', ''))}")
            print(f"  参考文献: {len(metaso_result.get('references', []))}个")
        
        # 显示PubChem结果
        pubchem_result = result.get('pubchem_result')
        if pubchem_result and 'error' not in pubchem_result:
            print("\n✅ PubChem数据库结果获取成功")
            print(f"  化合物名称: {pubchem_result.get('name', 'N/A')}")
            print(f"  分子式: {pubchem_result.get('molecular_formula', 'N/A')}")
            print(f"  分子量: {pubchem_result.get('molecular_weight', 'N/A')}")
        
        # 显示综合答案预览
        combined_answer = result.get('combined_answer', '')
        if combined_answer:
            print(f"\n综合答案预览: {combined_answer[:300]}...")
            
    except Exception as e:
        print(f"❌ 综合知识测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

def test_controller_integration():
    """测试控制器集成"""
    print("\n=== 测试控制器集成 ===")
    
    try:
        # 初始化控制器
        print("初始化控制器...")
        controller = Controller()
        
        # 测试外部知识库搜索
        query = "请介绍一下乙醇的性质和用途"
        print(f"\n测试查询: {query}")
        
        result = controller.search_external_knowledge(query)
        
        if result.get('success'):
            print("\n✅ 控制器外部知识库搜索成功!")
            print(f"来源: {result.get('source', '')}")
            print(f"答案长度: {len(result.get('answer', ''))}")
            print(f"参考文献数量: {len(result.get('references', []))}")
            
            # 显示答案预览
            answer = result.get('answer', '')
            if answer:
                print(f"\n答案预览: {answer[:400]}...")
        else:
            print(f"❌ 控制器搜索失败: {result.get('error', '未知错误')}")
        
        # 测试综合知识获取
        print("\n--- 测试综合知识获取 ---")
        comp_result = controller.get_comprehensive_knowledge("乙醇")
        
        if comp_result.get('success'):
            print("\n✅ 控制器综合知识获取成功!")
            print(f"知识源数量: {len(comp_result.get('sources', []))}")
            
            for i, source in enumerate(comp_result.get('sources', []), 1):
                print(f"  {i}. {source.get('name', '未知来源')}")
        else:
            print(f"❌ 综合知识获取失败: {comp_result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 控制器集成测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("开始测试Metaso知识库API集成...")
    
    # 测试1: 直接测试KnowledgeAPI
    test_knowledge_api_direct()
    
    # 测试2: 测试综合知识获取
    test_comprehensive_knowledge()
    
    # 测试3: 测试控制器集成
    test_controller_integration()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()