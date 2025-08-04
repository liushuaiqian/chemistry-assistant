#!/usr/bin/env python
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
