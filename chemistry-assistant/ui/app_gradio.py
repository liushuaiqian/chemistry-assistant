# -*- coding: utf-8 -*-
"""
Gradio Web界面
"""

import gradio as gr
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODEL_CONFIG, UI_CONFIG

def start_ui(controller=None):
    """
    启动Gradio Web界面
    
    Args:
        controller: 主控制器实例（可选）
    """
    
    def process_question(question, function_choice, image=None):
        """
        处理用户问题
        """
        if not question.strip():
            return "请输入问题"
        
        # 如果controller为None，使用简单的回复逻辑
        if controller is None:
            result = f"**功能**: {function_choice}\n"
            result += f"**问题**: {question}\n\n"
            
            if image is not None:
                result += "**图像**: 已上传图像\n\n"
            
            # 根据功能类型给出不同回复
            if function_choice == "化学计算":
                if "摩尔质量" in question:
                    result += "正在计算摩尔质量...\n例如：H2O的摩尔质量 = 2×1.008 + 15.999 = 18.015 g/mol"
                elif "平衡" in question:
                    result += "正在平衡化学方程式...\n例如：2H2 + O2 → 2H2O"
                else:
                    result += "这是一个化学计算问题，请提供具体的计算要求。"
            elif function_choice == "信息检索":
                result += "正在检索相关信息...\n这里会显示从知识库检索到的相关信息。"
            else:
                result += "这是智能问答功能，我会尽力回答您的化学问题。"
            
            return result
        
        # 构建任务信息
        task_info = {}
        
        # 如果有图像，添加到任务信息中
        if image is not None:
            task_info["image"] = image
        
        # 根据功能类型调整问题
        if function_choice == "化学计算":
            if "摩尔质量" not in question and "平衡" not in question and "计算" not in question:
                question = f"化学计算：{question}"
        elif function_choice == "信息检索":
            if "查询" not in question and "检索" not in question:
                question = f"查询：{question}"
        
        try:
            response = controller.process_query(question, task_info)
            return response
        except Exception as e:
            return f"处理出错：{str(e)}"
    
    def get_available_models():
        """
        获取可用的模型列表
        """
        available_models = ["本地模型"]
        
        model_configs = {
            "OpenAI": "openai",
            "智谱AI": "zhipu", 
            "Claude": "claude",
            "通义大模型": "tongyi"
        }
        
        for model_name, model_key in model_configs.items():
            if MODEL_CONFIG.get(model_key, {}).get("api_key", ""):
                available_models.append(model_name)
        
        return available_models
    
    # 创建Gradio界面
    with gr.Blocks(title="🧪 化学助手", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🧪 化学助手")
        gr.Markdown("基于AI的化学学习辅助系统，帮助您理解化学概念、解决化学问题。")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 设置")
                

                
                # 功能选择
                function_choice = gr.Radio(
                    choices=["智能问答", "化学计算", "信息检索"],
                    value="智能问答",
                    label="功能类型",
                    info="选择要使用的功能"
                )
            
            with gr.Column(scale=3):
                gr.Markdown("### 对话界面")
                
                # 图像上传（可选）
                image_input = gr.Image(
                    label="上传图像（可选）",
                    type="pil",
                    height=200
                )
                
                # 问题输入
                question_input = gr.Textbox(
                    label="请输入您的问题",
                    placeholder="例如：计算H2O的摩尔质量、平衡化学方程式H2 + O2 = H2O等",
                    lines=3
                )
                
                # 提交按钮
                submit_btn = gr.Button("提交问题", variant="primary")
                
                # 回答输出
                answer_output = gr.Markdown(
                    label="回答"
                )
                
                # 清除按钮
                clear_btn = gr.Button("清除对话")
        
        # 示例问题
        gr.Markdown("### 💡 示例问题")
        with gr.Row():
            example_btns = [
                gr.Button("计算H2O的摩尔质量", size="sm"),
                gr.Button("平衡方程式：H2 + O2 = H2O", size="sm"),
                gr.Button("什么是化学键？", size="sm"),
                gr.Button("查询苯的性质", size="sm")
            ]
        
        # 系统信息
        with gr.Accordion("系统信息", open=False):
            gr.Markdown("""
            **版本**: 1.0.0  
            **功能**: 智能问答、化学计算、信息检索  
            **支持**: 多模型、多模态输入  
            **技术**: 多Agent架构，支持本地模型和外部API
            """)
        
        # 事件绑定
        submit_btn.click(
            fn=process_question,
            inputs=[question_input, function_choice, image_input],
            outputs=answer_output
        )
        
        # 回车提交
        question_input.submit(
            fn=process_question,
            inputs=[question_input, function_choice, image_input],
            outputs=answer_output
        )
        
        # 清除功能
        clear_btn.click(
            fn=lambda: ("", None),
            outputs=[question_input, answer_output]
        )
        
        # 示例问题点击事件
        example_btns[0].click(lambda: "计算H2O的摩尔质量", outputs=question_input)
        example_btns[1].click(lambda: "平衡化学方程式：H2 + O2 = H2O", outputs=question_input)
        example_btns[2].click(lambda: "什么是化学键？", outputs=question_input)
        example_btns[3].click(lambda: "查询苯的性质和用途", outputs=question_input)
    
    # 启动界面
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )
    
    return demo

if __name__ == "__main__":
    # 测试用的简单启动
    print("请通过main.py启动完整系统")