#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仅启用自适应检索功能的启动脚本
避免加载本地模型依赖
"""

import os
import sys
import argparse

# 修复OpenMP库冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_minimal_controller():
    """
    创建最小化控制器，避免加载本地模型
    """
    try:
        # 临时修改导入，避免加载本地模型
        import importlib.util
        
        # 检查是否可以导入核心模块
        print("🔍 检查核心模块...")
        
        # 导入LLM管理器
        from core.llm_manager import LLMManager
        print("✅ LLM管理器模块可用")
        
        # 导入RAG检索器
        from tools.rag_retriever import RAGRetriever
        print("✅ RAG检索器模块可用")
        
        # 导入自适应检索策略
        from tools.adaptive_retrieval_strategy import AdaptiveRetrievalStrategy
        print("✅ 自适应检索策略模块可用")
        
        # 导入化学计算器
        from tools.chemistry_solver import ChemistrySolver
        print("✅ 化学计算器模块可用")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def start_adaptive_web_ui():
    """
    启动支持自适应检索的Web界面
    """
    try:
        print("🚀 启动自适应检索Web界面...")
        
        # 导入Gradio
        import gradio as gr
        from config import MODEL_CONFIG
        
        # 导入核心组件
        from core.llm_manager import LLMManager
        from tools.rag_retriever import RAGRetriever
        from tools.chemistry_solver import ChemistrySolver
        
        # 初始化组件
        print("📦 初始化组件...")
        llm_manager = LLMManager()
        rag_retriever = RAGRetriever(use_reranker=True, enable_adaptive=True)
        chemistry_solver = ChemistrySolver()
        
        # 检查自适应检索状态
        adaptive_info = rag_retriever.get_adaptive_info()
        if adaptive_info['enabled'] and adaptive_info['available']:
            print("✅ 自适应检索功能已启用")
            status_msg = "🔍 自适应检索功能已启用"
        else:
            print("⚠️ 自适应检索功能未完全启用")
            status_msg = "⚠️ 自适应检索功能未完全启用"
        
        def process_query_with_adaptive(message, enable_adaptive, show_complexity, show_strategy):
            """
            使用自适应检索处理查询
            """
            try:
                if not message.strip():
                    return "请输入您的问题"
                
                print(f"\n🔍 处理查询: {message}")
                print(f"自适应检索: {enable_adaptive}")
                
                if enable_adaptive and rag_retriever.enable_adaptive:
                    # 使用自适应检索
                    import asyncio
                    
                    async def async_process():
                        return await rag_retriever.adaptive_retrieve(message)
                    
                    result = asyncio.run(async_process())
                    
                    # 构建回复
                    response_parts = []
                    
                    if 'answer' in result:
                        response_parts.append(f"**回答:** {result['answer']}")
                    
                    if show_complexity and 'complexity_analysis' in result:
                        analysis = result['complexity_analysis']
                        response_parts.append(f"\n**复杂度分析:**")
                        response_parts.append(f"- 复杂度等级: {analysis.get('complexity', 'unknown')}")
                        response_parts.append(f"- 复杂度分数: {analysis.get('score', 0):.2f}")
                        response_parts.append(f"- 分析维度: {', '.join(analysis.get('dimensions', []))}")
                    
                    if show_strategy and 'strategy_used' in result:
                        response_parts.append(f"\n**使用策略:** {result['strategy_used']}")
                    
                    return "\n".join(response_parts)
                    
                else:
                    # 使用传统检索
                    docs = rag_retriever.retrieve(message)
                    if docs:
                        context = "\n".join([doc.page_content for doc in docs[:3]])
                        return f"**传统检索结果:**\n{context}"
                    else:
                        return "未找到相关信息"
                        
            except Exception as e:
                return f"处理查询时出错: {str(e)}"
        
        def analyze_complexity_only(message):
            """
            仅分析查询复杂度
            """
            try:
                if not message.strip():
                    return "请输入要分析的问题"
                
                if rag_retriever.adaptive_strategy:
                    analysis = rag_retriever.adaptive_strategy.complexity_analyzer.analyze_query(message)
                    
                    result_parts = [
                        f"**查询:** {message}",
                        f"**复杂度等级:** {analysis.get('complexity', 'unknown')}",
                        f"**复杂度分数:** {analysis.get('score', 0):.2f}",
                        f"**推荐策略:** {analysis.get('recommended_strategy', 'unknown')}",
                        f"**分析维度:** {', '.join(analysis.get('dimensions', []))}"
                    ]
                    
                    return "\n".join(result_parts)
                else:
                    return "自适应检索策略未启用，无法分析复杂度"
                    
            except Exception as e:
                return f"复杂度分析失败: {str(e)}"
        
        # 创建Gradio界面
        with gr.Blocks(title="化学助手 - 自适应检索模式", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🧪 化学助手 - 自适应检索模式")
            gr.Markdown(status_msg)
            
            with gr.Tab("自适应检索"):
                with gr.Row():
                    with gr.Column(scale=2):
                        message_input = gr.Textbox(
                            label="输入您的化学问题",
                            placeholder="例如：计算H2O的摩尔质量",
                            lines=3
                        )
                        
                        with gr.Row():
                            enable_adaptive = gr.Checkbox(
                                label="启用自适应检索",
                                value=True
                            )
                            show_complexity = gr.Checkbox(
                                label="显示复杂度分析",
                                value=True
                            )
                            show_strategy = gr.Checkbox(
                                label="显示策略信息",
                                value=True
                            )
                        
                        submit_btn = gr.Button("提交查询", variant="primary")
                    
                    with gr.Column(scale=3):
                        output = gr.Textbox(
                            label="回答",
                            lines=15,
                            max_lines=20
                        )
            
            with gr.Tab("复杂度分析"):
                with gr.Row():
                    with gr.Column():
                        analyze_input = gr.Textbox(
                            label="输入要分析的问题",
                            placeholder="输入任何化学问题进行复杂度分析",
                            lines=2
                        )
                        analyze_btn = gr.Button("分析复杂度", variant="secondary")
                    
                    with gr.Column():
                        analyze_output = gr.Textbox(
                            label="复杂度分析结果",
                            lines=10
                        )
            
            with gr.Tab("系统状态"):
                def get_system_status():
                    status_info = []
                    status_info.append(f"**自适应检索状态:** {'✅ 已启用' if adaptive_info['enabled'] else '❌ 未启用'}")
                    status_info.append(f"**自适应检索可用:** {'✅ 是' if adaptive_info['available'] else '❌ 否'}")
                    status_info.append(f"**文本排序器:** {'✅ 已启用' if adaptive_info['reranker_enabled'] else '❌ 未启用'}")
                    status_info.append(f"**支持策略:** {', '.join(adaptive_info['supported_strategies'])}")
                    
                    return "\n".join(status_info)
                
                status_display = gr.Textbox(
                    label="系统状态",
                    value=get_system_status(),
                    lines=8,
                    interactive=False
                )
                
                refresh_btn = gr.Button("刷新状态")
                refresh_btn.click(get_system_status, outputs=[status_display])
            
            # 绑定事件
            submit_btn.click(
                process_query_with_adaptive,
                inputs=[message_input, enable_adaptive, show_complexity, show_strategy],
                outputs=[output]
            )
            
            message_input.submit(
                process_query_with_adaptive,
                inputs=[message_input, enable_adaptive, show_complexity, show_strategy],
                outputs=[output]
            )
            
            analyze_btn.click(
                analyze_complexity_only,
                inputs=[analyze_input],
                outputs=[analyze_output]
            )
            
            analyze_input.submit(
                analyze_complexity_only,
                inputs=[analyze_input],
                outputs=[analyze_output]
            )
        
        # 启动界面
        print("🌐 启动Web界面...")
        demo.launch(
            server_name="127.0.0.1",
            server_port=7863,
            share=False,
            inbrowser=True,
            show_error=True,
            quiet=False
        )
        
    except Exception as e:
        print(f"❌ Web界面启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主函数
    """
    print("🧪 化学助手 - 自适应检索专用启动器")
    print("版本: 1.0.0 (无本地模型依赖)")
    print("="*50)
    
    # 检查核心模块
    if not create_minimal_controller():
        print("\n❌ 核心模块检查失败，无法启动")
        print("\n🔧 建议:")
        print("1. 检查Python环境")
        print("2. 安装必要依赖: pip install gradio requests")
        print("3. 确认配置文件正确")
        return
    
    print("\n✅ 核心模块检查通过")
    
    # 启动Web界面
    start_adaptive_web_ui()

if __name__ == "__main__":
    main()