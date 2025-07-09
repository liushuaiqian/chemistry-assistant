# -*- coding: utf-8 -*-
"""
测试Gradio界面
"""

import gradio as gr

def simple_chat(message, history):
    """
    简单的聊天函数
    """
    if not message.strip():
        return "请输入问题"
    
    # 简单的回复逻辑
    if "摩尔质量" in message or "分子量" in message:
        return f"正在计算摩尔质量...\n您的问题：{message}\n这是一个化学计算问题，需要具体的化学式才能计算。"
    elif "平衡" in message:
        return f"正在平衡化学方程式...\n您的问题：{message}\n这是一个化学方程式平衡问题。"
    elif "什么是" in message:
        return f"正在查询相关信息...\n您的问题：{message}\n这是一个知识查询问题。"
    else:
        return f"收到您的问题：{message}\n这是化学助手的测试回复。系统正在处理您的问题..."

def process_question(question, model_choice, function_choice, image=None):
    """
    处理用户问题
    """
    if not question.strip():
        return "请输入问题"
    
    result = f"**模型**: {model_choice}\n"
    result += f"**功能**: {function_choice}\n"
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

# 创建Gradio界面
with gr.Blocks(title="🧪 化学助手测试", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧪 化学助手 (测试版)")
    gr.Markdown("基于AI的化学学习辅助系统测试界面")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 设置")
            
            # 模型选择
            model_choice = gr.Dropdown(
                choices=["本地模型", "OpenAI", "智谱AI", "Claude", "通义大模型"],
                value="本地模型",
                label="选择模型"
            )
            
            # 功能选择
            function_choice = gr.Radio(
                choices=["智能问答", "化学计算", "信息检索"],
                value="智能问答",
                label="功能类型"
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
            answer_output = gr.Textbox(
                label="回答",
                lines=10,
                max_lines=20,
                interactive=False
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
    
    # 事件绑定
    submit_btn.click(
        fn=process_question,
        inputs=[question_input, model_choice, function_choice, image_input],
        outputs=answer_output
    )
    
    # 回车提交
    question_input.submit(
        fn=process_question,
        inputs=[question_input, model_choice, function_choice, image_input],
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

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )