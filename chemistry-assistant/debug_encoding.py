#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试LangChain处理结果乱码问题
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.unified_markdown_renderer import render_chain_result

# ConversationManager类定义（从app_gradio.py复制）
CONVERSATION_HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'conversation_history.json')

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
            print(f"加载对话历史失败: {e}")
            return []

def test_encoding_issue():
    """测试编码问题"""
    print("=== 调试LangChain处理结果乱码问题 ===")
    print(f"Python版本: {sys.version}")
    print(f"默认编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    print()
    
    # 1. 测试从历史记录中读取LangChain结果
    print("1. 从历史记录读取LangChain处理结果...")
    history = ConversationManager.load_history()
    
    langchain_results = [item for item in history if item.get('function_type') == 'LangChain处理']
    
    if not langchain_results:
        print("未找到LangChain处理结果")
        return
    
    # 取最新的一个结果进行测试
    latest_result = langchain_results[-1]
    print(f"找到 {len(langchain_results)} 个LangChain处理结果")
    print(f"测试最新结果 ID: {latest_result['id']}")
    print(f"问题: {latest_result['question']}")
    print()
    
    # 2. 检查原始数据
    print("2. 原始答案数据检查:")
    raw_answer = latest_result['answer']
    print(f"答案类型: {type(raw_answer)}")
    print(f"答案长度: {len(raw_answer)}")
    print(f"前100个字符: {repr(raw_answer[:100])}")
    print()
    
    # 3. 测试渲染过程
    print("3. 测试渲染过程...")
    try:
        rendered_html = render_chain_result(raw_answer)
        print(f"渲染成功，HTML长度: {len(rendered_html)}")
        print(f"HTML前200个字符: {repr(rendered_html[:200])}")
        print()
        
        # 4. 检查特殊字符
        print("4. 检查特殊字符...")
        special_chars = ['→', '←', '↔', '₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']
        for char in special_chars:
            if char in raw_answer:
                print(f"原始数据包含: {char} (Unicode: U+{ord(char):04X})")
            if char in rendered_html:
                print(f"渲染结果包含: {char} (Unicode: U+{ord(char):04X})")
        print()
        
        # 5. 保存测试结果到文件
        print("5. 保存测试结果...")
        test_output = {
            'raw_answer': raw_answer,
            'rendered_html': rendered_html,
            'encoding_info': {
                'python_version': sys.version,
                'default_encoding': sys.getdefaultencoding(),
                'filesystem_encoding': sys.getfilesystemencoding()
            }
        }
        
        with open('encoding_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(test_output, f, ensure_ascii=False, indent=2)
        
        with open('encoding_test_result.html', 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>编码测试结果</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
    window.MathJax = {{
        tex: {{
            inlineMath: [["$", "$"], ['\\(', '\\)']],
            displayMath: [["$$", "$$"], ['\\[', '\\]']],
            processEscapes: true,
            processEnvironments: true,
            packages: {{'[+]': ['mhchem']}}
        }},
        loader: {{
            load: ['[tex]/mhchem']
        }}
    }};
    </script>
</head>
<body>
    <h1>编码测试结果</h1>
    <h2>原始数据</h2>
    <pre>{raw_answer[:500]}...</pre>
    <h2>渲染结果</h2>
    <div>{rendered_html}</div>
</body>
</html>""")
        
        print("测试结果已保存到:")
        print("- encoding_test_result.json")
        print("- encoding_test_result.html")
        
    except Exception as e:
        print(f"渲染失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_encoding_issue()