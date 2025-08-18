#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web UI 格式化工具
专门为Gradio等Web界面提供统一的输出格式化功能
整合了输出清理、Markdown格式化、LaTeX渲染等功能
"""

import re
import json
import ast
import logging
from typing import Any, Dict, Union, Optional

# 导入基础的输出清理器
from .output_cleaner import output_cleaner

# 新增：集成 LangChain 的输出解析工具
try:
    from langchain_core.output_parsers import StrOutputParser
    try:
        # JsonOutputParser 在较新版本中位于 langchain_core
        from langchain_core.output_parsers import JsonOutputParser  # type: ignore
    except Exception:  # 兼容旧版本
        JsonOutputParser = None  # type: ignore
except Exception:
    # 如果未安装 LangChain，保持兼容
    StrOutputParser = None  # type: ignore
    JsonOutputParser = None  # type: ignore

class WebUIFormatter:
    """
    Web UI 格式化器类
    专门为Web界面优化的输出格式化工具
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cleaner = output_cleaner
    
    def parse_raw_output(self, raw_output: Any) -> Any:
        """
        解析原始输出，处理JSON字符串、Python字面量或普通字符串
        
        Args:
            raw_output: 原始输出数据
            
        Returns:
            Any: 解析后的数据
        """
        if not raw_output:
            return ""
        
        data = None
        if isinstance(raw_output, str):
            try:
                # 尝试解析为JSON
                data = json.loads(raw_output)
            except (json.JSONDecodeError, TypeError):
                try:
                    # 检查字符串是否包含LaTeX公式或化学符号，如果包含则不使用ast.literal_eval
                    if any(pattern in raw_output for pattern in ['$', '\\', 'products', 'reactants', '\\sum', '\\Delta']):
                        # 直接保持为字符串，避免LaTeX公式被误解析为Python代码
                        data = raw_output
                    else:
                        # 尝试解析为Python字面量
                        data = ast.literal_eval(raw_output)
                except (ValueError, SyntaxError, TypeError):
                    # 保持为字符串
                    data = raw_output
        else:
            data = raw_output
        
        return data
    
    def extract_core_answer(self, data: Any) -> Any:
        """
        从数据中提取核心答案内容
        
        Args:
            data: 解析后的数据
            
        Returns:
            Any: 提取的核心答案
        """
        if isinstance(data, dict):
            # 按优先级提取答案
            for key in ['integrated_answer', 'answer', 'solution', 'content', 'text', 'result']:
                if key in data and data[key]:
                    return data[key]
            
            # 如果没有找到标准字段，检查是否有错误信息
            if 'error' in data:
                return data['error']
            
            # 返回整个字典
            return data
        
        return data
    
    def format_structured_data(self, data: Any) -> str:
        """
        格式化结构化数据（字典、列表等）
        
        Args:
            data: 需要格式化的数据
            
        Returns:
            str: 格式化后的字符串
        """
        if isinstance(data, dict):
            # 字典格式化为美化的JSON
            return f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"
        elif isinstance(data, list):
            # 列表每项占一行
            return "\n".join(str(item) for item in data)
        else:
            # 其他情况转为字符串
            return str(data)
    
    def _format_chemical_subscripts(self, text: str) -> str:
        """
        使用正则表达式将化学式中的数字转换为下标。
        例如: C2H4 -> C₂H₄
        但要避免影响LaTeX环境内的内容
        """
        subscript_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

        def replace_with_subscript(match):
            # 对于CH4这样的，只对数字进行下标转换
            element = match.group(1)
            number = match.group(2)
            return element + number.translate(subscript_map)

        # 定义函数来只在LaTeX环境外进行替换
        def replace_outside_latex(text):
            # 分割文本，保护$...$内的内容
            parts = re.split(r'(\$[^$]*\$)', text)
            for i in range(0, len(parts), 2):  # 只处理非LaTeX部分
                # 匹配一个或多个字母（元素）后跟一个或多个数字
                # 正向预测确保我们只在数字后跟空格、字母或行尾时进行替换，避免错误匹配
                parts[i] = re.sub(r"([A-Za-z]+)(\d+)(?=[\sA-Za-z]|$)", replace_with_subscript, parts[i])
            return ''.join(parts)
        
        return replace_outside_latex(text)

    def apply_chemistry_formatting(self, text: str) -> str:
        """
        应用化学专用格式化
        
        Args:
            text: 需要格式化的文本
            
        Returns:
            str: 格式化后的文本
        """
        try:
            # 1. 使用基础的箭头和公式规范化
            text = self.cleaner._normalize_chemical_formulas(text)
            
            # 2. 动态地将所有公式中的数字转换为下标（但避免LaTeX环境）
            text = self._format_chemical_subscripts(text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"化学格式化失败: {str(e)}")
            return text
    
    def apply_latex_formatting(self, text: str) -> str:
        """
        应用LaTeX数学公式格式化
        
        Args:
            text: 需要格式化的文本
            
        Returns:
            str: 格式化后的文本
        """
        try:
            # 使用output_cleaner的LaTeX修复
            text = self.cleaner._fix_latex_formulas(text)
            
            # 确保LaTeX公式标记完整
            if text.count('$$') % 2 != 0:
                text += '$$'
            
            # 修复不成对的$符号，但要更小心
            dollar_count = text.count('$')
            if dollar_count % 2 != 0:
                # 如果$符号数量为奇数，在末尾添加一个$
                text += '$'
            
            # 定义一个函数来只在LaTeX环境外替换符号
            def replace_outside_latex(pattern, replacement, text):
                # 分割文本，保护$...$内的内容
                parts = re.split(r'(\$[^$]*\$)', text)
                for i in range(0, len(parts), 2):  # 只处理非LaTeX部分
                    parts[i] = re.sub(pattern, replacement, parts[i])
                return ''.join(parts)
            
            # 修复常见的数学符号，但只在LaTeX环境外
            math_replacements = {
                r'\\pm': '±',
                r'\\times': '×',
                r'\\div': '÷',
                r'\\leq': '≤',
                r'\\geq': '≥',
                r'\\neq': '≠',
                r'\\approx': '≈',
                r'\\infty': '∞',
                r'\\alpha': 'α',
                r'\\beta': 'β',
                r'\\gamma': 'γ',
                r'\\delta': 'δ',
                r'\\epsilon': 'ε',
                r'\\theta': 'θ',
                r'\\lambda': 'λ',
                r'\\mu': 'μ',
                r'\\pi': 'π',
                r'\\sigma': 'σ',
                r'\\phi': 'φ',
                r'\\omega': 'ω',
            }
            
            for pattern, replacement in math_replacements.items():
                text = replace_outside_latex(pattern, replacement, text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"LaTeX格式化失败: {str(e)}")
            return text
    
    def optimize_table_equations(self, text: str) -> str:
        """
        优化表格中的化学方程式显示
        
        Args:
            text: 需要优化的文本
            
        Returns:
            str: 优化后的文本
        """
        try:
            # 检查文本是否已包含chemical-equation类，避免重复格式化
            if 'class="chemical-equation"' in text:
                self.logger.debug("文本已包含化学方程式格式化标签，跳过处理")
                return text
            
            # 更精确的化学方程式判定函数
            def is_likely_chemical_equation(content: str) -> bool:
                """判断内容是否可能是化学方程式"""
                content = content.strip()
                
                # 检查是否已经是 MathJax 格式（避免重复处理）
                if content.startswith(('$', '\\(', '\\[', '\\ce{', '\\cee{')):
                    return False
                
                # 检查是否已经是HTML标签（避免重复处理）
                if content.startswith('<') and content.endswith('>'):
                    return False
                
                # 化学方程式的特征模式
                chemical_patterns = [
                    r'[A-Z][a-z]?[\d₀-₉]*\s*[+\-→←↔=]\s*[A-Z][a-z]?',  # 化学反应式
                    r'[A-Z][a-z]?[\d₀-₉]*\s*\+\s*[A-Z][a-z]?[\d₀-₉]*\s*→',  # 反应箭头
                    r'[A-Z][a-z]?[\d₀-₉]*\s*=\s*[A-Z][a-z]?[\d₀-₉]*',  # 等号连接的化学式
                    r'[\d\s]*[A-Z][a-z]?[\d₀-₉]*[\(\)]?[\d₀-₉]*\s*[→←↔]\s*[\d\s]*[A-Z][a-z]?',  # 带系数的反应
                ]
                
                # 常见化学符号和离子
                chemical_symbols = [
                    'H₂O', 'CO₂', 'SO₄', 'NO₃', 'NH₄', 'OH⁻', 'Cl⁻', 'Na⁺', 'K⁺', 'Ca²⁺', 'Mg²⁺',
                    'H2O', 'CO2', 'SO4', 'NO3', 'NH4', 'NaCl', 'KCl', 'CaCl2', 'MgCl2',
                    'Al₂O₃', 'Fe₂O₃', 'CuSO₄', 'AgNO₃', 'BaSO₄', 'Al2O3', 'Fe2O3', 'CuSO4'
                ]
                
                # 反应条件和箭头
                reaction_indicators = ['→', '←', '↔', '⇌', '→', '⟶', '⟵', '⇄']
                
                # 检查是否包含化学反应特征
                has_chemical_pattern = any(re.search(pattern, content) for pattern in chemical_patterns)
                has_chemical_symbols = any(symbol in content for symbol in chemical_symbols)
                has_reaction_arrow = any(arrow in content for arrow in reaction_indicators)
                
                # 排除纯文本描述（如包含过多中文或英文单词）
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
                english_words = len(re.findall(r'\b[a-zA-Z]{3,}\b', content))
                
                # 如果中文字符或长英文单词过多，可能不是化学方程式
                if chinese_chars > 5 or english_words > 3:
                    # 除非明确包含反应箭头
                    return has_reaction_arrow
                
                # 综合判断
                return (has_chemical_pattern or (has_chemical_symbols and has_reaction_arrow))
            
            # 检测表格中的化学方程式并添加CSS类
            def add_equation_class(match):
                content = match.group(1).strip()
                
                # 检查是否已包含HTML标签，避免重复处理
                if '<span' in content and 'chemical-equation' in content:
                    return match.group(0)
                
                # 使用精确判定
                if is_likely_chemical_equation(content):
                    # 添加无障碍属性和语义角色
                    return f'| <span class="chemical-equation" role="math" aria-label="化学方程式: {content}" title="化学方程式">{content}</span> |'
                return match.group(0)
            
            # 匹配表格中可能包含化学内容的单元格
            # 不再硬编码为第二列，而是检查所有单元格
            text = re.sub(r'\|\s*([^|]+)\s*\|', add_equation_class, text)
            
            # 处理可能的 MathJax 化学方程式转换
            text = self._convert_chemical_to_mathjax(text)
            
            # 确保表格格式正确
            lines = text.split('\n')
            formatted_lines = []
            
            for line in lines:
                if '|' in line and not line.strip().startswith('|'):
                    # 修复表格格式
                    line = '|' + line if not line.startswith('|') else line
                    line = line + '|' if not line.endswith('|') else line
                    # 规范化空格
                    line = re.sub(r'\s*\|\s*', ' | ', line)
                    line = re.sub(r'^\s*\|\s*', '| ', line)
                    line = re.sub(r'\s*\|\s*$', ' |', line)
                
                formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            self.logger.error(f"表格方程式优化失败: {str(e)}")
            return text
    
    def _convert_chemical_to_mathjax(self, text: str) -> str:
        """
        将识别出的化学方程式转换为 MathJax 格式（可选优化）
        
        Args:
            text: 包含化学方程式的文本
            
        Returns:
            str: 转换后的文本
        """
        try:
            # 简单的化学方程式转 \ce{} 格式
            def convert_to_ce(match):
                equation = match.group(1)
                # 简单转换：如果包含明显的化学反应
                if any(arrow in equation for arrow in ['→', '←', '↔', '=']):
                    # 清理并转换为 MathJax mhchem 格式
                    cleaned = equation.replace('→', ' -> ').replace('←', ' <- ').replace('↔', ' <-> ')
                    return f'$\\ce{{{cleaned}}}$'
                return match.group(0)
            
            # 修改正则表达式以匹配带有完整属性的chemical-equation span标签
            # 匹配 <span class="chemical-equation" role="math" aria-label="..." title="...">...</span>
            pattern = r'<span[^>]*class="chemical-equation"[^>]*>([^<]+)</span>'
            text = re.sub(pattern, convert_to_ce, text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"化学方程式MathJax转换失败: {str(e)}")
            return text
    
    def _format_with_langchain_parsers(self, data: Any) -> Optional[str]:
        """使用 LangChain 的输出解析器优先格式化输出。
        - 优先尝试 JsonOutputParser，将结构化结果以 JSON 代码块形式美观展示；
        - 回退到 StrOutputParser，确保文本输出被可靠清洗；
        - 如果 LangChain 不可用或解析失败，返回 None 以走原有逻辑。
        """
        try:
            # 如果没有安装 LangChain，直接返回 None
            if StrOutputParser is None and JsonOutputParser is None:
                return None
            
            # 直接处理字典/列表：优先以 JSON 代码块形式展示
            if isinstance(data, (dict, list)):
                pretty = json.dumps(data, ensure_ascii=False, indent=2)
                return f"```json\n{pretty}\n```"
            
            # 处理字符串
            if isinstance(data, str):
                # 优先尝试 JSON 解析（仅当看起来像JSON时）
                looks_like_json = data.strip().startswith(('{', '[')) and data.strip().endswith(('}', ']'))
                if JsonOutputParser is not None and looks_like_json:
                    try:
                        parsed = JsonOutputParser().parse(data)  # type: ignore
                        pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
                        return f"```json\n{pretty}\n```"
                    except Exception:
                        # JSON 解析失败则回退
                        pass
                
                # 使用 StrOutputParser 进行纯文本解析清洗
                if StrOutputParser is not None:
                    try:
                        parsed_text = StrOutputParser().parse(data)
                        return str(parsed_text)
                    except Exception:
                        pass
                # 最后回退为原文本
                return str(data)
            
            # 其他类型，交给默认逻辑
            return None
        except Exception as e:
            # 为安全起见，任何异常都不影响原有流程
            self.logger.debug(f"LangChain解析器格式化失败: {e}")
            return None

    def clean_and_format_for_web(self, raw_output: Any, title: Optional[str] = None) -> str:
        """
        统一的Web UI输出清理和格式化函数
        这是主要的对外接口，整合了所有格式化功能
        
        Args:
            raw_output: 原始输出数据
            title: 可选的标题
            
        Returns:
            str: 清理和格式化后的文本
        """
        try:
            # 1. 解析原始输出
            data = self.parse_raw_output(raw_output)
            
            # 2. 提取核心答案
            answer = self.extract_core_answer(data)
            
            # 2.5 优先尝试使用 LangChain 的输出解析器进行格式化（若可用）
            lc_formatted = self._format_with_langchain_parsers(answer)
            if lc_formatted is not None:
                formatted_text = lc_formatted
            else:
                # 3. 原有格式化逻辑
                if isinstance(answer, (dict, list)):
                    formatted_text = self.format_structured_data(answer)
                else:
                    formatted_text = str(answer)
            
            # 4. 使用基础清理器清理
            cleaned_text = self.cleaner.clean_model_response(formatted_text)
            
            # 5. 应用化学专用格式化
            cleaned_text = self.apply_chemistry_formatting(cleaned_text)
            
            # 6. 应用LaTeX格式化
            cleaned_text = self.apply_latex_formatting(cleaned_text)
            
            # 7. 优化表格中的化学方程式显示
            cleaned_text = self.optimize_table_equations(cleaned_text)
            
            # 8. 最终格式化输出
            final_output = self.cleaner.format_final_output(cleaned_text, title)
            
            return final_output
            
        except Exception as e:
            self.logger.error(f"Web UI格式化失败: {str(e)}")
            return str(raw_output) if raw_output else ""
    
    def format_comparison_output(self, comparison_data: Any) -> str:
        """
        格式化比较输出（用于模型对比等场景）
        
        Args:
            comparison_data: 比较数据
            
        Returns:
            str: 格式化后的比较输出
        """
        return self.clean_and_format_for_web(comparison_data, "模型对比结果")
    
    def format_chain_result(self, chain_data: Any) -> str:
        """
        格式化链式处理结果（用于LangChain等场景）
        
        Args:
            chain_data: 链式处理数据
            
        Returns:
            str: 格式化后的链式结果
        """
        return self.clean_and_format_for_web(chain_data, "链式处理结果")
    
    def format_error_message(self, error: Exception, context: str = "") -> str:
        """
        格式化错误消息
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            str: 格式化后的错误消息
        """
        error_msg = f"❌ **处理出错**\n\n"
        if context:
            error_msg += f"**错误上下文**: {context}\n\n"
        error_msg += f"**错误信息**: {str(error)}\n\n"
        error_msg += "请检查输入内容或联系技术支持。"
        
        return self.cleaner.format_final_output(error_msg)
    
    def format_status_message(self, status: str, details: str = "") -> str:
        """
        格式化状态消息
        
        Args:
            status: 状态信息
            details: 详细信息
            
        Returns:
            str: 格式化后的状态消息
        """
        status_msg = f"ℹ️ **状态信息**: {status}"
        if details:
            status_msg += f"\n\n**详细信息**: {details}"
        
        return self.cleaner.format_final_output(status_msg)

# 创建全局实例
web_ui_formatter = WebUIFormatter()

# 便捷函数
def clean_and_format_output(raw_output: Any, title: Optional[str] = None) -> str:
    """
    便捷的Web UI输出格式化函数
    
    Args:
        raw_output: 原始输出数据
        title: 可选标题
        
    Returns:
        str: 格式化后的输出
    """
    return web_ui_formatter.clean_and_format_for_web(raw_output, title)

def format_comparison_output(comparison_data: Any) -> str:
    """
    便捷的比较输出格式化函数
    
    Args:
        comparison_data: 比较数据
        
    Returns:
        str: 格式化后的比较输出
    """
    return web_ui_formatter.format_comparison_output(comparison_data)

def format_chain_result(chain_data: Any) -> str:
    """
    便捷的链式结果格式化函数
    
    Args:
        chain_data: 链式处理数据
        
    Returns:
        str: 格式化后的链式结果
    """
    return web_ui_formatter.format_chain_result(chain_data)

def format_error_message(error: Exception, context: str = "") -> str:
    """
    便捷的错误消息格式化函数
    
    Args:
        error: 异常对象
        context: 错误上下文
        
    Returns:
        str: 格式化后的错误消息
    """
    return web_ui_formatter.format_error_message(error, context)

def format_status_message(status: str, details: str = "") -> str:
    """
    便捷的状态消息格式化函数
    
    Args:
        status: 状态信息
        details: 详细信息
        
    Returns:
        str: 格式化后的状态消息
    """
    return web_ui_formatter.format_status_message(status, details)