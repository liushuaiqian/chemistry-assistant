#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试教材检索功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.rag_retriever import RAGRetriever

def test_textbook_retrieval():
    """测试教材检索功能"""
    print("🔍 开始测试教材检索功能...")
    
    try:
        # 创建RAGRetriever实例
        retriever = RAGRetriever()
        print("✅ RAGRetriever初始化成功")
        
        # 测试查询
        test_queries = [
            "苯的性质",
            "化学键",
            "甲烷燃烧",
            "酸碱反应"
        ]
        
        for query in test_queries:
            print(f"\n📝 测试查询: {query}")
            try:
                # 测试教材检索
                results = retriever.retrieve_from_textbooks(query, k=3)
                print(f"✅ 检索成功，返回 {len(results)} 个结果")
                
                if results:
                    for i, result in enumerate(results[:2], 1):
                        print(f"   [{i}] {result[:100]}...")
                else:
                    print("   ⚠️ 未找到相关内容")
                    
            except Exception as e:
                print(f"❌ 检索失败: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ RAGRetriever初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_textbook_retrieval()