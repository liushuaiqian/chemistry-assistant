#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试图像处理功能
"""

import base64
import requests
from config import MODEL_CONFIG
from utils.logger import setup_logger

def test_tongyi_vision_api():
    """
    测试通义千问视觉模型API
    """
    logger = setup_logger("test_vision")
    
    # 获取配置
    tongyi_vision_config = MODEL_CONFIG.get('tongyi_vision', {})
    api_key = tongyi_vision_config.get('api_key', '')
    model = tongyi_vision_config.get('model', 'qwen-vl-max')
    
    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: 未配置")
    print(f"Model: {model}")
    
    if not api_key:
        print("❌ 通义视觉模型API密钥未配置")
        return False
    
    # 创建一个简单的测试图像（base64编码的1x1像素图像）
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请描述这张图片的内容。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{test_image_base64}"
                                }
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "temperature": 0.1,
                "top_p": 0.8
            }
        }
        
        print("🔄 正在测试通义视觉模型API...")
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 通义视觉模型API调用成功")
            print(f"响应内容: {result}")
            return True
        else:
            print(f"❌ 通义视觉模型API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        return False

def test_multimodal_processor():
    """
    测试多模态处理器
    """
    try:
        from core.multimodal_processor import MultimodalProcessor
        
        print("🔄 正在测试多模态处理器...")
        processor = MultimodalProcessor()
        
        # 测试文本输入
        text_result = processor.process_input("计算H2O的摩尔质量", "text")
        print(f"✅ 文本处理结果: {text_result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 多模态处理器测试失败: {str(e)}")
        return False

def test_controller_multimodal():
    """
    测试Controller的多模态处理
    """
    try:
        from core.controller import Controller
        
        print("🔄 正在测试Controller多模态处理...")
        controller = Controller()
        
        # 测试文本输入
        result = controller.process_multimodal_input("什么是化学键？", "text")
        print(f"✅ Controller多模态处理结果: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Controller多模态处理测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 图像处理功能测试 ===")
    
    # 测试1: 通义视觉API
    print("\n1. 测试通义视觉模型API")
    api_success = test_tongyi_vision_api()
    
    # 测试2: 多模态处理器
    print("\n2. 测试多模态处理器")
    processor_success = test_multimodal_processor()
    
    # 测试3: Controller多模态处理
    print("\n3. 测试Controller多模态处理")
    controller_success = test_controller_multimodal()
    
    # 总结
    print("\n=== 测试结果总结 ===")
    print(f"通义视觉API: {'✅ 成功' if api_success else '❌ 失败'}")
    print(f"多模态处理器: {'✅ 成功' if processor_success else '❌ 失败'}")
    print(f"Controller多模态: {'✅ 成功' if controller_success else '❌ 失败'}")
    
    if not api_success:
        print("\n💡 建议检查:")
        print("1. 通义千问API密钥是否正确配置")
        print("2. 网络连接是否正常")
        print("3. API密钥是否有视觉模型的调用权限")