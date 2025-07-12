#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API嵌入模型测试脚本
用于测试不同API提供商的嵌入服务
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.api_embedding_model import APIEmbeddingModel, create_zhipu_embedding, create_tongyi_embedding
from models.embedding_model import EmbeddingModel
from config import MODEL_CONFIG

def test_api_embedding(provider='zhipu'):
    """
    测试指定API提供商的嵌入服务
    """
    print(f"\n=== 测试 {provider} API嵌入模型 ===")
    
    try:
        # 创建API嵌入模型
        if provider == 'zhipu':
            model = create_zhipu_embedding()
        elif provider == 'tongyi':
            model = create_tongyi_embedding()
        else:
            model = APIEmbeddingModel(provider=provider)
        
        # 测试连接
        print("\n1. 测试API连接...")
        if model.test_connection():
            print("✅ API连接成功")
        else:
            print("❌ API连接失败")
            return False
        
        # 测试单个文本嵌入
        print("\n2. 测试单个文本嵌入...")
        test_text = "化学是研究物质的组成、结构、性质、变化规律的科学"
        embedding = model.get_embedding(test_text)
        print(f"文本: {test_text}")
        print(f"嵌入向量维度: {len(embedding)}")
        print(f"向量前5个值: {embedding[:5]}")
        
        # 测试批量文本嵌入
        print("\n3. 测试批量文本嵌入...")
        test_texts = [
            "氢气是最轻的气体",
            "氧气支持燃烧",
            "水的化学式是H2O",
            "碳酸钠是一种碱性盐",
            "酸碱中和反应产生盐和水"
        ]
        embeddings = model.get_embeddings_batch(test_texts, batch_size=3)
        print(f"批量处理 {len(test_texts)} 个文本")
        print(f"返回嵌入矩阵形状: {embeddings.shape}")
        
        # 测试LangChain兼容性
        print("\n4. 测试LangChain兼容性...")
        query_embedding = model.embed_query("什么是化学反应？")
        doc_embeddings = model.embed_documents(["化学反应是原子重新组合的过程", "反应物转化为生成物"])
        print(f"查询嵌入维度: {len(query_embedding)}")
        print(f"文档嵌入数量: {len(doc_embeddings)}")
        print(f"每个文档嵌入维度: {len(doc_embeddings[0])}")
        
        print(f"\n✅ {provider} API嵌入模型测试完成")
        return True
        
    except Exception as e:
        print(f"❌ {provider} API嵌入模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_embedding_model():
    """
    测试统一的嵌入模型（支持API和本地模型切换）
    """
    print("\n=== 测试统一嵌入模型 ===")
    
    try:
        # 测试API模式
        print("\n当前配置:")
        print(f"使用API: {MODEL_CONFIG['embedding'].get('use_api', False)}")
        print(f"API提供商: {MODEL_CONFIG['embedding'].get('api_provider', 'N/A')}")
        print(f"API模型: {MODEL_CONFIG['embedding'].get('api_model', 'N/A')}")
        
        model = EmbeddingModel()
        
        # 测试基本功能
        test_text = "测试统一嵌入模型的功能"
        embedding = model.get_embedding(test_text)
        print(f"\n文本: {test_text}")
        print(f"嵌入向量维度: {len(embedding)}")
        
        # 测试批量处理
        test_texts = ["文本1", "文本2", "文本3"]
        embeddings = model.get_embeddings_batch(test_texts)
        print(f"批量处理结果形状: {embeddings.shape}")
        
        print("✅ 统一嵌入模型测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 统一嵌入模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主测试函数
    """
    print("API嵌入模型测试开始")
    print("=" * 50)
    
    # 检查配置
    print("当前配置信息:")
    embedding_config = MODEL_CONFIG.get('embedding', {})
    print(f"- 使用API: {embedding_config.get('use_api', False)}")
    print(f"- API提供商: {embedding_config.get('api_provider', 'N/A')}")
    print(f"- API模型: {embedding_config.get('api_model', 'N/A')}")
    
    # 检查API密钥
    zhipu_key = MODEL_CONFIG.get('zhipu', {}).get('api_key', '')
    tongyi_key = MODEL_CONFIG.get('tongyi', {}).get('api_key', '')
    
    print(f"\nAPI密钥状态:")
    print(f"- 智谱AI: {'已配置' if zhipu_key else '未配置'}")
    print(f"- 通义千问: {'已配置' if tongyi_key else '未配置'}")
    
    success_count = 0
    total_tests = 0
    
    # 测试智谱AI
    if zhipu_key:
        total_tests += 1
        if test_api_embedding('zhipu'):
            success_count += 1
    else:
        print("\n⚠️ 智谱AI API密钥未配置，跳过测试")
    
    # 测试通义千问
    if tongyi_key:
        total_tests += 1
        if test_api_embedding('tongyi'):
            success_count += 1
    else:
        print("\n⚠️ 通义千问API密钥未配置，跳过测试")
    
    # 测试统一模型
    total_tests += 1
    if test_unified_embedding_model():
        success_count += 1
    
    # 总结
    print("\n" + "=" * 50)
    print(f"测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接")

if __name__ == "__main__":
    main()