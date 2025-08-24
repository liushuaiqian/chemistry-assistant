#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Ngrok集成功能
"""

import gradio as gr
import socket
from pyngrok import ngrok

def find_free_port(start_port=7861, max_port=7900):
    """查找可用端口"""
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def simple_chat(message, history):
    """简单的聊天功能"""
    if not message.strip():
        return history, ""
    
    # 简单的回复逻辑
    response = f"您好！您说的是：{message}。这是一个测试回复。"
    history.append([message, response])
    return history, ""

def main():
    """主函数"""
    print("🧪 启动Ngrok测试应用...")
    
    # 查找可用端口
    available_port = find_free_port()
    if available_port is None:
        print("❌ 无法找到可用端口，请手动指定端口")
        available_port = 0  # 让Gradio自动分配
    else:
        print(f"🌐 使用端口: {available_port}")
    
    # 配置Ngrok
    public_url = None
    try:
        print("🔧 开始配置Ngrok...")
        
        # 设置Ngrok认证token
        print("📝 设置Ngrok认证token...")
        ngrok.set_auth_token("30wI9yvO37ZIJZLmGMFO1RcuHjm_3axwVACtnAwToAeUFirKF")
        print("✅ Ngrok认证token已设置")
        
        # 创建Ngrok隧道
        print(f"🚇 创建Ngrok隧道，端口: {available_port}...")
        public_url = ngrok.connect(available_port, bind_tls=True)
        print(f"🌍 公网访问地址: {public_url}")
        print(f"📱 您可以通过以下链接在任何设备上访问应用: {public_url}")
        print("✅ Ngrok隧道创建成功！")
        
    except Exception as e:
        print(f"⚠️ Ngrok配置失败: {e}")
        print(f"错误详情: {type(e).__name__}: {str(e)}")
        print("将使用本地模式启动")
        import traceback
        traceback.print_exc()
    
    # 创建简单的Gradio界面
    with gr.Blocks(title="🧪 Ngrok测试应用", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🧪 Ngrok测试应用")
        gr.Markdown("这是一个用于测试Ngrok集成功能的简单应用。")
        
        if public_url:
            gr.Markdown(f"### 🌍 公网访问地址: {public_url}")
            gr.Markdown("您可以通过上面的链接在任何设备上访问此应用！")
        
        chatbot = gr.Chatbot(label="聊天记录")
        msg = gr.Textbox(label="输入消息", placeholder="请输入您的消息...")
        clear = gr.Button("清除")
        
        msg.submit(simple_chat, [msg, chatbot], [chatbot, msg])
        clear.click(lambda: ([], ""), outputs=[chatbot, msg])
    
    # 启动应用
    try:
        demo.launch(
            server_name="127.0.0.1",
            server_port=available_port,
            share=True,  # 启用Gradio内置分享功能作为备选
            inbrowser=True,
            show_error=True,
            quiet=False
        )
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    finally:
        # 清理Ngrok隧道
        if public_url:
            try:
                ngrok.disconnect(public_url)
                print("🔌 Ngrok隧道已断开")
            except:
                pass

if __name__ == "__main__":
    main()