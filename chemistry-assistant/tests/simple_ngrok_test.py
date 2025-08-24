#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的Ngrok测试
"""

import time
from pyngrok import ngrok

def test_ngrok():
    """测试Ngrok基本功能"""
    print("🔧 开始测试Ngrok...")
    
    try:
        print("📝 设置Ngrok认证token...")
        ngrok.set_auth_token("30wI9yvO37ZIJZLmGMFO1RcuHjm_3axwVACtnAwToAeUFirKF")
        print("✅ Ngrok认证token设置成功")
        
        print("🚇 创建HTTP隧道到端口8000...")
        public_url = ngrok.connect(8000)
        print(f"🌍 公网访问地址: {public_url}")
        
        print("📋 获取所有活动隧道...")
        tunnels = ngrok.get_tunnels()
        print(f"活动隧道数量: {len(tunnels)}")
        for tunnel in tunnels:
            print(f"  - {tunnel.name}: {tunnel.public_url} -> {tunnel.config['addr']}")
        
        print("⏰ 隧道将保持5秒钟...")
        time.sleep(5)
        
        print("🔌 断开隧道...")
        ngrok.disconnect(public_url)
        print("✅ 隧道已断开")
        
        print("🧹 清理所有隧道...")
        ngrok.kill()
        print("✅ 所有隧道已清理")
        
    except Exception as e:
        print(f"❌ Ngrok测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    print("🎉 Ngrok测试成功完成！")
    return True

if __name__ == "__main__":
    success = test_ngrok()
    if success:
        print("\n✅ Ngrok功能正常，可以集成到Gradio应用中")
    else:
        print("\n❌ Ngrok功能异常，请检查网络连接和token")