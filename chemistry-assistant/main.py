#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学助手启动入口
支持CLI或Web模式启动
"""

import argparse
from core.controller import Controller
from ui.app_gradio import start_ui
from config import MODEL_CONFIG

def main():
    parser = argparse.ArgumentParser(description='Chemistry Assistant')
    parser.add_argument('--mode', type=str, default='web', choices=['cli', 'web'],
                        help='启动模式: cli或web (默认: web)')
    parser.add_argument('--model', type=str, default='local_model',
                        choices=['local_model', 'openai', 'zhipu', 'claude', 'tongyi'],
                        help='使用的模型: local_model, openai, zhipu, claude, tongyi (默认: local_model)')
    args = parser.parse_args()
    
    # 尝试初始化Controller，如果失败则使用None
    try:
        controller = Controller()
        print("Controller初始化成功")
    except Exception as e:
        print(f"Controller初始化失败: {e}")
        print("将使用简化模式启动界面")
        controller = None
    
    # 检查选择的模型是否有API密钥（本地模型除外）
    if controller and args.model != 'local_model' and not MODEL_CONFIG.get(args.model, {}).get("api_key", ""):
        print(f"警告: 所选模型 {args.model} 没有配置API密钥，将使用本地模型代替。")
        args.model = 'local_model'
    
    if args.mode == 'cli':
        # CLI模式
        print(f"启动CLI模式...使用模型: {args.model}")
        print("提示: 输入'multimodal'可切换到多模态模式，输入'exit'退出")
        
        multimodal_mode = False
        
        while True:
            if multimodal_mode:
                query = input("请输入问题或图片路径 (输入'normal'切换到普通模式，'exit'退出): ")
                if query.lower() == 'exit':
                    break
                elif query.lower() == 'normal':
                    multimodal_mode = False
                    print("已切换到普通模式")
                    continue
                
                # 检查是否为图片路径
                if query.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        with open(query, 'rb') as f:
                            image_data = f.read()
                        response = controller.process_multimodal_input(image_data, 'image')
                    except FileNotFoundError:
                        print(f"错误: 找不到图片文件 {query}")
                        continue
                    except Exception as e:
                        print(f"错误: 读取图片失败 - {str(e)}")
                        continue
                else:
                    response = controller.process_multimodal_input(query, 'text')
                
                print(f"多模态回答: {response}")
            else:
                query = input("请输入问题 (输入'multimodal'切换到多模态模式，'exit'退出): ")
                if query.lower() == 'exit':
                    break
                elif query.lower() == 'multimodal':
                    multimodal_mode = True
                    print("已切换到多模态模式")
                    continue
                
                task_info = {"preferred_model": args.model}
                response = controller.process_query(query, task_info)
                print(f"回答: {response}")
    else:
        # Web模式
        print("启动Web界面...")
        start_ui(controller)

if __name__ == "__main__":
    main()