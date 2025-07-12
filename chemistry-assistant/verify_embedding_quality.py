#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证嵌入向量质量脚本
用于检查知识库是否使用了真实的API向量还是随机向量
"""

import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_embedding_consistency():
    """
    测试嵌入向量的一致性
    如果是真实的API向量，同一文本的多次嵌入应该完全相同
    如果是随机向量，每次都会不同
    """
    print("测试嵌入向量一致性...")
    
    try:
        from models.embedding_model import EmbeddingModel
        
        model = EmbeddingModel()
        test_text = "化学反应的基本原理"
        
        print(f"测试文本: {test_text}")
        print("获取3次嵌入向量...")
        
        # 获取同一文本的3次嵌入
        embedding1 = model.get_embedding(test_text)
        embedding2 = model.get_embedding(test_text)
        embedding3 = model.get_embedding(test_text)
        
        # 计算向量之间的相似度
        similarity_1_2 = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        similarity_1_3 = np.dot(embedding1, embedding3) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding3))
        similarity_2_3 = np.dot(embedding2, embedding3) / (np.linalg.norm(embedding2) * np.linalg.norm(embedding3))
        
        print(f"\n向量维度: {len(embedding1)}")
        print(f"向量1与向量2相似度: {similarity_1_2:.6f}")
        print(f"向量1与向量3相似度: {similarity_1_3:.6f}")
        print(f"向量2与向量3相似度: {similarity_2_3:.6f}")
        
        # 判断是否为真实向量
        if similarity_1_2 > 0.999 and similarity_1_3 > 0.999 and similarity_2_3 > 0.999:
            print("\n✅ 结论: 使用的是真实的API嵌入向量")
            print("   同一文本的多次嵌入结果完全一致")
            return True
        elif similarity_1_2 < 0.1 and similarity_1_3 < 0.1 and similarity_2_3 < 0.1:
            print("\n❌ 结论: 使用的是随机向量")
            print("   同一文本的多次嵌入结果完全不同")
            return False
        else:
            print("\n⚠️  结论: 向量质量不确定")
            print("   可能存在部分API调用失败的情况")
            return None
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_knowledge_base_vectors():
    """
    测试知识库中的向量质量
    """
    print("\n测试知识库向量质量...")
    
    try:
        from tools.rag_retriever import RAGRetriever
        
        # 初始化检索器
        retriever = RAGRetriever()
        
        # 测试查询
        test_query = "化学反应速率"
        print(f"测试查询: {test_query}")
        
        # 获取查询向量
        query_embedding = retriever.embedding_model.get_embedding(test_query)
        
        # 进行检索
        results = retriever.search_textbooks(test_query, k=3)
        
        print(f"\n检索结果数量: {len(results)}")
        if results:
            print("前3个检索结果:")
            for i, result in enumerate(results[:3], 1):
                content_preview = result.page_content[:100].replace('\n', ' ')
                print(f"  {i}. {content_preview}...")
                print(f"     相似度分数: {getattr(result, 'score', 'N/A')}")
            
            print("\n✅ 知识库检索功能正常")
            return True
        else:
            print("\n❌ 知识库检索未返回结果")
            return False
            
    except Exception as e:
        print(f"❌ 知识库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_api_configuration():
    """
    检查API配置状态
    """
    print("\n检查API配置状态...")
    
    try:
        from config import MODEL_CONFIG
        
        embedding_config = MODEL_CONFIG.get('embedding', {})
        use_api = embedding_config.get('use_api', False)
        api_provider = embedding_config.get('api_provider', '')
        api_model = embedding_config.get('api_model', '')
        
        print(f"使用API模式: {use_api}")
        if use_api:
            print(f"API提供商: {api_provider}")
            print(f"API模型: {api_model}")
            
            # 检查API密钥
            provider_config = MODEL_CONFIG.get(api_provider, {})
            api_key = provider_config.get('api_key', '')
            
            if api_key:
                print(f"API密钥: 已配置 (长度: {len(api_key)})")
                
                # 测试API连接
                from models.api_embedding_model import APIEmbeddingModel
                api_model_instance = APIEmbeddingModel(provider=api_provider)
                connection_ok = api_model_instance.test_connection()
                
                if connection_ok:
                    print("✅ API连接测试成功")
                else:
                    print("❌ API连接测试失败")
                    
                return connection_ok
            else:
                print("❌ API密钥未配置")
                return False
        else:
            print("当前使用本地模型模式")
            return True
            
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

def main():
    print("嵌入向量质量验证工具")
    print("=" * 50)
    
    # 1. 检查API配置
    config_ok = check_api_configuration()
    
    # 2. 测试嵌入向量一致性
    consistency_result = test_embedding_consistency()
    
    # 3. 测试知识库功能
    kb_result = test_knowledge_base_vectors()
    
    # 总结
    print("\n" + "=" * 50)
    print("验证结果总结:")
    
    if consistency_result is True:
        print("✅ 嵌入向量质量: 真实API向量")
        print("✅ 知识库状态: 使用高质量向量，检索效果良好")
    elif consistency_result is False:
        print("❌ 嵌入向量质量: 随机向量")
        print("❌ 知识库状态: 使用随机向量，检索效果差")
        print("\n建议解决方案:")
        print("1. 检查网络连接和API密钥配置")
        print("2. 运行: python switch_embedding_mode.py --mode test")
        print("3. 重新更新知识库: python update_knowledge_base.py --mode all")
    else:
        print("⚠️  嵌入向量质量: 不确定")
        print("⚠️  知识库状态: 可能存在部分问题")
    
    if kb_result:
        print("✅ 知识库检索: 功能正常")
    else:
        print("❌ 知识库检索: 存在问题")
    
    if not config_ok:
        print("❌ API配置: 存在问题")
    
if __name__ == "__main__":
    main()