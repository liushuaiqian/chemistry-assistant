#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
输出清理工具
专门处理输出中的乱码、编码问题和格式化
"""

import re
import logging
from typing import Any, Dict, Union

class OutputCleaner:
    """
    输出清理器类
    负责清理和格式化各种输出内容，解决乱码和编码问题
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def clean_text(self, text: Union[str, Any]) -> str:
        """
        清理文本内容 - 只处理真正的编码问题，保留原始内容结构
        
        Args:
            text: 需要清理的文本内容
            
        Returns:
            str: 清理后的文本
        """
        try:
            # 确保输入是字符串
            if not isinstance(text, str):
                text = str(text)
            
            # 只移除真正的控制字符，保留正常的换行和制表符
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            
            # 移除明显的错误信息
            text = re.sub(r'\\Double subscripts: use braces to clarify', '', text)
            text = re.sub(r'Extra close brace or missing open brace', '', text)
            
            # 基本的空白字符清理
            text = re.sub(r'\n{3,}', '\n\n', text)  # 最多保留两个连续换行
            text = re.sub(r'[ \t]+', ' ', text)  # 合并多个空格和制表符
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"文本清理失败: {str(e)}")
            return str(text) if text else ""
    
    def _sanitize_markdown_content(self, text: str) -> str:
        """
        专门针对Markdown内容的清理，保护LaTeX公式和化学符号
        
        Args:
            text: 需要清理的Markdown文本
            
        Returns:
            str: 清理后的文本
        """
        try:
            # 基本的控制字符清理，但保留换行和制表符
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            
            # 确保代码块标记完整
            if text.count('```') % 2 != 0:
                text += '\n```'
            
            # 确保LaTeX公式标记完整
            if text.count('$$') % 2 != 0:
                text += '$$'
            
            if text.count('$') % 2 != 0:
                # 如果单个$不成对，尝试修复
                text = re.sub(r'(?<!\$)\$(?!\$)([^$]+)(?<!\$)(?!\$)', r'$\1$', text)
            
            # 移除明显的LaTeX错误信息
            text = re.sub(r'\\Double subscripts: use braces to clarify', '', text)
            text = re.sub(r'Extra close brace or missing open brace', '', text)
            
            # 规范化化学公式格式
            text = self._normalize_chemical_formulas(text)
            
            # 清理多余的空白，但保持段落结构
            text = re.sub(r'\n{4,}', '\n\n\n', text)  # 最多保留三个连续换行
            text = re.sub(r'[ \t]+', ' ', text)  # 合并多个空格和制表符
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Markdown内容清理失败: {str(e)}")
            return text
    
    def _normalize_chemical_formulas(self, text: str) -> str:
        """
        规范化化学公式格式
        
        Args:
            text: 包含化学公式的文本
            
        Returns:
            str: 规范化后的文本
        """
        try:
            # 修复常见的化学公式格式问题
            # 将简单的化学式转换为下标格式
            text = re.sub(r'\bH2O\b', 'H₂O', text)
            text = re.sub(r'\bO2\b', 'O₂', text)
            text = re.sub(r'\bH2\b', 'H₂', text)
            text = re.sub(r'\bCO2\b', 'CO₂', text)
            text = re.sub(r'\bSO2\b', 'SO₂', text)
            text = re.sub(r'\bNO2\b', 'NO₂', text)
            text = re.sub(r'\bNH3\b', 'NH₃', text)
            text = re.sub(r'\bCH4\b', 'CH₄', text)
            
            # 规范化箭头符号
            text = re.sub(r'\\rightarrow|\\to|->', '→', text)
            text = re.sub(r'\\leftarrow', '←', text)
            text = re.sub(r'\\leftrightarrow', '↔', text)
            
            # 修复破损的LaTeX化学公式
            text = re.sub(r'\\ce\{([^}]+)\}', r'\1', text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"化学公式规范化失败: {str(e)}")
            return text
    
    def clean_model_response(self, response: Union[str, Dict[str, Any]]) -> str:
        """
        清理模型响应内容 - 专门针对LangChain处理优化
        
        Args:
            response: 模型响应（字符串或字典）
            
        Returns:
            str: 清理后的响应内容
        """
        try:
            if isinstance(response, dict):
                # 如果是字典，提取主要内容
                if 'answer' in response:
                    content = response['answer']
                elif 'content' in response:
                    content = response['content']
                elif 'text' in response:
                    content = response['text']
                elif 'reasoning_content' in response:
                    # 对于DeepSeek等模型，可能有推理内容
                    content = response['reasoning_content']
                else:
                    content = str(response)
            else:
                content = str(response)
            
            # 确保内容是字符串
            if not isinstance(content, str):
                content = str(content)
            
            # 专门的Markdown和LaTeX格式保护清理
            content = self._sanitize_markdown_content(content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"模型响应清理失败: {str(e)}")
            return str(response) if response else ""
    
    def sanitize_model_output_for_fusion(self, model_output: str, model_name: str) -> str:
        """
        为融合处理清理单个模型输出，确保格式完整性
        
        Args:
            model_output: 模型输出内容
            model_name: 模型名称
            
        Returns:
            str: 清理后的输出
        """
        try:
            if not model_output or not isinstance(model_output, str):
                return ""
            
            # 专门的清理，确保Markdown结构完整
            cleaned = self._sanitize_markdown_content(model_output)
            
            # 为每个模型输出添加清晰的分隔标记
            formatted_output = f"\n\n### {model_name} 模型回答\n\n{cleaned}\n\n---\n"
            
            return formatted_output
            
        except Exception as e:
            self.logger.error(f"模型输出清理失败 ({model_name}): {str(e)}")
            return f"\n\n### {model_name} 模型回答\n\n{model_output}\n\n---\n"
    
    def clean_parallel_results(self, parallel_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        清理并行处理结果
        
        Args:
            parallel_results: 并行处理结果字典
            
        Returns:
            Dict: 清理后的结果字典
        """
        try:
            cleaned_results = {}
            
            for model_name, result in parallel_results.items():
                cleaned_result = {}
                
                for key, value in result.items():
                    if key == 'answer' and isinstance(value, str):
                        cleaned_result[key] = self.clean_model_response(value)
                    elif isinstance(value, str):
                        cleaned_result[key] = self.clean_text(value)
                    else:
                        cleaned_result[key] = value
                
                cleaned_results[model_name] = cleaned_result
            
            return cleaned_results
            
        except Exception as e:
            self.logger.error(f"并行结果清理失败: {str(e)}")
            return parallel_results
    
    def _fix_chemical_formulas(self, text: str) -> str:
        """
        修复化学公式格式
        
        Args:
            text: 包含化学公式的文本
            
        Returns:
            str: 修复后的文本
        """
        try:
            # 修复错误的LaTeX化学公式格式
            text = re.sub(r'\\ce\{\$([^}]+)\$\}', r'\\ce{\1}', text)
            text = re.sub(r'\$\\ce\{([^}]+)\}\$', r'\\ce{\1}', text)
            
            # 移除破损的LaTeX结构
            text = re.sub(r'\\\([^)]*\\\)', '', text)
            text = re.sub(r'\\\[[^\]]*\\\]', '', text)
            
            # 修复化学方程式箭头
            text = re.sub(r'\s*->\s*', r' → ', text)
            text = re.sub(r'\s*→\s*', r' → ', text)
            
            # 修复Fe2O3等化学式的显示
            text = re.sub(r'Fe2O3', r'Fe₂O₃', text)
            text = re.sub(r'H2O', r'H₂O', text)
            text = re.sub(r'O2', r'O₂', text)
            text = re.sub(r'CO2', r'CO₂', text)
            text = re.sub(r'SO2', r'SO₂', text)
            text = re.sub(r'NO2', r'NO₂', text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"化学公式修复失败: {str(e)}")
            return text
    
    def _fix_latex_formulas(self, text: str) -> str:
        """
        修复LaTeX公式格式
        
        Args:
            text: 包含LaTeX公式的文本
            
        Returns:
            str: 修复后的文本
        """
        try:
            # 移除 "Double subscripts: use braces to clarify" 错误
            text = re.sub(r'\\Double subscripts: use braces to clarify', '', text)

            # 移除错误的LaTeX格式
            text = re.sub(r'\\ce\{\$([^}]+)\$\}', r'$\1$', text)
            text = re.sub(r'\$\\ce\{([^}]+)\}\$', r'$\1$', text)
            text = re.sub(r'\\ce\{([^}]+)\}', r'\1', text)
            
            # 修复破损的LaTeX结构，但保留正常的LaTeX公式
            text = re.sub(r'\\\([^)]*\\\)', '', text)
            text = re.sub(r'\\\[[^\]]*\\\]', '', text)
            
            # 修复KaTeX不支持的LaTeX命令
            # 处理\text{}命令 - 转换为普通文本
            text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
            
            # 处理\mathrm{}命令 - 转换为普通文本
            text = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', text)
            
            # 处理\xrightarrow{}命令 - 转换为KaTeX支持的格式
            text = re.sub(r'\\xrightarrow\{([^}]*)\}', r'\\xrightarrow[]{\1}', text)
            text = re.sub(r'\\xrightarrow\[([^\]]*)\]\{([^}]*)\}', r'\\xrightarrow[\1]{\2}', text)
            
            # 处理度数符号 - 修复常见的度数符号问题
            text = re.sub(r'\^\\circ', r'^\\circ', text)
            text = re.sub(r'\\\^\\circ', r'^\\circ', text)
            text = re.sub(r'\^\\circC', r'^\\circ C', text)
            
            # 保持间距命令
            text = re.sub(r'\\,', r'\\,', text)
            
            # 修复常见的数学符号，但只在非LaTeX环境中
            # 保留LaTeX环境中的符号
            def replace_outside_latex(pattern, replacement, text):
                # 分割文本，保护$...$内的内容
                parts = re.split(r'(\$[^$]*\$)', text)
                for i in range(0, len(parts), 2):  # 只处理非LaTeX部分
                    parts[i] = re.sub(pattern, replacement, parts[i])
                return ''.join(parts)
            
            # 对于非LaTeX环境，直接转换为Unicode符号
            text = replace_outside_latex(r'\\rightarrow', r'→', text)
            text = replace_outside_latex(r'\\leftarrow', r'←', text)
            text = replace_outside_latex(r'\\Delta', r'Δ', text)
            text = replace_outside_latex(r'\\xrightarrow\{[^}]*\}', r'→', text)
            text = replace_outside_latex(r'\\text\{([^}]+)\}', r'\1', text)
            text = replace_outside_latex(r'\\mathrm\{([^}]+)\}', r'\1', text)
            text = replace_outside_latex(r'\^\\circ', r'°', text)
            text = replace_outside_latex(r'\\\^\\circ', r'°', text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"LaTeX公式修复失败: {str(e)}")
            return text
    
    def format_final_output(self, content: str, title: str = None) -> str:
        """
        格式化最终输出内容 - 专门为Gradio Markdown组件优化
        
        Args:
            content: 内容文本
            title: 可选的标题
            
        Returns:
            str: 格式化后的输出
        """
        try:
            if not content:
                return ""
            
            # 使用专门的Markdown清理
            content = self._sanitize_markdown_content(content)
            
            # 添加标题（如果提供）
            if title:
                content = f"## {title}\n\n{content}"
            
            # 确保UTF-8编码正确
            try:
                content = content.encode('utf-8').decode('utf-8')
            except UnicodeError:
                # 如果编码失败，移除有问题的字符
                content = ''.join(char for char in content if ord(char) < 65536)
            
            # 确保内容以换行结束
            if not content.endswith('\n'):
                content += '\n'
            
            return content
            
        except Exception as e:
            self.logger.error(f"最终输出格式化失败: {str(e)}")
            return str(content) if content else ""

# 创建全局实例
output_cleaner = OutputCleaner()

# 便捷函数
def clean_output(text: Union[str, Any]) -> str:
    """
    便捷的输出清理函数
    
    Args:
        text: 需要清理的文本
        
    Returns:
        str: 清理后的文本
    """
    return output_cleaner.clean_text(text)

def clean_model_output(response: Union[str, Dict[str, Any]]) -> str:
    """
    便捷的模型输出清理函数
    
    Args:
        response: 模型响应
        
    Returns:
        str: 清理后的响应
    """
    return output_cleaner.clean_model_response(response)

def clean_parallel_output(parallel_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    便捷的并行输出清理函数
    
    Args:
        parallel_results: 并行处理结果
        
    Returns:
        Dict: 清理后的结果
    """
    return output_cleaner.clean_parallel_results(parallel_results)

def format_output(content: str, title: str = None) -> str:
    """
    便捷的输出格式化函数
    
    Args:
        content: 内容文本
        title: 可选标题
        
    Returns:
        str: 格式化后的输出
    """
    return output_cleaner.format_final_output(content, title)