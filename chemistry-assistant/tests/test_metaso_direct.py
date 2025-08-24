#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试Metaso知识库API调用
不依赖项目的其他模块
"""

import requests
import json
import time

def test_metaso_api_direct():
    """直接测试Metaso API调用"""
    print("=== 直接测试Metaso知识库API ===")
    
    # API配置
    url = 'https://metaso.cn/api/open/search/v2'
    headers = {
        'Authorization': 'Bearer mk-3FCF7B3E7AA7A7357AB297B790401583',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }
    
    # 测试查询列表
    test_queries = [
        "请总结知识库中关于甲烷的主要内容",
        "乙醇的化学性质和应用",
        "苯的结构特点和化学反应",
        "酸碱反应的基本原理"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i}: {query} ---")
        
        params = {
            'question': query,
            'searchTopicId': '8640179836073414656'
        }
        
        try:
            print(f"发送请求到: {url}")
            print(f"查询内容: {query}")
            
            start_time = time.time()
            response = requests.post(url, data=json.dumps(params), headers=headers, timeout=30)
            end_time = time.time()
            
            print(f"请求耗时: {end_time - start_time:.2f}秒")
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    if result.get('errCode') == 0:
                        print("✅ API调用成功!")
                        
                        data = result.get('data', {})
                        
                        # 基本信息
                        print(f"结果ID: {data.get('resultId', 'N/A')}")
                        print(f"会话ID: {data.get('sessionId', 'N/A')}")
                        print(f"余额: {data.get('balance', 'N/A')}")
                        
                        # 答案内容
                        answer = data.get('text', '')
                        print(f"答案长度: {len(answer)}字符")
                        
                        if answer:
                            # 显示答案前300字符
                            print(f"\n答案预览:\n{answer[:300]}...")
                        
                        # 参考文献
                        references = data.get('references', [])
                        print(f"\n参考文献数量: {len(references)}")
                        
                        if references:
                            print("参考文献详情:")
                            for j, ref in enumerate(references[:3], 1):
                                print(f"  {j}. 标题: {ref.get('title', '未知标题')}")
                                print(f"     作者: {ref.get('author', '未知作者')}")
                                print(f"     类型: {ref.get('article_type', '未知类型')}")
                                print(f"     页码: {ref.get('page', 'N/A')}/{ref.get('total_page', 'N/A')}")
                                if ref.get('publish_date'):
                                    print(f"     发布日期: {ref.get('publish_date')}")
                                print()
                    else:
                        print(f"❌ API返回错误: errCode = {result.get('errCode')}")
                        print(f"错误信息: {result}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {str(e)}")
                    print(f"原始响应: {response.text[:500]}...")
            else:
                print(f"❌ HTTP请求失败: {response.status_code}")
                print(f"响应内容: {response.text[:500]}...")
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误")
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
        
        # 在测试之间稍作停顿
        if i < len(test_queries):
            print("等待2秒后进行下一个测试...")
            time.sleep(2)

def test_api_configuration():
    """测试API配置"""
    print("\n=== 测试API配置 ===")
    
    # 检查配置
    config = {
        'url': 'https://metaso.cn/api/open/search/v2',
        'api_key': 'mk-3FCF7B3E7AA7A7357AB297B790401583',
        'search_topic_id': '8640179836073414656'
    }
    
    print("API配置信息:")
    for key, value in config.items():
        if 'key' in key.lower():
            # 隐藏API密钥的部分内容
            masked_value = value[:10] + '*' * (len(value) - 20) + value[-10:] if len(value) > 20 else value
            print(f"  {key}: {masked_value}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ 配置检查完成")

def main():
    """主测试函数"""
    print("开始直接测试Metaso知识库API...")
    print("这个测试不依赖项目的其他模块，直接调用API")
    
    # 测试API配置
    test_api_configuration()
    
    # 测试API调用
    test_metaso_api_direct()
    
    print("\n=== 测试完成 ===")
    print("\n如果API调用成功，说明Metaso知识库可以正常访问!")
    print("接下来可以将其集成到项目的KnowledgeAPI类中。")

if __name__ == "__main__":
    main()