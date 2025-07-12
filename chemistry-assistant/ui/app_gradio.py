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
        if not question.strip() and image is None:
            return "请输入问题或上传图片", "", ""
        
        # 如果controller为None，使用简单的回复逻辑
        if controller is None:
            result = f"**功能**: {function_choice}\n"
            
            if image is not None:
                result += "**图像**: 已上传图像，但图像识别功能需要完整的系统支持\n\n"
                if not question.strip():
                    question = "请分析这张图片中的化学内容"
            
            result += f"**问题**: {question}\n\n"
            
            # 根据功能类型给出不同回复，并添加公式渲染示例
            if function_choice == "化学计算":
                if "摩尔质量" in question:
                    result += "正在计算摩尔质量...\n\n"
                    result += "例如：$H_2O$ 的摩尔质量计算：\n\n"
                    result += "$$M(H_2O) = 2 \\times M(H) + M(O) = 2 \\times 1.008 + 15.999 = 18.015 \\text{ g/mol}$$\n\n"
                elif "平衡" in question:
                    result += "正在平衡化学方程式...\n\n"
                    result += "例如：$H_2 + O_2 \\rightarrow H_2O$ 的配平：\n\n"
                    result += "$$2H_2 + O_2 \\rightarrow 2H_2O$$\n\n"
                else:
                    result += "这是一个化学计算问题，请提供具体的计算要求。\n\n"
                    result += "支持的计算类型：\n"
                    result += "- 摩尔质量：如 $M(NaCl) = 58.44 \\text{ g/mol}$\n"
                    result += "- 化学方程式配平\n"
                    result += "- 浓度计算等\n"
            elif function_choice == "信息检索":
                result += "正在检索相关信息...\n这里会显示从知识库检索到的相关信息。"
            elif function_choice == "LangChain处理":
                result += "正在使用LangChain进行链式处理...\n这里会显示链式推理的结果。"
            else:
                result += "这是智能问答功能，我会尽力回答您的化学问题。\n\n"
                result += "示例化学公式渲染：\n"
                result += "- 水分子：$H_2O$\n"
                result += "- 理想气体状态方程：$PV = nRT$\n"
                result += "- 化学反应：$CaCO_3 \\xrightarrow{\\Delta} CaO + CO_2 \\uparrow$\n"
            
            return result, "", ""
        
        # 构建任务信息
        task_info = {
            'function': function_choice
        }
        
        # 如果有图像，添加到任务信息中并处理图像输入
        if image is not None:
            task_info["image"] = image
            # 如果没有文本问题，设置默认的图像分析问题
            if not question.strip():
                question = "请分析这张图片中的化学内容，包括化学方程式、分子结构、实验装置等。"
        
        # 根据功能类型调整问题
        if function_choice == "化学计算":
            if "摩尔质量" not in question and "平衡" not in question and "计算" not in question:
                question = f"化学计算：{question}"
        elif function_choice == "信息检索":
            if "查询" not in question and "检索" not in question:
                question = f"查询：{question}"
        
        try:
            # 根据选择的功能进行处理
            if function_choice == "LangChain处理":
                # 使用LangChain链式处理，传递图像数据和功能类型
                response, comparison, chain_result = controller.process_with_chain(
                    question, 
                    function_type=function_choice, 
                    image_data=image
                )
                
                # 格式化链式处理结果
                chain_info = ""
                if chain_result and 'chain_summary' in chain_result:
                    chain_info = chain_result['chain_summary']
                
                # 清理编码问题
                def clean_output(text):
                    if not isinstance(text, str):
                        text = str(text)
                    # 移除控制字符和乱码
                    import re
                    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
                    # 确保UTF-8编码正确
                    try:
                        text = text.encode('utf-8').decode('utf-8')
                    except UnicodeError:
                        text = ''.join(char for char in text if ord(char) < 65536)
                    return text
                
                return clean_output(response), clean_output(comparison), clean_output(chain_info)
                
            else:
                # 使用传统处理方式
                response, comparison = controller.process_query(question, task_info)
                return response, comparison, ""
                
        except Exception as e:
            return f"处理出错：{str(e)}", "", ""
    

    
    # 创建Gradio界面
    with gr.Blocks(
        title="🧪 化学助手", 
        theme=gr.themes.Soft(),
        head="""
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
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
        
        // 重新渲染MathJax的函数
        function renderMathJax() {
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetPromise().catch(function (err) {
                    console.log('MathJax typeset failed: ' + err.message);
                });
            }
        }
        
        // 监听DOM变化，自动重新渲染数学公式
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
        
        // 开始观察
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
                

                

                
                # 功能选择
                function_choice = gr.Radio(
                    choices=["智能问答", "化学计算", "信息检索", "LangChain处理"],
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

                # 对比分析输出
                comparison_output = gr.Markdown(
                    label="模型答案对比分析"
                )
                
                # LangChain链式处理结果输出
                chain_result_output = gr.Markdown(
                    label="LangChain链式分析结果"
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
            **功能**: 智能问答、化学计算、信息检索、LangChain处理  
            **支持**: 多模型、多模态输入、链式推理  
            **技术**: 多Agent架构，支持本地模型、外部API和LangChain
            """)
        
        # 事件绑定
        submit_btn.click(
            fn=process_question,
            inputs=[question_input, function_choice, image_input],
            outputs=[answer_output, comparison_output, chain_result_output]
        )
        
        # 回车提交
        question_input.submit(
            fn=process_question,
            inputs=[question_input, function_choice, image_input],
            outputs=[answer_output, comparison_output, chain_result_output]
        )
        
        # 清除功能
        clear_btn.click(
            fn=lambda: ("", None, "", "", ""),
            outputs=[question_input, image_input, answer_output, comparison_output, chain_result_output]
        )
        
        # 示例问题点击事件
        example_btns[0].click(lambda: "计算H2O的摩尔质量", outputs=question_input)
        example_btns[1].click(lambda: "平衡化学方程式：H2 + O2 = H2O", outputs=question_input)
        example_btns[2].click(lambda: "什么是化学键？", outputs=question_input)
        example_btns[3].click(lambda: "查询苯的性质和用途", outputs=question_input)
    
    # 启动界面
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        inbrowser=True
    )
    
    return demo

if __name__ == "__main__":
    # 测试用的简单启动
    print("请通过main.py启动完整系统")