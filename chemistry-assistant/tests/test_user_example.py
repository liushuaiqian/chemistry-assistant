#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用用户提供的原始示例代码测试Metaso API
"""

import requests
import json

def test_original_example():
    """使用用户提供的原始示例代码"""
    print("=== 使用用户原始示例代码测试 ===")
    
    url = 'https://metaso.cn/api/open/search/v2'
    params = {
        'question': '请总结知识库中关于甲烷的主要内容',
        'searchTopicId': '8640179836073414656'
    }
    
    headers = {
        'Authorization': 'Bearer mk-3FCF7B3E7AA7A7357AB297B790401583',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }
    
    try:
        print(f"发送请求到: {url}")
        print(f"请求参数: {params}")
        print(f"请求头: {headers}")
        
        response = requests.post(url, data=json.dumps(params), headers=headers)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n解析后的JSON: {json.dumps(result, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {str(e)}")
        
    except Exception as e:
        print(f"请求异常: {str(e)}")

def test_different_auth_formats():
    """测试不同的认证格式"""
    print("\n=== 测试不同的认证格式 ===")
    
    url = 'https://metaso.cn/api/open/search/v2'
    params = {
        'question': '甲烷的基本性质',
        'searchTopicId': '8640179836073414656'
    }
    
    # 测试不同的认证头格式
    auth_formats = [
        {'Authorization': 'Bearer mk-3FCF7B3E7AA7A7357AB297B790401583'},
        {'Authorization': 'mk-3FCF7B3E7AA7A7357AB297B790401583'},
        {'X-API-Key': 'mk-3FCF7B3E7AA7A7357AB297B790401583'},
        {'api-key': 'mk-3FCF7B3E7AA7A7357AB297B790401583'}
    ]
    
    for i, auth_header in enumerate(auth_formats, 1):
        print(f"\n--- 测试认证格式 {i}: {auth_header} ---")
        
        headers = {
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        }
        headers.update(auth_header)
        
        try:
            response = requests.post(url, data=json.dumps(params), headers=headers, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('errCode') == 0:
                        print("✅ 认证成功!")
                        return headers  # 返回成功的认证格式
                    else:
                        print(f"❌ API错误: {result.get('errCode')} - {result.get('errMsg', '')}")
                except json.JSONDecodeError:
                    print(f"❌ JSON解析失败")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
    
    return None

def test_parameter_formats():
    """测试不同的参数格式"""
    print("\n=== 测试不同的参数格式 ===")
    
    url = 'https://metaso.cn/api/open/search/v2'
    
    # 测试不同的参数格式
    param_formats = [
        # 格式1: 原始格式
        {
            'question': '甲烷的基本性质',
            'searchTopicId': '8640179836073414656'
        },
        # 格式2: 不同的字段名
        {
            'query': '甲烷的基本性质',
            'topicId': '8640179836073414656'
        },
        # 格式3: 添加更多参数
        {
            'question': '甲烷的基本性质',
            'searchTopicId': '8640179836073414656',
            'limit': 10
        }
    ]
    
    headers = {
        'Authorization': 'Bearer mk-3FCF7B3E7AA7A7357AB297B790401583',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }
    
    for i, params in enumerate(param_formats, 1):
        print(f"\n--- 测试参数格式 {i}: {params} ---")
        
        try:
            response = requests.post(url, data=json.dumps(params), headers=headers, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"响应: {result}")
                    if result.get('errCode') == 0:
                        print("✅ 参数格式正确!")
                        return params
                    else:
                        print(f"❌ API错误: {result.get('errCode')} - {result.get('errMsg', '')}")
                except json.JSONDecodeError:
                    print(f"❌ JSON解析失败")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
    
    return None

def main():
    """主测试函数"""
    print("开始调试Metaso API调用问题...")
    
    # 测试1: 使用原始示例代码
    test_original_example()
    
    # 测试2: 尝试不同的认证格式
    successful_auth = test_different_auth_formats()
    
    # 测试3: 尝试不同的参数格式
    successful_params = test_parameter_formats()
    
    print("\n=== 调试总结 ===")
    if successful_auth:
        print(f"✅ 成功的认证格式: {successful_auth}")
    else:
        print("❌ 所有认证格式都失败")
    
    if successful_params:
        print(f"✅ 成功的参数格式: {successful_params}")
    else:
        print("❌ 所有参数格式都失败")
    
    print("\n可能的问题:")
    print("1. API密钥可能已过期或无效")
    print("2. searchTopicId可能不正确")
    print("3. API端点可能已更改")
    print("4. 需要额外的认证参数")
    print("\n建议检查API文档或联系API提供方确认正确的调用方式。")

if __name__ == "__main__":
    main()