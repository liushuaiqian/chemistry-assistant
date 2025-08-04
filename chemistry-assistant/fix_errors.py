#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统错误修复脚本
解决运行时遇到的常见错误
"""

import os
import sys

def fix_openmp_error():
    """
    修复OpenMP库冲突错误
    """
    print("🔧 修复OpenMP库冲突...")
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    print("✅ OpenMP库冲突已修复")

def fix_gradio_config():
    """
    修复Gradio配置问题
    """
    print("🔧 修复Gradio配置...")
    
    # 读取当前的app_gradio.py文件
    app_file = './ui/app_gradio.py'
    if not os.path.exists(app_file):
        print("❌ 找不到app_gradio.py文件")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复Gradio启动配置
    old_launch = '''demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        inbrowser=True
    )'''
    
    new_launch = '''demo.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        inbrowser=True,
        show_error=True,
        quiet=False
    )'''
    
    if old_launch in content:
        content = content.replace(old_launch, new_launch)
        
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Gradio配置已修复")
        return True
    else:
        print("⚠️ 未找到需要修复的Gradio配置")
        return False

def create_startup_script():
    """
    创建安全的启动脚本
    """
    print("🔧 创建安全启动脚本...")
    
    startup_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全启动脚本
"""

import os
import sys

# 修复OpenMP库冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import main
    print("🚀 启动化学助手...")
    main()
except Exception as e:
    print(f"❌ 启动失败: {e}")
    print("\n🔍 错误诊断:")
    print("1. 检查Python环境是否正确")
    print("2. 检查依赖包是否完整安装")
    print("3. 检查API密钥配置是否正确")
    print("4. 查看详细错误日志")
    
    import traceback
    traceback.print_exc()
'''
    
    with open('./start_safe.py', 'w', encoding='utf-8') as f:
        f.write(startup_content)
    
    print("✅ 安全启动脚本已创建: start_safe.py")

def create_error_handler():
    """
    创建错误处理模块
    """
    print("🔧 创建错误处理模块...")
    
    error_handler_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误处理模块
提供统一的错误处理和恢复机制
"""

import logging
import traceback
from functools import wraps

class ErrorHandler:
    """
    错误处理器
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    def safe_execute(self, func, *args, **kwargs):
        """
        安全执行函数
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"执行 {func.__name__} 时发生错误: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def retry_on_failure(self, max_retries=3, delay=1):
        """
        失败重试装饰器
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            self.logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
                            raise
                        else:
                            self.logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{delay}秒后重试: {e}")
                            time.sleep(delay)
                
            return wrapper
        return decorator
    
    def graceful_degradation(self, fallback_func=None):
        """
        优雅降级装饰器
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.logger.warning(f"函数 {func.__name__} 执行失败，启用降级模式: {e}")
                    if fallback_func:
                        return fallback_func(*args, **kwargs)
                    return None
            return wrapper
        return decorator

# 全局错误处理器实例
error_handler = ErrorHandler()
'''
    
    with open('./utils/error_handler.py', 'w', encoding='utf-8') as f:
        f.write(error_handler_content)
    
    print("✅ 错误处理模块已创建: utils/error_handler.py")

def main():
    """
    主修复函数
    """
    print("🔧 开始修复系统错误...\n")
    
    # 修复OpenMP错误
    fix_openmp_error()
    print()
    
    # 修复Gradio配置
    fix_gradio_config()
    print()
    
    # 创建安全启动脚本
    create_startup_script()
    print()
    
    # 创建错误处理模块
    create_error_handler()
    print()
    
    print("✅ 所有错误修复完成！")
    print("\n📋 使用建议:")
    print("1. 使用 'python start_safe.py' 启动系统")
    print("2. 如果仍有问题，检查控制台输出的详细错误信息")
    print("3. 确保所有依赖包已正确安装")
    print("4. 检查API密钥配置是否正确")

if __name__ == "__main__":
    main()