#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试通义百炼知识检索智能体集成
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.knowledge_api import KnowledgeAPI
from tools.rag_retriever import RAGRetriever

def test_knowledge_api():
    """
    测试KnowledgeAPI中的通义百炼功能
    """
    print("=== 测试KnowledgeAPI ===\n")
    
    # 初始化KnowledgeAPI
    knowledge_api = KnowledgeAPI()
    
    # 测试配置状态
    print("1. 检查配置状态:")
    print(f"   通义百炼API Key: {'已配置' if knowledge_api.tongyi_api_key else '未配置'}")
    print(f"   通义百炼App ID: {'已配置' if knowledge_api.tongyi_app_id else '未配置'}")
    print(f"   知识库ID数量: {len(knowledge_api.tongyi_pipeline_ids) if knowledge_api.tongyi_pipeline_ids else 0}")
    print(f"   DashScope可用性: {'可用' if hasattr(knowledge_api, 'DASHSCOPE_AVAILABLE') else '不可用'}\n")
    
    # 测试通义百炼知识检索
    test_query = "检索甲烷相关的知识"
    print(f"2. 测试通义百炼知识检索:")
    print(f"   查询: {test_query}")
    
    try:
        result = knowledge_api.search_tongyi_knowledge(test_query)
        print(f"   结果状态: {'成功' if result.get('success') else '失败'}")
        
        if result.get('success'):
            answer = result.get('answer', '')
            print(f"   答案长度: {len(answer)}字符")
            print(f"   答案预览: {answer[:100]}..." if len(answer) > 100 else f"   完整答案: {answer}")
            if result.get('usage'):
                print(f"   使用统计: {result['usage']}")
        else:
            print(f"   错误信息: {result.get('error', '未知错误')}")
    except Exception as e:
        print(f"   异常: {str(e)}")
    
    print("\n" + "="*50 + "\n")

def test_enhanced_comprehensive_info():
    """
    测试增强的综合信息获取功能
    """
    print("=== 测试增强综合信息获取 ===\n")
    
    knowledge_api = KnowledgeAPI()
    test_query = "甲烷的分子结构和性质"
    
    print(f"查询: {test_query}")
    
    try:
        result = knowledge_api.get_enhanced_comprehensive_info(test_query)
        
        print(f"\n综合答案长度: {len(result.get('combined_answer', ''))}字符")
        print(f"成功的知识源数量: {len(result.get('all_sources', []))}")
        
        # 显示各个知识源的结果
        for source in result.get('all_sources', []):
            print(f"\n知识源: {source.get('source', '未知')}")
            print(f"状态: {'成功' if source.get('success') else '失败'}")
            content = source.get('content', '')
            if content:
                print(f"内容预览: {content[:150]}..." if len(content) > 150 else f"内容: {content}")
        
        # 显示综合答案的开头部分
        combined_answer = result.get('combined_answer', '')
        if combined_answer:
            print(f"\n综合答案预览:\n{combined_answer[:300]}..." if len(combined_answer) > 300 else f"\n完整综合答案:\n{combined_answer}")
        
    except Exception as e:
        print(f"异常: {str(e)}")
    
    print("\n" + "="*50 + "\n")

def test_rag_retriever_integration():
    """
    测试RAG检索器的通义百炼集成
    """
    print("=== 测试RAG检索器集成 ===\n")
    
    try:
        # 初始化RAG检索器（不强制重建索引）
        retriever = RAGRetriever(force_recreate=False, use_reranker=False, enable_adaptive=False)
        
        # 检查知识API状态
        print("1. 知识API状态:")
        status = retriever.get_knowledge_api_status()
        for key, value in status.items():
            print(f"   {key}: {'是' if value else '否'}")
        
        # 测试仅通义百炼检索
        test_query = "甲烷燃烧反应"
        print(f"\n2. 测试仅通义百炼检索:")
        print(f"   查询: {test_query}")
        
        tongyi_result = retriever.search_tongyi_only(test_query)
        print(f"   结果状态: {'成功' if tongyi_result.get('success') else '失败'}")
        
        if tongyi_result.get('success'):
            answer = tongyi_result.get('answer', '')
            print(f"   答案长度: {len(answer)}字符")
            print(f"   答案预览: {answer[:150]}..." if len(answer) > 150 else f"   完整答案: {answer}")
        else:
            print(f"   错误: {tongyi_result.get('error', '未知错误')}")
        
        # 测试综合检索（本地+外部）
        print(f"\n3. 测试综合检索（本地+外部知识库）:")
        print(f"   查询: {test_query}")
        
        comprehensive_result = retriever.retrieve_with_external_knowledge(
            test_query, 
            k=3, 
            include_tongyi=True, 
            include_metaso=True, 
            include_pubchem=True
        )
        
        print(f"   本地文档数量: {len(comprehensive_result.get('local_documents', []))}")
        print(f"   知识源数量: {len(comprehensive_result.get('sources', []))}")
        print(f"   知识源: {', '.join(comprehensive_result.get('sources', []))}")
        
        combined_answer = comprehensive_result.get('combined_answer', '')
        if combined_answer:
            print(f"   综合答案长度: {len(combined_answer)}字符")
            print(f"   综合答案预览: {combined_answer[:200]}..." if len(combined_answer) > 200 else f"   完整答案: {combined_answer}")
        
    except Exception as e:
        print(f"RAG检索器测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50 + "\n")

def main():
    """
    主测试函数
    """
    print("通义百炼知识检索智能体集成测试\n")
    print("="*60)
    
    # 测试1: KnowledgeAPI基础功能
    test_knowledge_api()
    
    # 测试2: 增强综合信息获取
    test_enhanced_comprehensive_info()
    
    # 测试3: RAG检索器集成
    test_rag_retriever_integration()
    
    print("测试完成！")

if __name__ == "__main__":
    main()