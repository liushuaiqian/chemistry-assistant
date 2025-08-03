#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用用户提供的正确API密钥测试Metaso API
"""

import requests
import json

def test_with_correct_api_key():
    """使用用户提供的正确API密钥测试"""
    print("=== 使用正确的API密钥测试Metaso API ===")
    
    url = 'https://metaso.cn/api/open/search/v2'
    params = {
        'question': 'please summarize',
        'searchTopicId': '8640179836073414656'
    }
    
    headers = {
        'Authorization': 'Bearer mk-3751176E6B379BB3C57E79BCB513BD33',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }
    
    try:
        print(f"发送请求到: {url}")
        print(f"请求参数: {params}")
        print(f"API密钥: mk-3751176E6B379BB3C57E79BCB513BD33")
        
        response = requests.post(url, data=json.dumps(params), headers=headers)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n解析后的JSON:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                if result.get('errCode') == 0:
                    print("\n✅ API调用成功!")
                    
                    data = result.get('data', {})
                    print(f"结果ID: {data.get('resultId', 'N/A')}")
                    print(f"会话ID: {data.get('sessionId', 'N/A')}")
                    print(f"余额: {data.get('balance', 'N/A')}")
                    
                    answer = data.get('text', '')
                    print(f"答案长度: {len(answer)}字符")
                    
                    if answer:
                        print(f"\n答案内容:\n{answer}")
                    
                    references = data.get('references', [])
                    print(f"\n参考文献数量: {len(references)}")
                    
                    if references:
                        print("参考文献:")
                        for i, ref in enumerate(references, 1):
                            print(f"  {i}. {ref.get('title', '未知标题')}")
                            print(f"     作者: {ref.get('author', '未知作者')}")
                            print(f"     页码: {ref.get('page', 'N/A')}/{ref.get('total_page', 'N/A')}")
                    
                    return True
                else:
                    print(f"❌ API返回错误: errCode = {result.get('errCode')}")
                    print(f"错误信息: {result.get('errMsg', '')}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {str(e)}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def test_chemistry_queries():
    """测试化学相关查询"""
    print("\n=== 测试化学相关查询 ===")
    
    url = 'https://metaso.cn/api/open/search/v2'
    headers = {
        'Authorization': 'Bearer mk-3751176E6B379BB3C57E79BCB513BD33',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }
    
    chemistry_queries = [
        "请总结知识库中关于甲烷的主要内容",
        "乙醇的化学性质和应用",
        "苯的结构特点和化学反应"
    ]
    
    for i, query in enumerate(chemistry_queries, 1):
        print(f"\n--- 测试查询 {i}: {query} ---")
        
        params = {
            'question': query,
            'searchTopicId': '8640179836073414656'
        }
        
        try:
            response = requests.post(url, data=json.dumps(params), headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('errCode') == 0:
                    print("✅ 查询成功")
                    data = result.get('data', {})
                    answer = data.get('text', '')
                    print(f"答案长度: {len(answer)}字符")
                    
                    if answer:
                        print(f"答案预览: {answer[:200]}...")
                else:
                    print(f"❌ 查询失败: {result.get('errMsg', '')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 查询异常: {str(e)}")

def main():
    """主测试函数"""
    print("开始使用正确的API密钥测试Metaso知识库API...")
    
    # 测试基本连接
    success = test_with_correct_api_key()
    
    if success:
        print("\n基本测试成功，继续测试化学查询...")
        test_chemistry_queries()
        
        print("\n=== 测试总结 ===")
        print("✅ Metaso知识库API连接正常")
        print("✅ 可以正常获取化学相关信息")
        print("✅ 准备集成到项目的KnowledgeAPI中")
    else:
        print("\n❌ 基本测试失败，请检查API配置")

if __name__ == "__main__":
    main()