#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复导入问题，临时禁用本地模型以启用自适应检索
"""

import os
import shutil
from datetime import datetime

def backup_file(file_path):
    """
    备份文件
    """
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已备份: {file_path} -> {backup_path}")
        return backup_path
    return None

def modify_agent_manager():
    """
    修改agent_manager.py，临时禁用本地模型导入
    """
    file_path = "core/agent_manager.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 备份原文件
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 注释掉本地模型导入
        modified_content = content.replace(
            "from agents.local_model_agent import LocalModelAgent",
            "# from agents.local_model_agent import LocalModelAgent  # 临时禁用"
        )
        
        # 修改初始化方法
        modified_content = modified_content.replace(
            "self.local_agent = LocalModelAgent()",
            "# self.local_agent = LocalModelAgent()  # 临时禁用"
        )
        
        # 修改get_agent方法
        if "elif agent_type == 'local':" in modified_content:
            modified_content = modified_content.replace(
                "elif agent_type == 'local':\n            return self.local_agent",
                "elif agent_type == 'local':\n            # return self.local_agent  # 临时禁用\n            return self.external_agent  # 使用外部模型代替"
            )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✅ 已修改: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修改失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"🔄 已恢复备份")
        return False

def modify_controller():
    """
    修改controller.py，简化初始化
    """
    file_path = "core/controller.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 备份原文件
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 注释掉agent_manager导入和初始化
        modified_content = content.replace(
            "from .agent_manager import AgentManager",
            "# from .agent_manager import AgentManager  # 临时禁用"
        )
        
        # 注释掉agent_manager初始化
        if "self.agent_manager = AgentManager()" in modified_content:
            modified_content = modified_content.replace(
                "self.agent_manager = AgentManager()",
                "# self.agent_manager = AgentManager()  # 临时禁用"
            )
        
        # 注释掉task_router导入和初始化
        modified_content = modified_content.replace(
            "from .task_router import TaskRouter",
            "# from .task_router import TaskRouter  # 临时禁用"
        )
        
        if "self.task_router = TaskRouter()" in modified_content:
            modified_content = modified_content.replace(
                "self.task_router = TaskRouter()",
                "# self.task_router = TaskRouter()  # 临时禁用"
            )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✅ 已修改: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修改失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"🔄 已恢复备份")
        return False

def create_simple_main():
    """
    创建简化的启动脚本
    """
    content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的化学助手启动脚本 - 专注自适应检索
"""

import os
import sys
import argparse

# 修复OpenMP库冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description='Chemistry Assistant - Adaptive Retrieval')
    parser.add_argument('--enable-adaptive', action='store_true', default=True,
                        help='启用自适应检索功能')
    args = parser.parse_args()
    
    print("🧪 化学助手 - 自适应检索模式")
    print("="*50)
    
    try:
        # 直接导入和初始化核心组件
        print("📦 初始化核心组件...")
        
        from core.llm_manager import LLMManager
        from core.chemistry_chain import ChemistryAnalysisChain
        from ui.app_gradio import start_ui
        
        # 创建简化的控制器类
        class SimpleController:
            def __init__(self, enable_adaptive=True):
                self.llm_manager = LLMManager()
                self.chemistry_chain = ChemistryAnalysisChain(
                    use_reranker=True, 
                    enable_adaptive=enable_adaptive
                )
                self.enable_adaptive = enable_adaptive
            
            def process_query(self, query, image_data=None, function_type="智能问答", 
                            enable_adaptive_retrieval=True, show_complexity_analysis=False, 
                            show_strategy_info=False):
                """处理查询"""
                try:
                    if enable_adaptive_retrieval and self.enable_adaptive:
                        # 使用自适应检索
                        import asyncio
                        result = asyncio.run(self.chemistry_chain.rag_retriever.adaptive_retrieve(query))
                        
                        response = {
                            'success': True,
                            'answer': result.get('answer', '处理完成'),
                            'retrieval_info': {
                                'strategy_used': result.get('strategy_used', 'adaptive'),
                                'complexity_analysis': result.get('complexity_analysis', {})
                            }
                        }
                        
                        return response
                    else:
                        # 使用传统检索
                        docs = self.chemistry_chain.rag_retriever.retrieve(query)
                        context = "\\n".join([doc.page_content for doc in docs[:3]]) if docs else "未找到相关信息"
                        
                        return {
                            'success': True,
                            'answer': f"基于检索到的信息：\\n{context}",
                            'retrieval_info': {
                                'strategy_used': 'traditional',
                                'complexity_analysis': {}
                            }
                        }
                        
                except Exception as e:
                    return {
                        'success': False,
                        'answer': f"处理查询时出错: {str(e)}",
                        'retrieval_info': {}
                    }
            
            def get_adaptive_performance_report(self):
                """获取自适应检索性能报告"""
                try:
                    if hasattr(self.chemistry_chain.rag_retriever, 'get_adaptive_performance_report'):
                        return self.chemistry_chain.rag_retriever.get_adaptive_performance_report()
                    else:
                        return {'message': '自适应检索性能报告不可用'}
                except Exception as e:
                    return {'error': str(e)}
        
        # 初始化控制器
        controller = SimpleController(enable_adaptive=args.enable_adaptive)
        print("✅ 控制器初始化成功")
        
        # 显示启用的功能
        if args.enable_adaptive:
            print("🔍 已启用功能: 自适应检索 + 双阶段检索")
        else:
            print("📚 已启用功能: 传统向量检索")
        
        print("🌐 启动Web界面...")
        start_ui(controller)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        print("\\n🔧 故障排除建议:")
        print("1. 检查Python环境和依赖包")
        print("2. 确认API密钥配置正确")
        print("3. 运行: python fix_imports.py 恢复原始文件")

if __name__ == "__main__":
    main()
'''
    
    with open('main_adaptive.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已创建: main_adaptive.py")

def restore_backups():
    """
    恢复备份文件
    """
    print("🔄 恢复备份文件...")
    
    backup_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if '.backup_' in file:
                backup_files.append(os.path.join(root, file))
    
    if not backup_files:
        print("📁 未找到备份文件")
        return
    
    print(f"📁 找到 {len(backup_files)} 个备份文件:")
    for backup_file in backup_files:
        print(f"  - {backup_file}")
    
    choice = input("\n是否恢复所有备份文件? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes', '是']:
        for backup_file in backup_files:
            try:
                original_file = backup_file.split('.backup_')[0]
                shutil.copy2(backup_file, original_file)
                print(f"✅ 已恢复: {original_file}")
                os.remove(backup_file)
                print(f"🗑️ 已删除备份: {backup_file}")
            except Exception as e:
                print(f"❌ 恢复失败 {backup_file}: {e}")
    else:
        print("⏭️ 跳过恢复")

def main():
    """
    主函数
    """
    print("🔧 化学助手导入修复工具")
    print("版本: 1.0.0")
    print("="*50)
    
    print("\n📋 可用操作:")
    print("1. 修复导入问题（临时禁用本地模型）")
    print("2. 创建简化启动脚本")
    print("3. 恢复备份文件")
    print("4. 执行完整修复并启动")
    
    choice = input("\n请选择操作 (1-4): ").strip()
    
    if choice == '1':
        print("\n🔧 修复导入问题...")
        success1 = modify_agent_manager()
        success2 = modify_controller()
        
        if success1 and success2:
            print("\n✅ 导入问题修复完成")
            print("💡 现在可以运行: python main.py --enable-adaptive")
        else:
            print("\n❌ 修复失败")
            
    elif choice == '2':
        print("\n🔧 创建简化启动脚本...")
        create_simple_main()
        print("\n✅ 简化启动脚本创建完成")
        print("💡 现在可以运行: python main_adaptive.py")
        
    elif choice == '3':
        restore_backups()
        
    elif choice == '4':
        print("\n🔧 执行完整修复...")
        
        # 修复导入
        print("1/3 修复导入问题...")
        success1 = modify_agent_manager()
        success2 = modify_controller()
        
        # 创建启动脚本
        print("2/3 创建启动脚本...")
        create_simple_main()
        
        if success1 and success2:
            print("3/3 启动系统...")
            print("\n✅ 修复完成，正在启动...")
            
            # 启动系统
            import subprocess
            try:
                subprocess.run([sys.executable, 'main_adaptive.py'], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ 启动失败: {e}")
            except KeyboardInterrupt:
                print("\n⏹️ 用户中断")
        else:
            print("\n❌ 修复失败，无法启动")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()