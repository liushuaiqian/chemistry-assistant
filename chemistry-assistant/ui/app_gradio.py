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
import socket
from datetime import datetime
from pyngrok import ngrok

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODEL_CONFIG, UI_CONFIG
from utils.output_cleaner import output_cleaner
from utils.unified_markdown_renderer import render_content, render_comparison_output, render_chain_result, render_error_message, render_status_message
from utils.logger import get_logger
from ui.performance_monitor import get_performance_monitor

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
        """搜索历史记录（增强版模糊匹配）"""
        history = ConversationManager.load_history()
        results = []
        keyword = keyword.lower().strip()
        
        for item in history:
            # 多维度搜索：问题、答案、功能类型
            question_match = keyword in item['question'].lower()
            answer_match = keyword in item['answer'].lower()
            function_type_match = keyword in item.get('function_type', '').lower()
            
            # 支持部分词匹配
            question_words = item['question'].lower().split()
            keyword_words = keyword.split()
            word_match = any(any(kw in word for word in question_words) for kw in keyword_words)
            
            if question_match or answer_match or function_type_match or word_match:
                results.append(item)
        
        # 按时间排序，最新的在前
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results

    @staticmethod
    def format_history_for_display(history, show_function_type=True, max_length=35):
        """格式化历史记录用于显示（优化版）"""
        formatted = []
        for i, item in enumerate(reversed(history)):  # 最新的在前面
            time_str = datetime.fromisoformat(item['timestamp']).strftime('%m-%d %H:%M')
            
            # 智能截断问题文本
            question = item['question']
            if len(question) > max_length:
                # 尝试在单词边界截断
                truncated = question[:max_length]
                last_space = truncated.rfind(' ')
                if last_space > max_length * 0.7:  # 如果空格位置合理
                    question = truncated[:last_space] + '...'
                else:
                    question = truncated + '...'
            
            # 添加功能类型标识（更丰富的图标）
            function_icons = {
                "智能问答": "💬",
                "化学计算": "🧮", 
                "综合检索": "🔍",
                "信息检索": "📚",
                "LangChain处理": "🔗"
            }
            function_icon = function_icons.get(item.get('function_type', ''), "❓")
            
            # 添加图片和长度标识
            image_icon = "🖼️" if item.get('image_path') else ""
            length_indicator = "📝" if len(item.get('answer', '')) > 500 else ""
            
            if show_function_type:
                display_text = f"{function_icon}{image_icon}{length_indicator} [{time_str}] {question}"
            else:
                display_text = f"[{time_str}] {question}"
                
            formatted.append(display_text)
        return formatted

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

def start_ui(controller=None):
    """
    启动Gradio Web界面
    """
    
    async def process_question(question, function_choice, image=None, 
                        enable_local_rag=True, enable_metaso=True, enable_tongyi=True, enable_pubchem=True,
                        use_llm_summary=True, adaptive_enabled=False, show_complexity=True, show_strategy=True, progress=gr.Progress()):
        """处理用户问题，带加载状态"""
        progress(0, desc="开始处理...")
        time.sleep(0.5)  # 给进度条显示时间

        if not question.strip() and image is None:
            progress(1, desc="处理完成")
            return "请输入问题或上传图片", "", "", ""

        if controller is None:
            progress(1, desc="处理完成")
            return "演示模式，请通过 main.py 启动完整系统。", "", "", ""

        # 构建任务信息
        task_info = {
            'function': function_choice,
            'enable_local_rag': enable_local_rag,
            'enable_metaso': enable_metaso,
            'enable_tongyi': enable_tongyi,
            'enable_pubchem': enable_pubchem
        }

        if image is not None:
            task_info["image"] = image
            if not question.strip():
                question = "请分析这张图片中的化学内容，包括化学方程式、分子结构、实验装置等。"

        try:
            progress(0.3, desc="正在处理问题...")
            
            if function_choice == "综合检索":
                progress(0.4, desc="使用增强综合检索处理...")
                # 调用新的异步综合检索功能
                start_time = time.time()
                result = await controller.process_comprehensive_retrieval(
                    query=question,
                    enable_local_rag=enable_local_rag,
                    enable_metaso=enable_metaso,
                    enable_tongyi=enable_tongyi,
                    enable_pubchem=enable_pubchem,
                    use_llm_summary=use_llm_summary
                )
                total_time = time.time() - start_time
                
                if result.get('success'):
                    # 记录性能数据
                    monitor = get_performance_monitor()
                    successful_sources = [s['name'] for s in result.get('sources', []) if s.get('confidence', 0) > 0.1]
                    source_times = {s['name']: s.get('retrieval_time', 0.0) for s in result.get('sources', [])}
                    
                    monitor.record_performance(
                        query=question,
                        total_time=total_time,
                        confidence_score=result.get('confidence_score', 0.0),
                        sources_count=len(result.get('sources', [])),
                        successful_sources=successful_sources,
                        strategy_used="综合检索" + (" + LLM总结" if use_llm_summary else ""),
                        source_times=source_times
                    )
                    
                    answer = result.get('combined_answer', '未获取到回答')
                    # 构建详细的来源信息
                    sources_info = ""
                    if result.get('sources'):
                        sources_info = "\n\n### 📚 知识来源信息\n"
                        for i, source in enumerate(result['sources'], 1):
                            confidence_bar = "🟢" if source['confidence'] > 0.7 else "🟡" if source['confidence'] > 0.4 else "🔴"
                            sources_info += f"**{i}. {source['name']}** {confidence_bar}\n"
                            sources_info += f"- 置信度: {source['confidence']:.2f}\n"
                            sources_info += f"- 检索时间: {source['retrieval_time']:.2f}秒\n"
                            if source['content']:
                                sources_info += f"- 内容摘要: {source['content']}\n\n"
                    
                    # 添加性能统计信息
                    performance_info = f"\n\n### ⚡ 性能统计\n"
                    performance_info += f"- 总耗时: {total_time:.2f}秒\n"
                    performance_info += f"- 整体置信度: {result.get('confidence_score', 0):.2f}\n"
                    performance_info += f"- 检索策略: {result.get('strategy', '未知')}\n"
                    
                    answer = answer + sources_info + performance_info
                    comp = "综合检索模式：已整合多个知识源的信息"
                else:
                    answer = f"综合检索失败: {result.get('error', '未知错误')}"
                    comp = "检索过程中发生错误"
                
                chain = ""
            elif function_choice == "LangChain处理":
                progress(0.4, desc="使用LangChain处理...")
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
            # 使用统一渲染器处理不同类型的输出
            cleaned_answer = render_content(answer)
            cleaned_comparison = render_comparison_output(comp)
            cleaned_chain_result = render_chain_result(chain)
            
            # 构建自适应状态信息
            if adaptive_enabled and hasattr(controller, 'get_last_retrieval_info'):
                progress(0.9, desc="准备状态信息...")
                try:
                    retrieval_info = controller.get_last_retrieval_info()
                    if retrieval_info:
                        status_details = f"""检索策略: {retrieval_info.get('strategy_used', '标准检索')}
响应时间: {retrieval_info.get('response_time', 0):.2f}秒"""
                        if show_complexity and retrieval_info.get('complexity_analysis'):
                            complexity = retrieval_info['complexity_analysis']
                            status_details += f"""
复杂度: {complexity.get('complexity', '未知')} (分数: {complexity.get('score', 0):.2f})"""
                        adaptive_status = render_status_message("处理完成", status_details)
                    else:
                        adaptive_status = render_status_message("处理完成", "使用标准处理流程")
                except Exception as status_error:
                    logger.warning(f"获取状态信息失败: {status_error}")
                    adaptive_status = render_status_message("处理完成")
            else:
                adaptive_status = render_status_message("处理完成")
            
            progress(1, desc="处理完成")
            
            # 保存对话历史
            try:
                ConversationManager.add_conversation(
                    question=question,
                    answer=cleaned_answer,
                    function_type=function_choice,
                    image_path=bool(image)
                )
            except Exception as save_error:
                logger.warning(f"保存对话历史失败: {save_error}")

            return cleaned_answer, cleaned_comparison, cleaned_chain_result, adaptive_status
                
        except Exception as e:
            logger.error(f"处理问题时出错: {str(e)}")
            error_msg = render_error_message(e, "问题处理")
            adaptive_status = render_status_message("处理失败", str(e))
            progress(1, desc="处理完成")
            return error_msg, "", "", adaptive_status

    def on_clear_conversation():
        """清空当前对话"""
        try:
            # 使用统一渲染器显示清空状态
            clear_msg = render_status_message("对话已清空", "可以开始新的对话")
            return clear_msg, "", ""
        except Exception as e:
            logger.error(f"清空对话时出错: {str(e)}")
            error_msg = render_error_message(e, "清空对话")
            return error_msg, "", ""
    
    # 创建Gradio界面
    with gr.Blocks(
        title="🧪 化学助手", 
        theme=gr.themes.Soft(),
         head="""
         <style>
         :root {
          --bg: #0f1419; /* 更深的背景色，类似ChatGPT dark mode */
          --panel: #1a1a1a; /* 面板背景 */
          --text: #e3e3e3; /* 主要文本颜色 */
          --subtle: #b3b3b3; /* 次级文本 */
          --primary: #19c37d; /* ChatGPT绿色主色调 */
          --accent: #ff6b4a; /* 强调色橙红 */
          --card: #212121; /* 卡片背景 */
          --border: #343541; /* 边框颜色 */
          --hover: #2a2a2f; /* 悬停颜色 */
          --input-bg: #40414f; /* 输入框背景 */
        }
        
        html, body { 
          font-family: 'Söhne', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
          color: var(--text); 
          background: var(--bg);
          font-size: 14px;
          line-height: 1.6;
        }
        
        .gradio-container { 
          max-width: 1200px !important; 
          margin: 0 auto; 
          padding: 16px;
        }
        
        /* 内容区域 */
        .gradio-container .prose, .markdown-body { 
          color: var(--text); 
          line-height: 1.7; 
          font-size: 14px; 
          max-width: none;
        }
        
        /* 标题样式 */
        .markdown-body h1, .markdown-body h2, .markdown-body h3 { 
          color: var(--text); 
          font-weight: 600; 
          margin-bottom: 12px; 
          margin-top: 24px;
        }
        
        .markdown-body h1 { font-size: 24px; }
        .markdown-body h2 { font-size: 20px; }
        .markdown-body h3 { font-size: 18px; }
        
        /* 段落和文本 */
        .markdown-body p { 
          margin: 8px 0; 
          color: var(--text); 
        }
        
        .markdown-body strong { color: var(--text); font-weight: 600; }
        .markdown-body em { color: var(--subtle); }
        
        /* 面板和容器 */
        .gr-panel, .gr-block { 
          background: var(--panel) !important; 
          border: 1px solid var(--border) !important; 
          border-radius: 8px !important;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important; 
        }
        
        .gr-accordion, .gr-box { 
          background: var(--card) !important; 
          border: 1px solid var(--border) !important; 
          border-radius: 6px !important;
        }
        
        /* 输入框样式 */
        .gradio-container .gr-input textarea, 
        .gradio-container .gr-input input { 
          background: var(--input-bg) !important; 
          border: 1px solid var(--border) !important; 
          color: var(--text) !important; 
          border-radius: 6px !important;
          padding: 12px !important;
          font-size: 14px !important;
        }
        
        .gradio-container .gr-input textarea:focus, 
        .gradio-container .gr-input input:focus { 
          border-color: var(--primary) !important; 
          box-shadow: 0 0 0 1px var(--primary) !important;
        }
        
        /* 按钮样式 */
        .gradio-container .gr-button { 
          background: var(--primary) !important; 
          color: white !important; 
          border: none !important; 
          border-radius: 6px !important;
          font-weight: 500 !important;
          font-size: 14px !important;
          padding: 8px 16px !important;
          transition: all 0.2s ease !important;
        }
        
        .gradio-container .gr-button:hover { 
          background: #16a166 !important;
          transform: translateY(-1px);
          box-shadow: 0 2px 6px rgba(25, 195, 125, 0.3) !important;
        }
        
        .gradio-container .gr-button.secondary { 
          background: var(--card) !important; 
          color: var(--text) !important; 
          border: 1px solid var(--border) !important; 
        }
        
        .gradio-container .gr-button.secondary:hover { 
          background: var(--hover) !important; 
          border-color: var(--primary) !important;
        }
        
        /* 下拉框和选择器 */
        .gradio-container .gr-dropdown { 
          background: var(--input-bg) !important;
          border: 1px solid var(--border) !important;
          color: var(--text) !important;
        }
        
        .gradio-container .gr-radio-group { 
          color: var(--text) !important; 
        }
        
        /* 链接 */
        .gradio-container .gr-prose a { 
          color: var(--primary); 
          text-decoration: none; 
        }
        
        .gradio-container .gr-prose a:hover { 
          text-decoration: underline; 
        }
        
        /* 代码块 */
        .markdown-body pre, .markdown-body code { 
          color: var(--text); 
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 4px;
        }
        
        .markdown-body pre { 
          padding: 16px; 
          margin: 12px 0;
        }
        
        .markdown-body code { 
          padding: 2px 6px; 
          font-size: 13px;
        }
        
        /* 引用块 */
        .markdown-body blockquote { 
          border-left: 3px solid var(--primary); 
          background: var(--card); 
          padding: 12px 16px; 
          color: var(--text); 
          margin: 12px 0;
        }
        
        /* 表格 */
        .markdown-body table { 
          border-color: var(--border); 
          background: var(--card);
        }
        
        .markdown-body table td, .markdown-body table th { 
          border-color: var(--border); 
          padding: 8px 12px;
        }
        
        /* Markdown区域优化 */
        .gr-markdown { 
          padding: 16px; 
          border-radius: 8px; 
          background: var(--card); 
          border: 1px solid var(--border); 
          margin: 8px 0;
        }
        
        /* 布局间距优化 */
        .gr-row { 
          gap: 12px; 
          margin: 8px 0;
        }
        
        .gr-column { 
          padding: 0 8px; 
        }
        
        /* 响应式优化 */
        @media (max-width: 768px) {
          .gradio-container { 
            padding: 8px; 
          }
          
          .gr-column { 
            padding: 0 4px; 
          }
          
          .gr-row { 
            gap: 8px; 
          }
        }
        </style>
        <script>
        window.MathJax = {
            tex: {
                inlineMath: [["$", "$"], ['\\(', '\\)']],
                displayMath: [["$$", "$$"], ['\\[', '\\]']],
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
                    shouldRender = true;
                }
            });
            if (shouldRender) {
                setTimeout(renderMathJax, 120);
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        """
    ) as demo:
        gr.Markdown("# 🧪 化学助手")
        gr.Markdown("基于AI的化学学习辅助系统，帮助您理解化学概念、解决化学问题。支持数学公式渲染和图片识别。")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 设置")
                function_choice = gr.Radio(
                    choices=["智能问答", "化学计算", "综合检索", "LangChain处理"],
                    value="综合检索",
                    label="功能类型",
                    info="选择要使用的功能"
                )
                
                # 综合检索设置
                with gr.Accordion("🔍 综合检索设置", open=True, visible=True) as comprehensive_settings:
                    enable_local_rag = gr.Checkbox(
                        label="启用本地RAG知识库",
                        value=True,
                        info="检索本地教材和题库"
                    )
                    enable_metaso = gr.Checkbox(
                        label="启用Metaso API",
                        value=True,
                        info="调用Metaso知识库API"
                    )
                    enable_tongyi = gr.Checkbox(
                        label="启用通义千问智能体",
                        value=True,
                        info="调用通义千问智能体知识库"
                    )
                    enable_pubchem = gr.Checkbox(
                        label="启用PubChem数据库",
                        value=True,
                        info="检索化学化合物信息"
                    )
                    use_llm_summary = gr.Checkbox(
                        label="启用LLM智能总结",
                        value=True,
                        info="使用大模型对检索结果进行智能总结和整合"
                    )
                
                # 自适应检索相关设置
                with gr.Accordion("🔧 自适应检索设置", open=False, visible=True) as adaptive_settings:
                    adaptive_enabled = gr.Checkbox(
                        label="启用自适应检索",
                        value=False,
                        info="根据查询复杂度动态调整检索策略"
                    )
                    show_complexity_analysis = gr.Checkbox(
                        label="显示复杂度分析",
                        value=True,
                        info="显示查询复杂度分析结果"
                    )
                    show_strategy_info = gr.Checkbox(
                        label="显示策略信息",
                        value=True,
                        info="显示使用的检索策略详情"
                    )
            
            with gr.Column(scale=3):
                gr.Markdown("### 对话界面")
                image_input = gr.Image(label="上传图像（可选）", type="pil", height=200)
                question_input = gr.Textbox(label="请输入您的问题", placeholder="例如：计算H2O的摩尔质量", lines=3)
                submit_btn = gr.Button("提交问题", variant="primary")
                answer_output = gr.Markdown(label="回答")
                comparison_output = gr.Markdown(label="模型答案对比分析")
                chain_result_output = gr.Markdown(label="LangChain链式分析结果")
                adaptive_status_output = gr.Textbox(label="自适应检索状态", interactive=False, lines=1)
                clear_btn = gr.Button("清除当前对话")
                
                # 自适应检索工具按钮
                with gr.Row():
                    analyze_complexity_btn = gr.Button("🧠 分析查询复杂度", variant="secondary", size="sm")
                    get_performance_btn = gr.Button("📊 获取性能报告", variant="secondary", size="sm")
                    
                # 综合检索性能监控
                with gr.Accordion("📈 综合检索性能监控", open=False):
                    with gr.Row():
                        perf_report_btn = gr.Button("📊 生成性能报告", variant="secondary", size="sm")
                        perf_clear_btn = gr.Button("🗑️ 清空性能数据", variant="secondary", size="sm")
                        perf_export_btn = gr.Button("💾 导出性能数据", variant="secondary", size="sm")
                    
                    perf_output = gr.Markdown(label="性能报告", value="暂无性能数据")
                    
                    with gr.Row():
                        perf_summary = gr.JSON(label="性能摘要", value={})
                        perf_trends = gr.JSON(label="性能趋势", value={})
                
                # 复杂度分析和性能报告显示区域
                with gr.Accordion("🔍 自适应检索详细信息", open=False):
                    complexity_analysis_output = gr.Markdown(label="复杂度分析结果")
                    performance_report_output = gr.Markdown(label="性能报告")

        with gr.Column(scale=1):
            gr.Markdown("### 📚 历史对话管理")
            
            # 搜索功能（增强版）
            with gr.Row():
                search_input = gr.Textbox(
                    placeholder="🔍 搜索历史对话（支持问题、答案、功能类型）...",
                    label="智能搜索",
                    scale=3,
                    lines=1
                )
                search_btn = gr.Button("🔍", scale=1, size="sm", variant="primary")
            
            # 功能类型筛选器
            with gr.Row():
                type_filter = gr.Radio(
                    choices=["全部", "智能问答", "化学计算", "综合检索", "LangChain处理"],
                    value="全部",
                    label="按类型筛选",
                    interactive=True
                )
            
            # 历史记录列表
            history_list = gr.Dropdown(
                choices=ConversationManager.format_history_for_display(ConversationManager.load_history()),
                label="历史对话列表",
                interactive=True
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
            
            # 状态显示（从Textbox改为Markdown以更友好地显示提示）
            history_status = gr.Markdown(
                value="",
                label="操作状态"
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
                        
                        # 获取原始答案内容，避免再次格式化
                        raw_answer = item['answer']
                        
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
{raw_answer}

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
            """搜索历史对话（增强版）"""
            if not keyword.strip():
                # 如果搜索关键词为空，显示所有历史记录
                all_history = ConversationManager.load_history()
                choices = ConversationManager.format_history_for_display(all_history)
                return choices, f"📋 显示所有 {len(all_history)} 条记录"
            
            try:
                results = ConversationManager.search_history(keyword.strip())
                choices = ConversationManager.format_history_for_display(results)
                
                if len(results) == 0:
                    return choices, f"🔍 未找到包含 '{keyword}' 的记录，尝试其他关键词"
                else:
                    return choices, f"🔍 找到 {len(results)} 条匹配记录（关键词：{keyword}）"
                    
            except Exception as e:
                logger.error(f"搜索历史记录失败: {e}")
                return [], f"❌ 搜索失败: {str(e)}"

        def filter_history_by_type(function_type):
            """按功能类型筛选历史记录"""
            try:
                all_history = ConversationManager.load_history()
                if function_type == "全部":
                    filtered_history = all_history
                else:
                    filtered_history = [item for item in all_history if item.get('function_type') == function_type]
                
                choices = ConversationManager.format_history_for_display(filtered_history)
                return choices, f"🏷️ {function_type}类型记录：{len(filtered_history)} 条"
            except Exception as e:
                logger.error(f"筛选历史记录失败: {e}")
                return [], f"❌ 筛选失败: {str(e)}"

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

        # 综合检索性能监控函数
        def generate_comprehensive_performance_report():
            """生成综合检索性能报告"""
            try:
                monitor = get_performance_monitor()
                report = monitor.generate_performance_report()
                return report
            except Exception as e:
                logger.error(f"生成综合检索性能报告失败: {e}")
                return f"生成性能报告失败: {str(e)}"
        
        def get_comprehensive_performance_summary():
            """获取综合检索性能摘要"""
            try:
                monitor = get_performance_monitor()
                summary = monitor.get_performance_summary()
                return summary
            except Exception as e:
                logger.error(f"获取性能摘要失败: {e}")
                return {"error": str(e)}
        
        def get_comprehensive_performance_trends():
            """获取综合检索性能趋势"""
            try:
                monitor = get_performance_monitor()
                trends = monitor.get_performance_trends()
                return trends
            except Exception as e:
                logger.error(f"获取性能趋势失败: {e}")
                return {"error": str(e)}
        
        def clear_comprehensive_performance_data():
            """清空综合检索性能数据"""
            try:
                monitor = get_performance_monitor()
                monitor.clear_records()
                return "性能数据已清空", {}, {}
            except Exception as e:
                logger.error(f"清空性能数据失败: {e}")
                return f"清空失败: {str(e)}", {}, {}
        
        def export_comprehensive_performance_data():
            """导出综合检索性能数据"""
            try:
                monitor = get_performance_monitor()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"performance_data_{timestamp}.json"
                monitor.export_data(filepath)
                return f"性能数据已导出到: {filepath}"
            except Exception as e:
                logger.error(f"导出性能数据失败: {e}")
                return f"导出失败: {str(e)}"

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

        # 新增：功能类型筛选事件
        type_filter.change(
            fn=filter_history_by_type,
            inputs=[type_filter],
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
        
        gr.Markdown("### 🧪 化学计算示例")
        with gr.Row():
            chem_calc_btns = [
                gr.Button("计算0.1mol NaCl在1L水中的浓度", size="sm"),
                gr.Button("计算0.1M HCl溶液的pH值", size="sm"),
                gr.Button("理想气体定律：1mol气体在STP条件下的体积", size="sm"),
                gr.Button("25°C转换为华氏度", size="sm")
            ]
        
        with gr.Row():
            more_chem_btns = [
                gr.Button("稀释：1M HCl 100mL稀释到500mL", size="sm"),
                gr.Button("化学计量：2mol H2与O2反应产生多少mol H2O", size="sm"),
                gr.Button("计算0.1M NaOH溶液的pH值", size="sm"),
                gr.Button("波义耳定律：压强从1atm变为2atm时体积变化", size="sm")
            ]
        
        with gr.Accordion("系统信息", open=False):
            gr.Markdown("""
            **版本**: 1.0.0  
            **功能**: 智能问答、化学计算、信息检索、LangChain处理  
            **支持**: 多模型、多模态输入、链式推理  
            **技术**: 多Agent架构，支持本地模型、外部API和LangChain
            """)
        
        # 自适应检索相关处理函数
        def analyze_query_complexity(question):
            """分析查询复杂度"""
            if not question.strip():
                return "请输入要分析的问题"
            
            if controller is None:
                return "演示模式，无法使用此功能"
            
            try:
                result = controller.analyze_query_complexity(question)
                if result.get('success'):
                    analysis = result['analysis']
                    return f"""### 🧠 查询复杂度分析

**复杂度等级**: {analysis.get('complexity', 'unknown')}
**复杂度分数**: {analysis.get('score', 0):.2f}
**推荐策略**: {analysis.get('recommended_strategy', 'unknown')}
**分析原因**: {analysis.get('reasoning', '无')}

---

**查询内容**: {question}"""
                else:
                    return f"分析失败: {result.get('error', '未知错误')}"
            except Exception as e:
                return f"分析过程中发生错误: {str(e)}"
        
        def get_performance_report():
            """获取自适应检索性能报告"""
            if controller is None:
                return "演示模式，无法使用此功能"
            
            try:
                result = controller.get_adaptive_performance_report()
                if result.get('success'):
                    report = result['report']
                    return f"""### 📊 自适应检索性能报告

**总查询数**: {report.get('total_queries', 0)}
**平均响应时间**: {report.get('avg_response_time', 0):.2f}秒

**策略使用统计**:
{chr(10).join([f"- {strategy}: {count}次" for strategy, count in report.get('strategy_usage', {}).items()])}

**系统状态**: {'正常运行' if report.get('total_queries', 0) > 0 else '暂无查询记录'}"""
                else:
                    return f"获取报告失败: {result.get('error', '未知错误')}"
            except Exception as e:
                return f"获取报告过程中发生错误: {str(e)}"
        
        # 主要功能事件绑定
        async def submit_and_refresh(question, function_choice, image, 
                              enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem, use_llm_summary,
                              adaptive_enabled, show_complexity, show_strategy):
            """提交问题并刷新历史记录"""
            # 处理问题
            answer, comparison, chain_result, adaptive_status = await process_question(
                question, function_choice, image, 
                enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem, use_llm_summary,
                adaptive_enabled, show_complexity, show_strategy
            )
            
            # 刷新历史记录和统计
            new_choices = update_history_list()
            new_stats = update_stats()
            
            return answer, comparison, chain_result, adaptive_status, new_choices, new_stats

        submit_btn.click(
            fn=submit_and_refresh,
            inputs=[question_input, function_choice, image_input,
                    enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem, use_llm_summary,
                    adaptive_enabled, show_complexity_analysis, show_strategy_info],
            outputs=[answer_output, comparison_output, chain_result_output, adaptive_status_output, history_list, stats_display],
            show_progress=True
        )
        
        question_input.submit(
            fn=submit_and_refresh,
            inputs=[question_input, function_choice, image_input,
                    enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem, use_llm_summary,
                    adaptive_enabled, show_complexity_analysis, show_strategy_info],
            outputs=[answer_output, comparison_output, chain_result_output, adaptive_status_output, history_list, stats_display],
            show_progress=True
        )
        
        # 自适应检索工具按钮事件
        analyze_complexity_btn.click(
            fn=analyze_query_complexity,
            inputs=[question_input],
            outputs=[complexity_analysis_output]
        )
        
        get_performance_btn.click(
            fn=get_performance_report,
            outputs=[performance_report_output]
        )
        
        clear_btn.click(
            fn=lambda: ("", None, "", "", "", "", "", "", "🧹 当前对话已清除"),
            outputs=[question_input, image_input, answer_output, comparison_output, chain_result_output, adaptive_status_output, complexity_analysis_output, performance_report_output, history_status]
        )
        
        example_btns[0].click(lambda: "计算H2O的摩尔质量", outputs=question_input)
        example_btns[1].click(lambda: "平衡化学方程式：H2 + O2 = H2O", outputs=question_input)
        example_btns[2].click(lambda: "什么是化学键？", outputs=question_input)
        example_btns[3].click(lambda: "查询苯的性质和用途", outputs=question_input)
        
        # 化学计算示例按钮事件绑定
        chem_calc_btns[0].click(lambda: "计算0.1mol NaCl在1L水中的浓度", outputs=question_input)
        chem_calc_btns[1].click(lambda: "计算0.1M HCl溶液的pH值", outputs=question_input)
        chem_calc_btns[2].click(lambda: "理想气体定律：1mol气体在STP条件下的体积", outputs=question_input)
        chem_calc_btns[3].click(lambda: "25°C转换为华氏度", outputs=question_input)
        
        more_chem_btns[0].click(lambda: "稀释：1M HCl 100mL稀释到500mL", outputs=question_input)
        more_chem_btns[1].click(lambda: "化学计量：2mol H2与O2反应产生多少mol H2O", outputs=question_input)
        more_chem_btns[2].click(lambda: "计算0.1M NaOH溶液的pH值", outputs=question_input)
        more_chem_btns[3].click(lambda: "波义耳定律：压强从1atm变为2atm时体积变化", outputs=question_input)
        
        # 综合检索性能监控事件绑定
        perf_report_btn.click(
            fn=generate_comprehensive_performance_report,
            outputs=[perf_output]
        )
        
        perf_clear_btn.click(
            fn=clear_comprehensive_performance_data,
            outputs=[perf_output, perf_summary, perf_trends]
        )
        
        perf_export_btn.click(
            fn=export_comprehensive_performance_data,
            outputs=[perf_output]
        )
        
        # 定期更新性能摘要和趋势
        def update_performance_displays():
            summary = get_comprehensive_performance_summary()
            trends = get_comprehensive_performance_trends()
            return summary, trends
        
        # 可以添加定时器或其他触发器来更新性能显示
    
    # 动态端口分配，避免端口冲突
    import socket
    
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
    
    # 查找可用端口
    available_port = find_free_port()
    if available_port is None:
        print("❌ 无法找到可用端口，请手动指定端口")
        available_port = 0  # 让Gradio自动分配
    else:
        print(f"🌐 使用端口: {available_port}")
    
    # 配置Ngrok
    try:
        # 设置Ngrok认证token
        ngrok.set_auth_token("30wI9yvO37ZIJZLmGMFO1RcuHjm_3axwVACtnAwToAeUFirKF")
        print("✅ Ngrok认证token已设置")
        
        # 创建Ngrok隧道
        public_url = ngrok.connect(available_port)
        print(f"🌍 公网访问地址: {public_url}")
        print(f"📱 您可以通过以下链接在任何设备上访问应用: {public_url}")
        
    except Exception as e:
        print(f"⚠️ Ngrok配置失败: {e}")
        print("将使用本地模式启动")
        public_url = None
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=available_port,
        share=True,  # 启用Gradio内置分享功能作为备选
        inbrowser=True,
        show_error=True,
        quiet=False
    )
    
    # 清理Ngrok隧道
    try:
        ngrok.disconnect(public_url)
        print("🔌 Ngrok隧道已断开")
    except:
        pass
    
    return demo

if __name__ == "__main__":
    print("请通过main.py启动完整系统")