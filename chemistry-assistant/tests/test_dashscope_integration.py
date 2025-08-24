#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试 dashscope SDK 集成
验证阿里百炼 multimodal-embedding-v1 模型的调用方式
"""

from models.api_embedding_model import APIEmbeddingModel, DASHSCOPE_AVAILABLE
import numpy as np

def test_dashscope_integration():
    """
    测试 dashscope SDK 集成
    """
    print("=== 测试 Dashscope SDK 集成 ===")
    print(f"Dashscope SDK 可用性: {DASHSCOPE_AVAILABLE}")
    
    if not DASHSCOPE_AVAILABLE:
        print("⚠️ Dashscope SDK 未安装，将使用 HTTP 请求方式")
    else:
        print("✅ Dashscope SDK 已安装")
    
    # 创建 tongyi 嵌入模型
    try:
        model = APIEmbeddingModel(provider='tongyi', model_name='multimodal-embedding-v1')
        print(f"✅ 模型初始化成功: {model.model_name}")
    except Exception as e:
        print(f"❌ 模型初始化失败: {e}")
        return
    
    # 测试单个文本嵌入
    print("\n1. 测试单个文本嵌入...")
    test_text = "阿里百炼多模态嵌入模型测试"
    try:
        embedding = model.get_embedding(test_text)
        print(f"✅ 单个文本嵌入成功")
        print(f"   文本: {test_text}")
        print(f"   向量维度: {len(embedding)}")
        print(f"   向量类型: {type(embedding)}")
        print(f"   前5个值: {embedding[:5]}")
    except Exception as e:
        print(f"❌ 单个文本嵌入失败: {e}")
    
    # 测试批量文本嵌入
    print("\n2. 测试批量文本嵌入...")
    test_texts = [
        "化学反应的基本原理",
        "有机化学分子结构",
        "无机化学元素周期表",
        "物理化学热力学定律"
    ]
    
    try:
        embeddings = model.get_embeddings_batch(test_texts, batch_size=2)
        print(f"✅ 批量文本嵌入成功")
        print(f"   文本数量: {len(test_texts)}")
        print(f"   返回矩阵形状: {embeddings.shape}")
        print(f"   数据类型: {embeddings.dtype}")
    except Exception as e:
        print(f"❌ 批量文本嵌入失败: {e}")
    
    # 测试 SDK 特定功能
    if DASHSCOPE_AVAILABLE:
        print("\n3. 测试 Dashscope SDK 特定功能...")
        try:
            sdk_embeddings = model._get_tongyi_embedding_with_sdk("SDK 直接调用测试")
            if sdk_embeddings:
                print(f"✅ SDK 直接调用成功")
                print(f"   返回向量数量: {len(sdk_embeddings)}")
                print(f"   向量维度: {len(sdk_embeddings[0])}")
            else:
                print("❌ SDK 直接调用返回空结果")
        except Exception as e:
            print(f"❌ SDK 直接调用失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_dashscope_integration()