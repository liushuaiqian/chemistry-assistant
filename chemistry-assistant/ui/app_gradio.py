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
from utils.web_ui_formatter import clean_and_format_output, format_comparison_output, format_chain_result, format_error_message, format_status_message
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

# clean_and_format_output函数已移至utils/web_ui_formatter.py模块
# 现在直接使用导入的函数

def start_ui(controller=None):
    """
    启动Gradio Web界面
    """
    
    def process_question(question, function_choice, image=None, 
                        enable_local_rag=True, enable_metaso=True, enable_tongyi=True, enable_pubchem=True,
                        adaptive_enabled=False, show_complexity=True, show_strategy=True, progress=gr.Progress()):
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
            
            # 综合检索处理
            if function_choice == "综合检索":
                progress(0.4, desc="正在进行综合检索...")
                
                # 调用综合检索方法
                result = controller.process_comprehensive_retrieval(
                    question, 
                    enable_local_rag=enable_local_rag,
                    enable_metaso=enable_metaso, 
                    enable_tongyi=enable_tongyi,
                    enable_pubchem=enable_pubchem
                )
                
                if result.get('success'):
                    answer = result.get('combined_answer', '未获取到结果')
                    
                    # 构建知识源信息
                    sources_info = []
                    sources = result.get('sources', [])
                    
                    if sources:
                        sources_info.append(f"**📚 使用的知识源**: {', '.join(sources)}")
                    
                    if 'local_documents' in result and result['local_documents']:
                        sources_info.append(f"**📄 本地文档数**: {len(result['local_documents'])}")
                    
                    if 'external_knowledge' in result:
                        ext_knowledge = result['external_knowledge']
                        if ext_knowledge.get('all_sources'):
                            successful_sources = [s['source'] for s in ext_knowledge['all_sources'] if s.get('success')]
                            if successful_sources:
                                sources_info.append(f"**🌐 外部知识源**: {', '.join(successful_sources)}")
                    
                    comp = "\n\n".join(sources_info) if sources_info else ""
                    chain = ""
                else:
                    answer = result.get('error', '综合检索处理失败')
                    comp = "检索失败，请检查网络连接和API配置"
                    chain = ""
            
            # 自适应检索处理
            elif adaptive_enabled:
                progress(0.4, desc="正在进行自适应检索...")
                import asyncio
                result = asyncio.run(controller.process_with_adaptive_retrieval(question))
                
                if result.get('success'):
                    answer = result['answer']
                    comp = ""
                    chain = ""
                    
                    # 构建自适应检索信息
                    adaptive_info = []
                    retrieval_info = result.get('retrieval_info', {})
                    
                    if show_strategy and retrieval_info:
                        strategy_used = retrieval_info.get('strategy_used', 'unknown')
                        adaptive_info.append(f"**🎯 使用策略**: {strategy_used}")
                        
                        if 'execution_time' in retrieval_info:
                            adaptive_info.append(f"**⏱️ 执行时间**: {retrieval_info['execution_time']:.2f}秒")
                        
                        if 'documents_retrieved' in retrieval_info:
                            adaptive_info.append(f"**📄 检索文档数**: {retrieval_info['documents_retrieved']}")
                    
                    if show_complexity and retrieval_info.get('complexity_analysis'):
                        analysis = retrieval_info['complexity_analysis']
                        adaptive_info.append(f"**🧠 查询复杂度**: {analysis.get('complexity', 'unknown')} (分数: {analysis.get('score', 0):.2f})")
                        adaptive_info.append(f"**💭 分析原因**: {analysis.get('reasoning', '无')}")
                    
                    if adaptive_info:
                        chain = "\n\n---\n\n### 🔍 自适应检索信息\n\n" + "\n\n".join(adaptive_info)
                else:
                    answer = result.get('answer', '自适应检索处理失败')
                    comp = f"错误信息: {result.get('error', '未知错误')}"
                    chain = ""
                    
            elif function_choice == "LangChain处理":
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
            # 使用专门的格式化函数处理不同类型的输出
            cleaned_answer = clean_and_format_output(answer)
            cleaned_comparison = format_comparison_output(comp)
            cleaned_chain_result = format_chain_result(chain)
            
            # 构建检索状态信息
            adaptive_status = ""
            if function_choice == "综合检索":
                status_parts = []
                if enable_local_rag:
                    status_parts.append("本地RAG")
                if enable_metaso:
                    status_parts.append("Metaso")
                if enable_tongyi:
                    status_parts.append("通义千问")
                if enable_pubchem:
                    status_parts.append("PubChem")
                
                if status_parts:
                    adaptive_status = f"✅ 综合检索已启用: {', '.join(status_parts)}"
                else:
                    adaptive_status = "⚠️ 未启用任何知识源"
            elif adaptive_enabled:
                if hasattr(controller, 'enable_adaptive') and controller.enable_adaptive:
                    adaptive_status = "✅ 自适应检索已启用"
                else:
                    adaptive_status = "⚠️ 自适应检索功能未在系统中启用，使用传统处理模式"

            # 保存对话历史
            ConversationManager.add_conversation(question, cleaned_answer, function_choice, bool(image))

            progress(1, desc="处理完成")
            return cleaned_answer, cleaned_comparison, cleaned_chain_result, adaptive_status
        except Exception as e:
            logger.error(f"处理问题时发生错误: {e}", exc_info=True)
            progress(1, desc="处理失败")
            return f"处理过程中发生错误: {e}", "", "", "❌ 处理失败"

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

            # 使用专门的格式化函数处理不同类型的输出
            cleaned_answer = clean_and_format_output(answer)
            cleaned_comparison = format_comparison_output(comp)
            cleaned_chain_result = format_chain_result(chain)

            return cleaned_answer, cleaned_comparison, cleaned_chain_result
                
        except Exception as e:
            error_msg = format_error_message(e, "问题处理")
            return error_msg, "", ""
    
    # 创建Gradio界面
    with gr.Blocks(
        title="🧪 化学助手", 
        theme=gr.themes.Soft(),
        head="""
        <style>
        /* 表格样式优化 - 解决方程式显示问题 */
        .markdown-body table {
            width: 100%;
            table-layout: auto;
            border-collapse: collapse;
            margin: 1em 0;
            overflow-x: auto;
        }
        
        .markdown-body table td, .markdown-body table th {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
            vertical-align: top;
            word-wrap: break-word;
            white-space: normal;
            min-width: 0;
        }
        
        /* 化学方程式样式 */
        .chemical-equation {
            white-space: nowrap;
            display: inline-block;
            font-family: 'Courier New', monospace;
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid #e9ecef;
            font-size: 0.95em;
            overflow-x: auto;
            max-width: 100%;
        }
        
        /* 特别处理方程式列 - 确保化学方程式在一行显示 */
        .markdown-body table td:nth-child(2) {
            white-space: nowrap;
            overflow-x: auto;
            max-width: 400px;
            font-family: 'Times New Roman', serif;
        }
        
        /* 确保化学方程式在表格中正确显示 */
        .markdown-body table .chemical-equation {
            font-family: 'Courier New', monospace;
            white-space: nowrap;
        }
        
        /* 包含化学方程式的表格单元格 */
        .markdown-body table td:has(.chemical-equation) {
            overflow-x: auto;
            white-space: nowrap;
        }
        
        /* 表格容器滚动 */
        .markdown-body {
            overflow-x: auto;
        }
        
        /* 响应式表格 */
        @media (max-width: 768px) {
            .markdown-body table {
                font-size: 0.9em;
            }
            .markdown-body table td:nth-child(2) {
                max-width: 300px;
            }
            
            .chemical-equation {
                font-size: 0.85em;
                max-width: 200px;
            }
        }
        
        /* 表格滚动条样式 */
        .markdown-body table td:nth-child(2)::-webkit-scrollbar,
        .chemical-equation::-webkit-scrollbar {
            height: 4px;
        }
        
        .markdown-body table td:nth-child(2)::-webkit-scrollbar-track,
        .chemical-equation::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        .markdown-body table td:nth-child(2)::-webkit-scrollbar-thumb,
        .chemical-equation::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 2px;
        }
        
        .markdown-body table td:nth-child(2)::-webkit-scrollbar-thumb:hover,
        .chemical-equation::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* 强制表格内容不换行 */
        .markdown-body table td:nth-child(2) * {
            white-space: nowrap !important;
        }
        </style>
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
                
                # 复杂度分析和性能报告显示区域
                with gr.Accordion("🔍 自适应检索详细信息", open=False):
                    complexity_analysis_output = gr.Markdown(label="复杂度分析结果")
                    performance_report_output = gr.Markdown(label="性能报告")

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
        def submit_and_refresh(question, function_choice, image, 
                              enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem,
                              adaptive_enabled, show_complexity, show_strategy):
            """提交问题并刷新历史记录"""
            # 处理问题
            answer, comparison, chain_result, adaptive_status = process_question(
                question, function_choice, image, 
                enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem,
                adaptive_enabled, show_complexity, show_strategy
            )
            
            # 刷新历史记录和统计
            new_choices = update_history_list()
            new_stats = update_stats()
            
            return answer, comparison, chain_result, adaptive_status, new_choices, new_stats

        submit_btn.click(
            fn=submit_and_refresh,
            inputs=[question_input, function_choice, image_input, 
                   enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem,
                   adaptive_enabled, show_complexity_analysis, show_strategy_info],
            outputs=[answer_output, comparison_output, chain_result_output, adaptive_status_output, history_list, stats_display]
        )
        
        question_input.submit(
            fn=submit_and_refresh,
            inputs=[question_input, function_choice, image_input, 
                   enable_local_rag, enable_metaso, enable_tongyi, enable_pubchem,
                   adaptive_enabled, show_complexity_analysis, show_strategy_info],
            outputs=[answer_output, comparison_output, chain_result_output, adaptive_status_output, history_list, stats_display]
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
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=available_port,
        share=False,
        inbrowser=True,
        show_error=True,
        quiet=False
    )
    
    return demo

if __name__ == "__main__":
    print("请通过main.py启动完整系统")