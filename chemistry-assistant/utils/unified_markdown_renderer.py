#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
统一Markdown渲染器
解决多层次格式化冲突，提供标准化的Markdown+MathJax+化学公式渲染管线
"""

import re
import html
import logging
from typing import Any, Dict, Union, Optional, Tuple

# 导入专业的Markdown解析库
import markdown
from markdown.extensions import tables, codehilite, toc
try:
    from pymdown import superfences, arithmatex
    PYMDOWN_AVAILABLE = True
except ImportError:
    PYMDOWN_AVAILABLE = False

class UnifiedMarkdownRenderer:
    """
    统一的Markdown渲染器
    提供标准化的内容渲染，避免多层次格式化冲突
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_markdown_processor()
    
    def _setup_markdown_processor(self):
        """设置Markdown处理器及其扩展"""
        try:
            # 基础扩展
            extensions = [
                'tables',           # 表格支持
                'codehilite',       # 代码高亮
                'toc',              # 目录生成
                'fenced_code',      # 围栏代码块
                'nl2br',            # 换行转换
                'sane_lists',       # 改进的列表处理
                'smarty',           # 智能标点
            ]
            
            # 扩展配置
            extension_configs = {
                'codehilite': {
                    'use_pygments': False,  # 不使用Pygments，避免额外依赖
                    'css_class': 'highlight'
                },
                'tables': {},
                'toc': {
                    'permalink': False,
                },
                'sane_lists': {},
            }
            
            # 如果PyMdown Extensions可用，添加更多功能
            if PYMDOWN_AVAILABLE:
                extensions.extend([
                    'pymdownx.arithmatex',  # 数学公式支持
                    'pymdownx.superfences', # 增强的代码块
                ])
                extension_configs.update({
                    'pymdownx.arithmatex': {
                        'generic': True,    # 通用数学公式支持
                    },
                    'pymdownx.superfences': {},
                })
            
            self.md_processor = markdown.Markdown(
                extensions=extensions,
                extension_configs=extension_configs,
                output_format='html',
                tab_length=4,
            )
            
        except Exception as e:
            self.logger.warning(f"高级Markdown扩展初始化失败，使用基础配置: {str(e)}")
            # 回退到基础配置
            self.md_processor = markdown.Markdown(
                extensions=['tables', 'fenced_code', 'nl2br'],
                output_format='html',
                tab_length=4,
            )
    
    def _protect_math_expressions(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        保护数学表达式，避免被Markdown处理器误解析
        
        Returns:
            tuple: (处理后的文本, 占位符映射字典)
        """
        protected_expressions = {}
        counter = 0
        
        # 保护显示数学公式 $$...$$
        def protect_display_math(match):
            nonlocal counter
            placeholder = f"PROTECTED_DISPLAY_MATH_{counter}"
            protected_expressions[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        # 保护行内数学公式 $...$
        def protect_inline_math(match):
            nonlocal counter
            placeholder = f"PROTECTED_INLINE_MATH_{counter}"
            protected_expressions[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        # 保护LaTeX命令 \ce{...}, \begin{...}\end{...} 等
        def protect_latex_commands(match):
            nonlocal counter
            placeholder = f"PROTECTED_LATEX_CMD_{counter}"
            protected_expressions[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        # 按优先级保护各种数学表达式
        text = re.sub(r'\$\$([^$]+?)\$\$', protect_display_math, text)
        text = re.sub(r'(?<!\$)\$([^$\n]+?)\$(?!\$)', protect_inline_math, text)
        text = re.sub(r'\\(?:ce|begin|end|text|frac|sqrt|sum|int|Delta|alpha|beta|gamma|theta|phi|pi|sigma|omega)\{[^}]*\}', protect_latex_commands, text)
        text = re.sub(r'\\(?:rightarrow|leftarrow|to|xrightarrow)\{[^}]*\}', protect_latex_commands, text)
        
        return text, protected_expressions
    
    def _restore_protected_expressions(self, text: str, protected_expressions: dict) -> str:
        """恢复被保护的数学表达式"""
        for placeholder, original in protected_expressions.items():
            text = text.replace(placeholder, original)
        return text
    
    def _normalize_chemical_formulas(self, text: str) -> str:
        """
        规范化化学公式格式（仅在非数学环境中）
        注意：此方法不应再次保护数学表达式，因为调用者已经处理了保护
        """
        try:
            # 化学公式下标转换映射
            subscript_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
            
            # 常见化学公式替换（只在非保护区域进行）
            chemical_replacements = {
                r'\bH2O\b': 'H₂O',
                r'\bO2\b': 'O₂', 
                r'\bH2\b': 'H₂',
                r'\bCO2\b': 'CO₂',
                r'\bSO2\b': 'SO₂',
                r'\bNO2\b': 'NO₂',
                r'\bNH3\b': 'NH₃',
                r'\bCH4\b': 'CH₄',
                r'\bSO4\b': 'SO₄',
                r'\bNO3\b': 'NO₃',
                r'\bNH4\b': 'NH₄',
                r'\bFe2O3\b': 'Fe₂O₃',
                r'\bAl2O3\b': 'Al₂O₃',
                r'\bCaCl2\b': 'CaCl₂',
                r'\bMgCl2\b': 'MgCl₂',
                r'\bH2SO4\b': 'H₂SO₄',
                r'\bHNO3\b': 'HNO₃',
                r'\bNaOH\b': 'NaOH',
                r'\bKOH\b': 'KOH',
                r'\bCa(OH)2\b': 'Ca(OH)₂',
            }
            
            # 应用化学公式替换（避免在保护的数学表达式中替换）
            for pattern, replacement in chemical_replacements.items():
                # 只在非保护区域进行替换
                if not re.search(r'PROTECTED_.*?_\d+', text):
                    text = re.sub(pattern, replacement, text)
                else:
                    # 分段处理，避免在保护区域内替换
                    parts = re.split(r'(PROTECTED_.*?_\d+)', text)
                    for i in range(0, len(parts), 2):  # 只处理非保护的部分
                        if i < len(parts):
                            parts[i] = re.sub(pattern, replacement, parts[i])
                    text = ''.join(parts)
            
            # 通用的元素+数字下标转换（更保守的匹配）
            def subscript_numbers(match):
                element = match.group(1)
                number = match.group(2)
                return element + number.translate(subscript_map)
            
            # 匹配化学元素后的数字（避免误匹配其他内容）
            if not re.search(r'PROTECTED_.*?_\d+', text):
                text = re.sub(r'\b([A-Z][a-z]?)(\d+)\b', subscript_numbers, text)
            else:
                # 分段处理，避免在保护区域内替换
                parts = re.split(r'(PROTECTED_.*?_\d+)', text)
                for i in range(0, len(parts), 2):  # 只处理非保护的部分
                    if i < len(parts):
                        parts[i] = re.sub(r'\b([A-Z][a-z]?)(\d+)\b', subscript_numbers, parts[i])
                text = ''.join(parts)
            
            # 规范化箭头符号
            if not re.search(r'PROTECTED_.*?_\d+', text):
                text = re.sub(r'\\rightarrow|\\to|->', '→', text)
                text = re.sub(r'\\leftarrow', '←', text)
                text = re.sub(r'\\leftrightarrow', '↔', text)
            else:
                # 分段处理，避免在保护区域内替换
                parts = re.split(r'(PROTECTED_.*?_\d+)', text)
                for i in range(0, len(parts), 2):  # 只处理非保护的部分
                    if i < len(parts):
                        parts[i] = re.sub(r'\\rightarrow|\\to|->', '→', parts[i])
                        parts[i] = re.sub(r'\\leftarrow', '←', parts[i])
                        parts[i] = re.sub(r'\\leftrightarrow', '↔', parts[i])
                text = ''.join(parts)
            
            return text
            
        except Exception as e:
            self.logger.error(f"化学公式规范化失败: {str(e)}")
            return text
    
    def _clean_html_tags(self, html_content: str) -> str:
        """
        清理和修复HTML标签问题
        """
        try:
            # 修复重复的span标签（针对用户报告的问题）
            html_content = re.sub(r'<span[^>]*class="chemical-equation"[^>]*>\s*<span[^>]*class="chemical-equation"[^>]*>([^<]+)</span>\s*</span>', 
                                  r'<span class="chemical-equation">\1</span>', html_content)
            
            # 清理多余的p标签嵌套
            html_content = re.sub(r'<p>\s*<p>([^<]+)</p>\s*</p>', r'<p>\1</p>', html_content)
            
            # 清理li标签内的p标签（列表项通常不需要p标签）
            html_content = re.sub(r'<li>\s*<p>([^<]+)</p>\s*</li>', r'<li>\1</li>', html_content)
            
            # 确保表格单元格内容正确
            html_content = re.sub(r'<td>\s*<p>([^<]+)</p>\s*</td>', r'<td>\1</td>', html_content)
            html_content = re.sub(r'<th>\s*<p>([^<]+)</p>\s*</th>', r'<th>\1</th>', html_content)
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"HTML标签清理失败: {str(e)}")
            return html_content
    
    def _enhance_chemical_equations_for_mathjax(self, html_content: str) -> str:
        """
        为化学方程式添加MathJax支持（可选增强）
        """
        try:
            def convert_to_mathjax(match):
                equation = match.group(1).strip()
                # 简单的化学反应转换为MathJax mhchem格式
                if any(arrow in equation for arrow in ['→', '←', '↔', '=', '+']):
                    # 清理并转换
                    cleaned = equation.replace('→', ' -> ').replace('←', ' <- ').replace('↔', ' <-> ')
                    return f'$\\ce{{{cleaned}}}$'
                return match.group(0)
            
            # 查找可能的化学方程式并转换
            # 这是可选的增强功能，保守处理
            if '→' in html_content or '←' in html_content or '↔' in html_content:
                # 仅处理明确标记的化学方程式
                html_content = re.sub(r'<span[^>]*class="chemical-equation"[^>]*>([^<]+)</span>', 
                                      convert_to_mathjax, html_content)
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"化学方程式MathJax增强失败: {str(e)}")
            return html_content
    
    def render(self, content: Any, title: Optional[str] = None) -> str:
        """
        统一的渲染入口
        
        Args:
            content: 要渲染的内容（字符串、字典或其他类型）
            title: 可选的标题
            
        Returns:
            str: 渲染后的HTML内容
        """
        try:
            # 1. 预处理：提取和规范化内容
            if isinstance(content, dict):
                # 从字典中提取主要内容
                if 'answer' in content:
                    text_content = str(content['answer'])
                elif 'content' in content:
                    text_content = str(content['content'])
                elif 'text' in content:
                    text_content = str(content['text'])
                else:
                    text_content = str(content)
            else:
                text_content = str(content) if content else ""
            
            if not text_content.strip():
                return ""
            
            # 2. 基础清理
            text_content = text_content.strip()
            
            # 移除真正的控制字符，保留正常格式
            text_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text_content)
            
            # 3. 规范化化学公式（在Markdown处理前）
            text_content = self._normalize_chemical_formulas(text_content)
            
            # 4. 保护数学表达式
            protected_text, protected_expressions = self._protect_math_expressions(text_content)
            
            # 5. Markdown渲染（核心步骤）
            html_content = self.md_processor.convert(protected_text)
            
            # 6. 恢复数学表达式
            html_content = self._restore_protected_expressions(html_content, protected_expressions)
            
            # 7. HTML清理和修复
            html_content = self._clean_html_tags(html_content)
            
            # 8. 可选的化学方程式MathJax增强
            html_content = self._enhance_chemical_equations_for_mathjax(html_content)
            
            # 9. 添加标题（如果需要）
            if title:
                html_content = f"<h2>{html.escape(title)}</h2>\n{html_content}"
            
            # 10. 重置Markdown处理器状态（重要！）
            self.md_processor.reset()
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"统一渲染失败: {str(e)}")
            # 失败时的安全回退
            fallback_content = html.escape(str(content)) if content else ""
            if title:
                fallback_content = f"<h2>{html.escape(title)}</h2>\n<p>{fallback_content}</p>"
            return fallback_content
    
    def render_comparison(self, comparison_data: Any) -> str:
        """渲染比较结果"""
        return self.render(comparison_data, "模型对比结果")
    
    def render_chain_result(self, chain_data: Any) -> str:
        """渲染链式处理结果"""
        return self.render(chain_data, "链式处理结果")
    
    def render_error(self, error: Exception, context: str = "") -> str:
        """渲染错误消息"""
        error_content = f"❌ **处理出错**\n\n"
        if context:
            error_content += f"**错误上下文**: {context}\n\n"
        error_content += f"**错误信息**: {str(error)}\n\n"
        error_content += "请检查输入内容或联系技术支持。"
        
        return self.render(error_content)
    
    def render_status(self, status: str, details: str = "") -> str:
        """渲染状态消息"""
        status_content = f"ℹ️ **状态信息**: {status}"
        if details:
            status_content += f"\n\n**详细信息**: {details}"
        
        return self.render(status_content)

# 创建全局实例
unified_renderer = UnifiedMarkdownRenderer()

# 便捷函数
def render_content(content: Any, title: Optional[str] = None) -> str:
    """
    便捷的内容渲染函数
    
    Args:
        content: 要渲染的内容
        title: 可选标题
        
    Returns:
        str: 渲染后的HTML
    """
    return unified_renderer.render(content, title)

def render_comparison_output(comparison_data: Any) -> str:
    """便捷的比较输出渲染函数"""
    return unified_renderer.render_comparison(comparison_data)

def render_chain_result(chain_data: Any) -> str:
    """便捷的链式结果渲染函数"""
    return unified_renderer.render_chain_result(chain_data)

def render_error_message(error: Exception, context: str = "") -> str:
    """便捷的错误消息渲染函数"""
    return unified_renderer.render_error(error, context)

def render_status_message(status: str, details: str = "") -> str:
    """便捷的状态消息渲染函数"""
    return unified_renderer.render_status(status, details)