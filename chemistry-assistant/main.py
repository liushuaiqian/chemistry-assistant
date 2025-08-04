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
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def main():
    parser = argparse.ArgumentParser(description='Chemistry Assistant')
    parser.add_argument('--mode', type=str, default='web', choices=['cli', 'web'],
                        help='启动模式: cli或web (默认: web)')
    parser.add_argument('--model', type=str, default='local_model',
                        choices=['local_model', 'openai', 'zhipu', 'claude', 'tongyi'],
                        help='使用的模型: local_model, openai, zhipu, claude, tongyi (默认: local_model)')
    parser.add_argument('--disable-reranker', action='store_true',
                        help='禁用文本排序器，使用传统向量检索模式')
    parser.add_argument('--enable-adaptive', action='store_true',
                        help='启用自适应检索功能，根据查询复杂度动态调整检索策略')
    args = parser.parse_args()
    
    # 确定是否使用排序器和自适应检索
    use_reranker = not args.disable_reranker
    enable_adaptive = args.enable_adaptive
    
    # 尝试初始化Controller，如果失败则使用None
    try:
        controller = Controller(use_reranker=use_reranker, enable_adaptive=enable_adaptive)
        print("Controller初始化成功")
        
        # 显示启用的功能
        features = []
        if enable_adaptive:
            features.append("自适应检索")
            if use_reranker:
                features.append("双阶段检索")
        elif use_reranker:
            features.append("双阶段检索（向量检索+文本排序）")
        else:
            features.append("传统向量检索")
        
        print(f"已启用功能: {', '.join(features)}")
        
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
        if enable_adaptive:
            print("提示: 输入'multimodal'切换到多模态模式，'adaptive'使用自适应检索，'analyze'分析查询复杂度，'exit'退出")
        else:
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
                if enable_adaptive:
                    query = input("请输入问题 (输入'multimodal'切换多模态，'adaptive'自适应检索，'analyze'分析复杂度，'report'性能报告，'exit'退出): ")
                else:
                    query = input("请输入问题 (输入'multimodal'切换到多模态模式，'exit'退出): ")
                
                if query.lower() == 'exit':
                    break
                elif query.lower() == 'multimodal':
                    multimodal_mode = True
                    print("已切换到多模态模式")
                    continue
                elif query.lower() == 'adaptive' and enable_adaptive:
                    adaptive_query = input("请输入要使用自适应检索处理的问题: ")
                    if adaptive_query.strip():
                        import asyncio
                        result = asyncio.run(controller.process_with_adaptive_retrieval(adaptive_query))
                        print(f"自适应检索回答: {result.get('answer', '处理失败')}")
                        print(f"使用策略: {result.get('retrieval_info', {}).get('strategy_used', 'unknown')}")
                        if result.get('retrieval_info', {}).get('complexity_analysis'):
                            analysis = result['retrieval_info']['complexity_analysis']
                            print(f"复杂度: {analysis.get('complexity', 'unknown')} (分数: {analysis.get('score', 0):.2f})")
                    continue
                elif query.lower() == 'analyze' and enable_adaptive:
                    analyze_query = input("请输入要分析复杂度的问题: ")
                    if analyze_query.strip():
                        result = controller.analyze_query_complexity(analyze_query)
                        if result.get('success'):
                            analysis = result['analysis']
                            print(f"复杂度分析结果:")
                            print(f"  复杂度等级: {analysis.get('complexity', 'unknown')}")
                            print(f"  复杂度分数: {analysis.get('score', 0):.2f}")
                            print(f"  推荐策略: {analysis.get('recommended_strategy', 'unknown')}")
                            print(f"  分析原因: {analysis.get('reasoning', '无')}")
                        else:
                            print(f"分析失败: {result.get('error', '未知错误')}")
                    continue
                elif query.lower() == 'report' and enable_adaptive:
                    result = controller.get_adaptive_performance_report()
                    if result.get('success'):
                        report = result['report']
                        print("自适应检索性能报告:")
                        print(f"  总查询数: {report.get('total_queries', 0)}")
                        print(f"  策略使用统计: {report.get('strategy_usage', {})}")
                        print(f"  平均响应时间: {report.get('avg_response_time', 0):.2f}秒")
                    else:
                        print(f"获取报告失败: {result.get('error', '未知错误')}")
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