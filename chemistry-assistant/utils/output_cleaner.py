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
    
    def clean_model_response(self, response: Union[str, Dict[str, Any]]) -> str:
        """
        清理模型响应内容 - 只处理真正的编码和格式问题
        
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
            
            # 只进行基本的文本清理，不破坏LaTeX和化学公式结构
            content = self.clean_text(content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"模型响应清理失败: {str(e)}")
            return str(response) if response else ""
    
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
            text = re.sub(r'\\ce\{\$([^}]+)\$\}', r'\1', text)
            text = re.sub(r'\$\\ce\{([^}]+)\}\$', r'\1', text)
            text = re.sub(r'\\ce\{([^}]+)\}', r'\1', text)
            
            # 清理多余的$符号
            text = re.sub(r'\$+([^$]*?)\$+', r'\1', text)
            text = re.sub(r'\$([^$]*)\$', r'\1', text)
            
            # 移除破损的LaTeX结构
            text = re.sub(r'\\\([^)]*\\\)', '', text)
            text = re.sub(r'\\\[[^\]]*\\\]', '', text)
            
            # 修复常见的数学符号
            text = re.sub(r'\\rightarrow', r'→', text)
            text = re.sub(r'\\leftarrow', r'←', text)
            text = re.sub(r'\\Delta', r'Δ', text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"LaTeX公式修复失败: {str(e)}")
            return text
    
    def format_final_output(self, content: str, title: str = None) -> str:
        """
        格式化最终输出内容
        
        Args:
            content: 内容文本
            title: 可选的标题
            
        Returns:
            str: 格式化后的输出
        """
        try:
            # 清理内容
            content = self.clean_text(content)
            
            # 添加标题（如果提供）
            if title:
                title = self.clean_text(title)
                content = f"## {title}\n\n{content}"
            
            # 确保段落间有适当的间距
            content = re.sub(r'\n([^\n])', r'\n\n\1', content)
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            return content.strip()
            
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