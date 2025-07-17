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
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODEL_CONFIG, UI_CONFIG
from utils.output_cleaner import output_cleaner
from utils.logger import get_logger

logger = get_logger(__name__)

# 对话历史管理
CONVERSATION_HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversation_history.json')

class ConversationManager:
    @staticmethod
    def load_history():
        """加载对话历史"""
        if not os.path.exists(CONVERSATION_HISTORY_PATH):
            return []
        try:
            with open(CONVERSATION_HISTORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载对话历史失败: {e}")
            return []

    @staticmethod
    def save_history(history):
        """保存对话历史"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(CONVERSATION_HISTORY_PATH), exist_ok=True)
            with open(CONVERSATION_HISTORY_PATH, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")

    @staticmethod
    def add_conversation(question, answer, function_type, image_path=False):
        """添加新对话"""
        history = ConversationManager.load_history()
        
        # 生成唯一ID
        conversation_id = f"{int(time.time() * 1000)}_{len(history)}"
        
        new_conversation = {
            "id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "function_type": function_type,
            "image_path": image_path,
            "question_length": len(question),
            "answer_length": len(answer)
        }
        history.append(new_conversation)
        
        # 限制历史记录数量为200条（增加容量）
        if len(history) > 200:
            history = history[-200:]
        ConversationManager.save_history(history)
        return conversation_id

    @staticmethod
    def clear_history():
        """清除对话历史"""
        ConversationManager.save_history([])
        logger.info("对话历史已清除")

    @staticmethod
    def delete_conversation(conversation_id):
        """删除指定对话"""
        history = ConversationManager.load_history()
        history = [item for item in history if item.get('id') != conversation_id]
        ConversationManager.save_history(history)
        logger.info(f"已删除对话: {conversation_id}")

    @staticmethod
    def search_history(keyword):
        """搜索历史记录"""
        history = ConversationManager.load_history()
        results = []
        for item in history:
            if keyword.lower() in item['question'].lower() or keyword.lower() in item['answer'].lower():
                results.append(item)
        return results

    @staticmethod
    def get_conversation_by_id(conversation_id):
        """根据ID获取对话"""
        history = ConversationManager.load_history()
        for item in history:
            if item.get('id') == conversation_id:
                return item
        return None

    @staticmethod
    def format_history_for_display(history, show_function_type=True):
        """格式化历史记录用于显示"""
        formatted = []
        for i, item in enumerate(reversed(history)):  # 最新的在前面
            time_str = datetime.fromisoformat(item['timestamp']).strftime('%m-%d %H:%M')
            question = item['question'][:40] + '...' if len(item['question']) > 40 else item['question']
            
            # 添加功能类型标识
            function_icon = {
                "智能问答": "💬",
                "化学计算": "🧮",
                "信息检索": "🔍",
                "LangChain处理": "🔗"
            }.get(item.get('function_type', ''), "❓")
            
            # 添加图片标识
            image_icon = "🖼️" if item.get('image_path') else ""
            
            if show_function_type:
                display_text = f"{function_icon}{image_icon}[{time_str}] {question}"
            else:
                display_text = f"[{time_str}] {question}"
                
            formatted.append(display_text)
        return formatted

    @staticmethod
    def get_statistics():
        """获取历史记录统计信息"""
        history = ConversationManager.load_history()
        if not history:
            return "暂无历史记录"
        
        total_count = len(history)
        function_stats = {}
        for item in history:
            func_type = item.get('function_type', '未知')
            function_stats[func_type] = function_stats.get(func_type, 0) + 1
        
        stats_text = f"总对话数: {total_count}\n"
        for func_type, count in function_stats.items():
            stats_text += f"{func_type}: {count}次\n"
        
        return stats_text.strip()

def update_loading_status(status):
    """更新加载状态"""
    return f"<div style='text-align: center; color: #666;'>{status}</div>"

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
    cleaned_text = re.sub(r'\\ce\{([^}]+)\}', r'\1', cleaned_text)
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
    
    def process_question(question, function_choice, image=None, progress=gr.Progress()):
        """处理用户问题，带加载状态"""
        progress(0, desc="开始处理...")
        time.sleep(0.5)  # 给进度条显示时间
    
        if not question.strip() and image is None:
            progress(1, desc="处理完成")
            return "请输入问题或上传图片", "", ""
    
        if controller is None:
            progress(1, desc="处理完成")
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
            progress(0.3, desc="正在处理问题...")
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

            progress(0.7, desc="正在格式化结果...")
            # 使用统一的清理函数处理所有输出
            cleaned_answer = clean_and_format_output(answer)
            cleaned_comparison = clean_and_format_output(comp)
            cleaned_chain_result = clean_and_format_output(chain)

            # 保存对话历史
            ConversationManager.add_conversation(question, cleaned_answer, function_choice, bool(image))

            progress(1, desc="处理完成")
            return cleaned_answer, cleaned_comparison, cleaned_chain_result
        except Exception as e:
            logger.error(f"处理问题时发生错误: {e}", exc_info=True)
            progress(1, desc="处理失败")
            return f"处理过程中发生错误: {e}", "", ""

    def on_clear_conversation():
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
                clear_btn = gr.Button("清除当前对话")

        with gr.Column(scale=1):
            gr.Markdown("### 📚 历史对话管理")
            
            # 搜索功能
            with gr.Row():
                search_input = gr.Textbox(
                    placeholder="搜索历史对话...",
                    label="搜索",
                    scale=3
                )
                search_btn = gr.Button("🔍", scale=1, size="sm")
            
            # 历史记录列表
            history_list = gr.Dropdown(
                choices=ConversationManager.format_history_for_display(ConversationManager.load_history()),
                label="历史对话列表",
                interactive=True,
                max_choices=50
            )
            
            # 操作按钮
            with gr.Row():
                load_history_btn = gr.Button("📥 加载", variant="primary", scale=1)
                view_history_btn = gr.Button("👁️ 查看", variant="secondary", scale=1)
                delete_history_btn = gr.Button("🗑️ 删除", variant="secondary", scale=1)
            
            with gr.Row():
                refresh_history_btn = gr.Button("🔄 刷新", scale=1)
                clear_history_btn = gr.Button("🧹 清空", variant="stop", scale=1)
            
            # 历史记录详细内容显示区域
            with gr.Accordion("📖 历史记录详细内容", open=False):
                history_detail_display = gr.Markdown(
                    value="选择一个历史记录并点击'查看'按钮来显示详细内容",
                    label="详细内容"
                )
            
            # 统计信息
            with gr.Accordion("📊 统计信息", open=False):
                stats_display = gr.Textbox(
                    value=ConversationManager.get_statistics(),
                    label="历史记录统计",
                    interactive=False,
                    lines=4
                )
            
            # 状态显示
            history_status = gr.Textbox(
                label="操作状态", 
                interactive=False, 
                visible=True,
                lines=2
            )
        
        # 历史对话相关事件处理函数
        def load_selected_history(history_index):
            """加载选中的历史对话"""
            if not history_index:
                return "", None, "请选择一个历史对话"
            
            try:
                # 解析时间戳（新格式：mm-dd HH:MM）
                time_str = history_index.split(']')[0].split('[')[1]
                history = ConversationManager.load_history()
                
                for item in reversed(history):  # 从最新的开始查找
                    item_time = datetime.fromisoformat(item['timestamp']).strftime('%m-%d %H:%M')
                    if item_time == time_str:
                        # 检查是否有图片
                        image_to_load = None
                        if item.get('image_path'):
                            try:
                                # 这里可以添加图片加载逻辑
                                pass
                            except:
                                pass
                        
                        return item['question'], image_to_load, f"✅ 已加载历史对话\n功能类型: {item.get('function_type', '未知')}"
                
                return "", None, "❌ 未找到选中的对话"
            except Exception as e:
                return "", None, f"❌ 加载失败: {str(e)}"
        
        def view_selected_history(history_index):
            """查看选中历史对话的完整内容"""
            if not history_index:
                return "请选择一个历史对话", "", ""
            
            try:
                # 解析时间戳（新格式：mm-dd HH:MM）
                time_str = history_index.split(']')[0].split('[')[1]
                history = ConversationManager.load_history()
                
                for item in reversed(history):  # 从最新的开始查找
                    item_time = datetime.fromisoformat(item['timestamp']).strftime('%m-%d %H:%M')
                    if item_time == time_str:
                        # 格式化显示内容
                        full_time = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 构建完整的历史记录显示
                        history_content = f"""## 📝 历史对话详情

**时间**: {full_time}
**功能类型**: {item.get('function_type', '未知')}
**问题长度**: {item.get('question_length', len(item['question']))} 字符
**答案长度**: {item.get('answer_length', len(item['answer']))} 字符
**包含图片**: {'是' if item.get('image_path') else '否'}

---

### 🤔 用户问题:
{item['question']}

---

### 🤖 AI回答:
{item['answer']}

---

*💡 提示: 您可以点击"加载到输入框"按钮将此问题重新加载到输入框中进行修改或重新提问。*"""
                        
                        return history_content, "", "✅ 历史对话内容已显示"
                
                return "❌ 未找到选中的对话", "", "未找到对话"
            except Exception as e:
                return f"❌ 查看失败: {str(e)}", "", f"查看失败: {str(e)}"

        def delete_selected_history(history_index):
            """删除选中的历史对话"""
            if not history_index:
                return update_history_list(), update_stats(), "请选择要删除的对话"
            
            try:
                # 解析时间戳找到对应的对话ID
                time_str = history_index.split(']')[0].split('[')[1]
                history = ConversationManager.load_history()
                
                for item in reversed(history):
                    item_time = datetime.fromisoformat(item['timestamp']).strftime('%m-%d %H:%M')
                    if item_time == time_str:
                        ConversationManager.delete_conversation(item.get('id'))
                        new_choices = ConversationManager.format_history_for_display(ConversationManager.load_history())
                        new_stats = ConversationManager.get_statistics()
                        return new_choices, new_stats, "✅ 对话已删除"
                
                return update_history_list(), update_stats(), "❌ 未找到要删除的对话"
            except Exception as e:
                return update_history_list(), update_stats(), f"❌ 删除失败: {str(e)}"

        def search_history_conversations(keyword):
            """搜索历史对话"""
            if not keyword.strip():
                # 如果搜索关键词为空，显示所有历史记录
                all_history = ConversationManager.load_history()
                choices = ConversationManager.format_history_for_display(all_history)
                return choices, f"显示所有 {len(all_history)} 条记录"
            
            try:
                results = ConversationManager.search_history(keyword.strip())
                choices = ConversationManager.format_history_for_display(results)
                return choices, f"🔍 找到 {len(results)} 条匹配记录"
            except Exception as e:
                return [], f"❌ 搜索失败: {str(e)}"

        def clear_all_history():
            """清除所有历史记录"""
            try:
                ConversationManager.clear_history()
                return [], "暂无历史记录", "✅ 所有历史记录已清除"
            except Exception as e:
                return update_history_list(), update_stats(), f"❌ 清除失败: {str(e)}"

        def update_history_list():
            """更新历史记录列表"""
            try:
                history = ConversationManager.load_history()
                choices = ConversationManager.format_history_for_display(history)
                return choices
            except Exception as e:
                logger.error(f"更新历史列表失败: {e}")
                return []

        def update_stats():
            """更新统计信息"""
            try:
                return ConversationManager.get_statistics()
            except Exception as e:
                logger.error(f"更新统计信息失败: {e}")
                return "统计信息获取失败"

        def refresh_history_and_stats():
            """刷新历史记录和统计信息"""
            try:
                new_choices = update_history_list()
                new_stats = update_stats()
                return new_choices, new_stats, "🔄 已刷新历史记录"
            except Exception as e:
                return update_history_list(), update_stats(), f"❌ 刷新失败: {str(e)}"

        # 绑定历史记录相关事件
        load_history_btn.click(
            fn=load_selected_history,
            inputs=[history_list],
            outputs=[question_input, image_input, history_status]
        )

        view_history_btn.click(
            fn=view_selected_history,
            inputs=[history_list],
            outputs=[history_detail_display, answer_output, history_status]
        )

        delete_history_btn.click(
            fn=delete_selected_history,
            inputs=[history_list],
            outputs=[history_list, stats_display, history_status]
        )

        search_btn.click(
            fn=search_history_conversations,
            inputs=[search_input],
            outputs=[history_list, history_status]
        )

        # 搜索框回车事件
        search_input.submit(
            fn=search_history_conversations,
            inputs=[search_input],
            outputs=[history_list, history_status]
        )

        refresh_history_btn.click(
            fn=refresh_history_and_stats,
            inputs=[],
            outputs=[history_list, stats_display, history_status]
        )

        clear_history_btn.click(
            fn=clear_all_history,
            inputs=[],
            outputs=[history_list, stats_display, history_status]
        )

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
        
        # 主要功能事件绑定
        def submit_and_refresh(question, function_choice, image):
            """提交问题并刷新历史记录"""
            # 处理问题
            answer, comparison, chain_result = process_question(question, function_choice, image)
            
            # 刷新历史记录和统计
            new_choices = update_history_list()
            new_stats = update_stats()
            
            return answer, comparison, chain_result, new_choices, new_stats

        submit_btn.click(
            fn=submit_and_refresh,
            inputs=[question_input, function_choice, image_input],
            outputs=[answer_output, comparison_output, chain_result_output, history_list, stats_display]
        )
        
        question_input.submit(
            fn=submit_and_refresh,
            inputs=[question_input, function_choice, image_input],
            outputs=[answer_output, comparison_output, chain_result_output, history_list, stats_display]
        )
        
        clear_btn.click(
            fn=lambda: ("", None, "", "", "", "🧹 当前对话已清除"),
            outputs=[question_input, image_input, answer_output, comparison_output, chain_result_output, history_status]
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