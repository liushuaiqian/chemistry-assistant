#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
演示 Ngrok 自动下载过程
"""

import os
from pyngrok import ngrok, conf
from pyngrok.installer import install_ngrok

def check_ngrok_installation():
    """检查 ngrok 是否已安装"""
    print("🔍 检查 ngrok 安装状态...")
    
    # 获取 ngrok 配置
    config = conf.get_default()
    ngrok_path = config.ngrok_path
    
    print(f"📁 Ngrok 路径: {ngrok_path}")
    
    if os.path.exists(ngrok_path):
        print("✅ Ngrok 二进制文件已存在")
        return True
    else:
        print("❌ Ngrok 二进制文件不存在，需要下载")
        return False

def install_ngrok_manually():
    """手动安装 ngrok"""
    print("\n📥 开始下载 ngrok...")
    print("⚠️  这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 获取默认路径
        config = conf.get_default()
        ngrok_path = config.ngrok_path
        
        # 创建目录
        os.makedirs(os.path.dirname(ngrok_path), exist_ok=True)
        
        # 安装 ngrok
        install_ngrok(ngrok_path)
        print("✅ Ngrok 下载完成！")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print("💡 提示：这通常是因为网络问题或需要科学上网")
        return False

def test_ngrok_basic():
    """测试 ngrok 基本功能"""
    print("\n🧪 测试 ngrok 基本功能...")
    
    try:
        # 设置认证 token
        print("🔑 设置认证 token...")
        ngrok.set_auth_token("30wI9yvO37ZIJZLmGMFO1RcuHjm_3axwVACtnAwToAeUFirKF")
        
        # 获取版本信息
        print("📋 获取 ngrok 版本信息...")
        version = ngrok.get_ngrok_process().version
        print(f"Ngrok 版本: {version}")
        
        print("✅ Ngrok 基本功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Ngrok 安装和测试程序")
    print("=" * 50)
    
    # 检查是否已安装
    is_installed = check_ngrok_installation()
    
    if not is_installed:
        print("\n💡 这是第一次使用 ngrok，需要下载二进制文件")
        print("   这是正常现象，只需要下载一次")
        
        # 手动安装
        success = install_ngrok_manually()
        if not success:
            print("\n❌ 安装失败，请检查网络连接")
            exit(1)
    
    # 测试基本功能
    test_success = test_ngrok_basic()
    
    if test_success:
        print("\n🎉 恭喜！Ngrok 已准备就绪")
        print("   现在可以在 Gradio 应用中使用 ngrok 分享功能了")
    else:
        print("\n❌ 测试失败，请检查配置")