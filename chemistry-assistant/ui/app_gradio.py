# -*- coding: utf-8 -*-
"""
Gradio Web界面
"""

import gradio as gr
import sys
import os
import json
import ast
import re

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODEL_CONFIG, UI_CONFIG
from utils.output_cleaner import output_cleaner

def clean_and_format_output(raw_output):
    """
    一个统一的函数，用于清理、解析和格式化模型的原始输出。
    """
    if not raw_output:
        return ""

    # 1. 解析输入：处理JSON字符串、Python字面量或普通字符串
    data = None
    if isinstance(raw_output, str):
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, TypeError):
            try:
                data = ast.literal_eval(raw_output)
            except (ValueError, SyntaxError, TypeError):
                data = raw_output # 保持为字符串
    else:
        data = raw_output

    # 2. 提取核心答案
    answer = data
    if isinstance(data, dict):
        answer = data.get('integrated_answer') or data.get('answer') or data.get('error') or data.get('solution') or data

    # 3. 格式化答案以供显示
    if isinstance(answer, dict):
        # 如果是字典，美化为JSON字符串
        formatted_answer = f"```json\n{json.dumps(answer, indent=2, ensure_ascii=False)}\n```"
    elif isinstance(answer, list):
        # 如果是列表，每项占一行
        formatted_answer = "\n".join(map(str, answer))
    else:
        # 其他情况，转为字符串
        formatted_answer = str(answer)

    # 4. 清理最终的文本
    # 使用专业的输出清理器
    cleaned_text = output_cleaner.clean_model_response(formatted_answer)
    
    # 额外的乱码和格式修复
    cleaned_text = re.sub(r'\Double subscripts: use braces to clarify', '', cleaned_text)
    cleaned_text = re.sub(r'Extra close brace or missing open brace', '', cleaned_text)
    cleaned_text = re.sub(r'\ce\{([^}]+)\}', r'\1', cleaned_text)
    cleaned_text = re.sub(r'\$+([^$]*?)\$+', r'$\1$', cleaned_text)
    cleaned_text = re.sub(r'H2O', r'H₂O', cleaned_text)
    cleaned_text = re.sub(r'O2', r'O₂', cleaned_text)
    cleaned_text = re.sub(r'H2', r'H₂', cleaned_text)
    cleaned_text = re.sub(r'CO2', r'CO₂', cleaned_text)
    cleaned_text = re.sub(r'SO2', r'SO₂', cleaned_text)
    cleaned_text = re.sub(r'NO2', r'NO₂', cleaned_text)
    cleaned_text = re.sub(r'\rightarrow', r'→', cleaned_text)
    cleaned_text = re.sub(r'\to', r'→', cleaned_text)
    cleaned_text = re.sub(r'->', r'→', cleaned_text)

    # 确保UTF-8编码正确
    try:
        cleaned_text = cleaned_text.encode('utf-8').decode('utf-8')
    except UnicodeError:
        cleaned_text = ''.join(char for char in cleaned_text if ord(char) < 65536)

    return cleaned_text

def start_ui(controller=None):
    """
    启动Gradio Web界面
    """
    
    def process_question(question, function_choice, image=None):
        """
        处理用户问题
        """
        if not question.strip() and image is None:
            return "请输入问题或上传图片", "", ""
        
        if controller is None:
            # ... (省略了演示模式的代码，因为它不涉及核心逻辑)
            return "演示模式，请通过 main.py 启动完整系统。", "", ""
        
        # 构建任务信息
        task_info = {
            'function': function_choice
        }
        
        if image is not None:
            task_info["image"] = image
            if not question.strip():
                question = "请分析这张图片中的化学内容，包括化学方程式、分子结构、实验装置等。"
        
        try:
            if function_choice == "LangChain处理":
                response, comparison, chain_result = controller.process_with_chain(
                    question, 
                    function_type="智能问答",
                    image_data=image
                )
                answer = response
                comp = comparison
                chain = chain_result
            else:
                response, comparison = controller.process_query(question, task_info)
                answer = response
                comp = comparison
                chain = ""

            # 使用统一的清理函数处理所有输出
            cleaned_answer = clean_and_format_output(answer)
            cleaned_comparison = clean_and_format_output(comp)
            cleaned_chain_result = clean_and_format_output(chain)

            return cleaned_answer, cleaned_comparison, cleaned_chain_result
                
        except Exception as e:
            return f"处理出错：{str(e)}", "", ""
    
    # 创建Gradio界面
    with gr.Blocks(
        title="🧪 化学助手", 
        theme=gr.themes.Soft(),
        head="""
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>
        <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                processEnvironments: true,
                packages: {'[+]': ['mhchem']}
            },
            loader: {
                load: ['[tex]/mhchem']
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }
        };
        
        function renderMathJax() {
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetPromise().catch(function (err) {
                    console.log('MathJax typeset failed: ' + err.message);
                });
            }
        }
        
        const observer = new MutationObserver(function(mutations) {
            let shouldRender = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    for (let node of mutation.addedNodes) {
                        if (node.nodeType === 1 && (node.textContent.includes('$') || node.textContent.includes('\\('))) {
                            shouldRender = true;
                            break;
                        }
                    }
                }
            });
            if (shouldRender) {
                setTimeout(renderMathJax, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        </script>
        """
    ) as demo:
        gr.Markdown("# 🧪 化学助手")
        gr.Markdown("基于AI的化学学习辅助系统，帮助您理解化学概念、解决化学问题。支持数学公式渲染和图片识别。")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 设置")
                function_choice = gr.Radio(
                    choices=["智能问答", "化学计算", "信息检索", "LangChain处理"],
                    value="智能问答",
                    label="功能类型",
                    info="选择要使用的功能"
                )
            
            with gr.Column(scale=3):
                gr.Markdown("### 对话界面")
                image_input = gr.Image(label="上传图像（可选）", type="pil", height=200)
                question_input = gr.Textbox(label="请输入您的问题", placeholder="例如：计算H2O的摩尔质量", lines=3)
                submit_btn = gr.Button("提交问题", variant="primary")
                answer_output = gr.Markdown(label="回答")
                comparison_output = gr.Markdown(label="模型答案对比分析")
                chain_result_output = gr.Markdown(label="LangChain链式分析结果")
                clear_btn = gr.Button("清除对话")
        
        gr.Markdown("### 💡 示例问题")
        with gr.Row():
            example_btns = [
                gr.Button("计算H2O的摩尔质量", size="sm"),
                gr.Button("平衡方程式：H2 + O2 = H2O", size="sm"),
                gr.Button("什么是化学键？", size="sm"),
                gr.Button("查询苯的性质", size="sm")
            ]
        
        with gr.Accordion("系统信息", open=False):
            gr.Markdown("""
            **版本**: 1.0.0  
            **功能**: 智能问答、化学计算、信息检索、LangChain处理  
            **支持**: 多模型、多模态输入、链式推理  
            **技术**: 多Agent架构，支持本地模型、外部API和LangChain
            """)
        
        submit_btn.click(
            fn=process_question,
            inputs=[question_input, function_choice, image_input],
            outputs=[answer_output, comparison_output, chain_result_output]
        )
        
        question_input.submit(
            fn=process_question,
            inputs=[question_input, function_choice, image_input],
            outputs=[answer_output, comparison_output, chain_result_output]
        )
        
        clear_btn.click(
            fn=lambda: ("", None, "", "", ""),
            outputs=[question_input, image_input, answer_output, comparison_output, chain_result_output]
        )
        
        example_btns[0].click(lambda: "计算H2O的摩尔质量", outputs=question_input)
        example_btns[1].click(lambda: "平衡化学方程式：H2 + O2 = H2O", outputs=question_input)
        example_btns[2].click(lambda: "什么是化学键？", outputs=question_input)
        example_btns[3].click(lambda: "查询苯的性质和用途", outputs=question_input)
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        inbrowser=True
    )
    
    return demo

if __name__ == "__main__":
    print("请通过main.py启动完整系统")