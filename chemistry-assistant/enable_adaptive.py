#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启用自适应检索功能的脚本
"""

import os
import sys
import subprocess

def enable_adaptive_retrieval():
    """
    启用自适应检索功能
    """
    print("🔍 启用自适应检索功能")
    print("="*50)
    
    # 检查当前目录
    if not os.path.exists('main.py'):
        print("❌ 请在项目根目录运行此脚本")
        return False
    
    print("📋 自适应检索功能说明:")
    print("• 根据查询复杂度动态调整检索策略")
    print("• 支持简单查询、计算查询、复杂理论查询")
    print("• 提供实时复杂度分析和策略推荐")
    print("• 优化检索效率和答案质量")
    
    print("\n🚀 启动选项:")
    print("1. 启用自适应检索 + 双阶段检索 (推荐)")
    print("2. 仅启用自适应检索")
    print("3. 查看当前配置状态")
    print("4. 测试自适应检索功能")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == '1':
        print("\n🔧 启动: 自适应检索 + 双阶段检索")
        cmd = [sys.executable, 'main.py', '--enable-adaptive']
        print(f"执行命令: {' '.join(cmd)}")
        return run_command(cmd)
        
    elif choice == '2':
        print("\n🔧 启动: 仅自适应检索")
        cmd = [sys.executable, 'main.py', '--enable-adaptive', '--disable-reranker']
        print(f"执行命令: {' '.join(cmd)}")
        return run_command(cmd)
        
    elif choice == '3':
        print("\n🔍 检查当前配置状态...")
        return check_current_status()
        
    elif choice == '4':
        print("\n🧪 运行自适应检索测试...")
        cmd = [sys.executable, 'test_adaptive_retrieval.py']
        print(f"执行命令: {' '.join(cmd)}")
        return run_command(cmd)
        
    else:
        print("❌ 无效选择")
        return False

def run_command(cmd):
    """
    运行命令
    """
    try:
        print("\n" + "="*50)
        print("🚀 正在启动...")
        print("💡 提示: 按 Ctrl+C 可以停止程序")
        print("="*50)
        
        # 使用subprocess运行命令
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 universal_newlines=True, bufsize=1)
        
        # 实时输出
        for line in process.stdout:
            print(line.rstrip())
            
        process.wait()
        return process.returncode == 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断程序")
        if 'process' in locals():
            process.terminate()
        return False
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def check_current_status():
    """
    检查当前配置状态
    """
    try:
        # 导入必要模块检查依赖
        print("🔍 检查依赖模块...")
        
        try:
            from tools.adaptive_retrieval_strategy import AdaptiveRetrievalStrategy
            print("✅ 自适应检索策略模块可用")
        except ImportError as e:
            print(f"❌ 自适应检索策略模块不可用: {e}")
            return False
            
        try:
            from tools.text_reranker import TextReranker
            print("✅ 文本排序器模块可用")
        except ImportError as e:
            print(f"⚠️ 文本排序器模块不可用: {e}")
            
        try:
            from tools.chemistry_solver import ChemistrySolver
            print("✅ 化学计算器模块可用")
        except ImportError as e:
            print(f"❌ 化学计算器模块不可用: {e}")
            return False
            
        # 检查配置文件
        print("\n🔍 检查配置文件...")
        try:
            from config import MODEL_CONFIG
            print("✅ 配置文件加载成功")
            
            # 检查API密钥
            api_keys_configured = 0
            for provider in ['zhipu', 'tongyi', 'claude', 'deepseek']:
                if provider in MODEL_CONFIG:
                    key = MODEL_CONFIG[provider].get('api_key', '')
                    if key and not key.startswith('your_'):
                        print(f"✅ {provider} API密钥已配置")
                        api_keys_configured += 1
                    else:
                        print(f"⚠️ {provider} API密钥未配置")
                        
            if api_keys_configured == 0:
                print("❌ 未配置任何API密钥，系统可能无法正常工作")
                return False
            else:
                print(f"✅ 已配置 {api_keys_configured} 个API密钥")
                
        except Exception as e:
            print(f"❌ 配置文件检查失败: {e}")
            return False
            
        print("\n✅ 系统状态检查完成，可以启用自适应检索功能")
        return True
        
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        return False

def show_usage_guide():
    """
    显示使用指南
    """
    print("\n📖 自适应检索使用指南:")
    print("\n🎯 适用场景:")
    print("• 简单查询: '氢气的化学式是什么？'")
    print("• 计算查询: '计算CaCO3的摩尔质量'")
    print("• 复杂查询: '解释化学平衡的勒夏特列原理'")
    
    print("\n⚙️ Web界面使用:")
    print("1. 在功能类型中选择'自适应检索'")
    print("2. 或在'自适应检索设置'中勾选'启用自适应检索'")
    print("3. 可选择显示复杂度分析和策略信息")
    
    print("\n🖥️ CLI命令:")
    print("• adaptive: 使用自适应检索处理问题")
    print("• analyze: 分析查询复杂度")
    print("• report: 查看性能报告")
    
    print("\n💡 最佳实践:")
    print("• 明确表达问题，有助于准确的复杂度分析")
    print("• 复杂问题可分解为多个子问题")
    print("• 定期查看性能报告，优化使用模式")

def main():
    """
    主函数
    """
    print("🧪 化学助手 - 自适应检索功能启用器")
    print("版本: 1.0.0")
    print("="*50)
    
    # 显示使用指南
    show_usage_guide()
    
    # 启用自适应检索
    success = enable_adaptive_retrieval()
    
    if success:
        print("\n✅ 自适应检索功能启用成功！")
    else:
        print("\n❌ 自适应检索功能启用失败")
        print("\n🔧 故障排除建议:")
        print("1. 检查Python环境和依赖包")
        print("2. 确认API密钥配置正确")
        print("3. 查看详细错误日志")
        print("4. 尝试运行: python test_adaptive_retrieval.py")

if __name__ == "__main__":
    main()