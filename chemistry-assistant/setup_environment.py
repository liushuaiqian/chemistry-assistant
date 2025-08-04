#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境设置和依赖检查脚本
"""

import subprocess
import sys
import os

def check_python_version():
    """
    检查Python版本
    """
    print("🔍 检查Python版本...")
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    else:
        print("✅ Python版本符合要求")
        return True

def install_package(package_name):
    """
    安装Python包
    """
    try:
        print(f"📦 安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def check_and_install_dependencies():
    """
    检查并安装依赖
    """
    print("\n🔍 检查依赖包...")
    
    # 基础依赖列表
    basic_deps = [
        "torch",
        "transformers", 
        "sentence-transformers",
        "faiss-cpu",
        "gradio",
        "requests",
        "numpy",
        "pandas"
    ]
    
    missing_deps = []
    
    for dep in basic_deps:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"❌ {dep} 未安装")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n📦 需要安装 {len(missing_deps)} 个依赖包...")
        for dep in missing_deps:
            install_package(dep)
    else:
        print("\n✅ 所有基础依赖都已安装")
    
    return len(missing_deps) == 0

def install_requirements():
    """
    从requirements.txt安装依赖
    """
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        print(f"\n📦 从 {requirements_file} 安装依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
            print("✅ requirements.txt 依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ requirements.txt 安装失败: {e}")
            return False
    else:
        print(f"⚠️ 未找到 {requirements_file} 文件")
        return False

def create_conda_environment():
    """
    创建conda环境的建议
    """
    print("\n💡 建议创建独立的conda环境:")
    print("conda create -n chemistry-assistant python=3.9")
    print("conda activate chemistry-assistant")
    print("pip install -r requirements.txt")

def check_api_keys():
    """
    检查API密钥配置
    """
    print("\n🔍 检查API密钥配置...")
    
    try:
        from config import MODEL_CONFIG
        
        api_keys = {
            'zhipu': MODEL_CONFIG.get('zhipu', {}).get('api_key', ''),
            'tongyi': MODEL_CONFIG.get('tongyi', {}).get('api_key', ''),
            'claude': MODEL_CONFIG.get('claude', {}).get('api_key', '')
        }
        
        configured_keys = 0
        for provider, key in api_keys.items():
            if key and key.strip() and not key.startswith('your_'):
                print(f"✅ {provider} API密钥已配置")
                configured_keys += 1
            else:
                print(f"⚠️ {provider} API密钥未配置")
        
        if configured_keys > 0:
            print(f"✅ 已配置 {configured_keys} 个API密钥")
            return True
        else:
            print("❌ 未配置任何API密钥")
            return False
            
    except Exception as e:
        print(f"❌ 检查API密钥时出错: {e}")
        return False

def create_minimal_startup():
    """
    创建最小化启动脚本
    """
    print("\n🔧 创建最小化启动脚本...")
    
    minimal_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小化启动脚本 - 仅启动核心功能
"""

import os
import sys

# 修复OpenMP库冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("🚀 启动最小化化学助手...")
    
    # 仅导入必要模块
    import gradio as gr
    from config import MODEL_CONFIG
    
    def simple_chat(message):
        """简单的聊天功能"""
        return f"收到消息: {message}\n\n这是最小化模式，完整功能需要安装所有依赖。"
    
    # 创建简单界面
    with gr.Blocks(title="化学助手 - 最小化模式") as demo:
        gr.Markdown("# 🧪 化学助手 (最小化模式)")
        gr.Markdown("⚠️ 当前运行在最小化模式，请安装完整依赖以使用所有功能")
        
        with gr.Row():
            with gr.Column():
                message_input = gr.Textbox(label="输入消息", placeholder="请输入您的问题...")
                submit_btn = gr.Button("发送", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(label="回复", lines=10)
        
        submit_btn.click(simple_chat, inputs=[message_input], outputs=[output])
        message_input.submit(simple_chat, inputs=[message_input], outputs=[output])
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False,
        inbrowser=True
    )
    
except Exception as e:
    print(f"❌ 最小化启动也失败: {e}")
    print("\n🔍 请检查:")
    print("1. 是否安装了gradio: pip install gradio")
    print("2. 是否在正确的目录中运行")
    print("3. Python环境是否正确")
    
    import traceback
    traceback.print_exc()
'''
    
    with open('./start_minimal.py', 'w', encoding='utf-8') as f:
        f.write(minimal_content)
    
    print("✅ 最小化启动脚本已创建: start_minimal.py")

def main():
    """
    主函数
    """
    print("🔧 化学助手环境设置向导\n")
    
    # 检查Python版本
    if not check_python_version():
        return
    
    # 检查并安装依赖
    print("\n" + "="*50)
    choice = input("是否要安装依赖包? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes', '是']:
        # 先尝试从requirements.txt安装
        if not install_requirements():
            # 如果失败，尝试安装基础依赖
            check_and_install_dependencies()
    
    # 检查API密钥
    check_api_keys()
    
    # 创建最小化启动脚本
    create_minimal_startup()
    
    # 显示conda环境建议
    create_conda_environment()
    
    print("\n" + "="*50)
    print("✅ 环境设置完成！")
    print("\n📋 启动选项:")
    print("1. 完整模式: python start_safe.py")
    print("2. 最小化模式: python start_minimal.py")
    print("3. 原始模式: python main.py")
    
if __name__ == "__main__":
    main()