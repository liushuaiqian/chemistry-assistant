#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Metaso知识库API测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_knowledge_api_only():
    """只测试KnowledgeAPI，不依赖其他模块"""
    print("\n=== 测试KnowledgeAPI独立功能 ===")
    
    try:
        # 直接导入KnowledgeAPI
        from tools.knowledge_api import KnowledgeAPI
        
        # 初始化知识库API
        print("初始化KnowledgeAPI...")
        knowledge_api = KnowledgeAPI()
        print("✅ KnowledgeAPI初始化成功")
        
        # 测试1: Metaso知识库搜索
        print("\n--- 测试1: Metaso知识库搜索 ---")
        query1 = "请总结知识库中关于甲烷的主要内容"
        print(f"查询: {query1}")
        
        result1 = knowledge_api.search_knowledge_base(query1)
        
        if result1.get('success'):
            print("\n✅ Metaso知识库搜索成功!")
            print(f"答案长度: {len(result1.get('answer', ''))}")
            print(f"参考文献数量: {len(result1.get('references', []))}")
            print(f"结果ID: {result1.get('result_id', '')}")
            print(f"会话ID: {result1.get('session_id', '')}")
            print(f"余额: {result1.get('balance', 0)}")
            
            # 显示答案前300字符
            answer = result1.get('answer', '')
            if answer:
                print(f"\n答案预览:\n{answer[:300]}...")
            
            # 显示参考文献
            references = result1.get('references', [])
            if references:
                print(f"\n参考文献:")
                for i, ref in enumerate(references[:2], 1):
                    print(f"  {i}. {ref.get('title', '未知标题')} (第{ref.get('page', 'N/A')}页/{ref.get('total_page', 'N/A')}页)")
                    print(f"     类型: {ref.get('article_type', 'N/A')}")
        else:
            print(f"❌ Metaso知识库搜索失败: {result1.get('error', '未知错误')}")
        
        # 测试2: 不同查询
        print("\n--- 测试2: 不同化学主题查询 ---")
        query2 = "乙醇的化学性质和应用"
        print(f"查询: {query2}")
        
        result2 = knowledge_api.search_knowledge_base(query2)
        
        if result2.get('success'):
            print("\n✅ 第二次搜索成功!")
            print(f"答案长度: {len(result2.get('answer', ''))}")
            print(f"参考文献数量: {len(result2.get('references', []))}")
            
            # 显示答案前200字符
            answer2 = result2.get('answer', '')
            if answer2:
                print(f"\n答案预览:\n{answer2[:200]}...")
        else:
            print(f"❌ 第二次搜索失败: {result2.get('error', '未知错误')}")
        
        # 测试3: PubChem化合物查询
        print("\n--- 测试3: PubChem化合物查询 ---")
        compound = "methane"
        print(f"查询化合物: {compound}")
        
        pubchem_result = knowledge_api.get_compound_info(compound)
        
        if 'error' not in pubchem_result:
            print("\n✅ PubChem查询成功!")
            print(f"化合物名称: {pubchem_result.get('name', 'N/A')}")
            print(f"分子式: {pubchem_result.get('molecular_formula', 'N/A')}")
            print(f"分子量: {pubchem_result.get('molecular_weight', 'N/A')}")
            print(f"SMILES: {pubchem_result.get('smiles', 'N/A')}")
        else:
            print(f"❌ PubChem查询失败: {pubchem_result.get('error', '未知错误')}")
        
        # 测试4: 综合信息获取
        print("\n--- 测试4: 综合信息获取 ---")
        query3 = "甲烷"
        print(f"综合查询: {query3}")
        
        comprehensive_result = knowledge_api.get_comprehensive_info(query3)
        
        print(f"\n综合答案长度: {len(comprehensive_result.get('combined_answer', ''))}")
        
        # 检查Metaso结果
        metaso_result = comprehensive_result.get('metaso_result')
        if metaso_result and metaso_result.get('success'):
            print("✅ Metaso知识库部分成功")
        else:
            print("❌ Metaso知识库部分失败")
        
        # 检查PubChem结果
        pubchem_result = comprehensive_result.get('pubchem_result')
        if pubchem_result and 'error' not in pubchem_result:
            print("✅ PubChem部分成功")
        else:
            print("❌ PubChem部分失败")
        
        # 显示综合答案预览
        combined_answer = comprehensive_result.get('combined_answer', '')
        if combined_answer:
            print(f"\n综合答案预览:\n{combined_answer[:400]}...")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("开始测试Metaso知识库API集成 (简化版)...")
    
    test_knowledge_api_only()
    
    print("\n=== 测试完成 ===")
    print("\n如果所有测试通过，说明Metaso知识库API已成功集成到项目中!")

if __name__ == "__main__":
    main()