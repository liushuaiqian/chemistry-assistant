#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文本排序器功能测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.text_reranker import TextReranker
from tools.rag_retriever import RAGRetriever
from core.chemistry_chain import ChemistryAnalysisChain
from core.controller import Controller

def test_text_reranker():
    """
    测试文本排序器基本功能
    """
    print("=== 测试文本排序器基本功能 ===")
    
    reranker = TextReranker()
    
    if not reranker.is_available():
        print("❌ 文本排序器不可用，请检查通义API密钥配置")
        return False
    
    # 测试数据
    query = "什么是化学键"
    documents = [
        "化学键是原子间相互结合的作用力，包括离子键、共价键和金属键",
        "量子力学是研究微观粒子运动规律的物理学分支",
        "共价键是原子间通过共享电子对形成的化学键",
        "离子键是正负离子间的静电相互作用",
        "金属键是金属原子间的化学键，具有非定向性和非饱和性"
    ]
    
    print(f"查询: {query}")
    print(f"候选文档数量: {len(documents)}")
    
    # 测试排序
    ranked_docs = reranker.rerank_with_scores(query, documents, top_n=3)
    
    if ranked_docs:
        print("\n✅ 排序结果:")
        for i, (doc, score) in enumerate(ranked_docs, 1):
            print(f"{i}. 分数: {score:.4f}")
            print(f"   文档: {doc}")
            print()
        return True
    else:
        print("❌ 排序失败")
        return False

def test_rag_retriever():
    """
    测试RAG检索器的双阶段检索功能
    """
    print("=== 测试RAG检索器双阶段检索功能 ===")
    
    try:
        # 测试启用排序器的检索器
        retriever_with_reranker = RAGRetriever(use_reranker=True)
        reranker_info = retriever_with_reranker.get_reranker_info()
        
        print(f"排序器状态: {reranker_info}")
        
        if reranker_info['enabled'] and reranker_info['available']:
            print("✅ 双阶段检索模式已启用")
            
            # 测试检索
            query = "化学键的类型有哪些"
            results = retriever_with_reranker.retrieve_comprehensive(
                query=query,
                textbook_k=3,
                question_k=2,
                rerank_top_n=4
            )
            
            print(f"\n检索查询: {query}")
            print(f"检索到文档数量: {len(results)}")
            
            if results:
                print("\n检索结果预览:")
                for i, doc in enumerate(results[:2], 1):
                    print(f"{i}. {doc[:100]}...")
                return True
            else:
                print("⚠️ 未检索到相关文档（可能是知识库为空）")
                return True
        else:
            print("❌ 双阶段检索模式不可用")
            return False
            
    except Exception as e:
        print(f"❌ RAG检索器测试失败: {str(e)}")
        return False

def test_chemistry_chain():
    """
    测试化学分析链的双阶段检索功能
    """
    print("=== 测试化学分析链双阶段检索功能 ===")
    
    try:
        # 测试启用排序器的化学分析链
        chain = ChemistryAnalysisChain(use_reranker=True)
        
        print("✅ 化学分析链初始化成功")
        
        # 获取排序器信息
        reranker_info = chain.rag_retriever.get_reranker_info()
        print(f"排序器状态: {reranker_info['enabled'] and reranker_info['available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 化学分析链测试失败: {str(e)}")
        return False

def test_controller():
    """
    测试控制器的双阶段检索功能
    """
    print("=== 测试控制器双阶段检索功能 ===")
    
    try:
        # 测试启用排序器的控制器
        controller = Controller(use_reranker=True)
        
        print("✅ 控制器初始化成功")
        
        # 获取排序器信息
        reranker_info = controller.chemistry_chain.rag_retriever.get_reranker_info()
        print(f"排序器状态: {reranker_info['enabled'] and reranker_info['available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 控制器测试失败: {str(e)}")
        return False

def main():
    """
    运行所有测试
    """
    print("开始测试文本排序器集成功能...\n")
    
    tests = [
        ("文本排序器基本功能", test_text_reranker),
        ("RAG检索器双阶段检索", test_rag_retriever),
        ("化学分析链集成", test_chemistry_chain),
        ("控制器集成", test_controller)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
            results.append((test_name, False))
        print(f"{'='*50}")
    
    # 输出测试总结
    print("\n" + "="*60)
    print("测试总结:")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！文本排序器集成成功！")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和依赖")

if __name__ == '__main__':
    main()