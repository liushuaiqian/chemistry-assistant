#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据处理模块
提供数据处理和转换功能
"""

import os
import re
import json
import pandas as pd
from typing import List, Dict, Any, Union, Optional
from .logger import get_logger
from .helpers import ensure_dir, save_json, load_json

# 获取日志记录器
logger = get_logger('data_processor')

class DataProcessor:
    """
    数据处理类
    提供数据处理和转换功能
    """
    
    def __init__(self, data_dir: str):
        """
        初始化数据处理器
        
        Args:
            data_dir (str): 数据目录
        """
        self.data_dir = data_dir
        ensure_dir(data_dir)
        logger.info(f"初始化数据处理器，数据目录: {data_dir}")
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """
        加载CSV文件
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            pd.DataFrame: 数据框
        """
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except Exception as e:
            logger.error(f"加载CSV文件出错 {file_path}: {e}")
            return pd.DataFrame()
    
    def save_csv(self, df: pd.DataFrame, file_path: str) -> bool:
        """
        保存数据框为CSV文件
        
        Args:
            df (pd.DataFrame): 数据框
            file_path (str): 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            ensure_dir(directory)
            
            # 保存文件
            df.to_csv(file_path, index=False, encoding='utf-8')
            logger.info(f"保存CSV文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存CSV文件出错 {file_path}: {e}")
            return False
    
    def process_textbook(self, text: str) -> List[Dict[str, Any]]:
        """
        处理教材文本，将其分割为章节和段落
        
        Args:
            text (str): 教材文本
            
        Returns:
            List[Dict[str, Any]]: 处理后的教材数据
        """
        try:
            # 分割章节（假设章节以"第X章"或"章X"开头）
            chapter_pattern = r'(第\s*\d+\s*章|章\s*\d+)\s*([^\n]+)'
            chapters = re.split(chapter_pattern, text)
            
            result = []
            current_chapter = ""
            current_title = ""
            
            for i, part in enumerate(chapters):
                if i % 3 == 0 and i > 0:  # 章节内容
                    # 分割段落
                    paragraphs = [p.strip() for p in part.split('\n\n') if p.strip()]
                    
                    # 创建章节数据
                    chapter_data = {
                        "chapter": current_chapter,
                        "title": current_title,
                        "content": part,
                        "paragraphs": paragraphs
                    }
                    
                    result.append(chapter_data)
                elif i % 3 == 1:  # 章节标识（如"第1章"）
                    current_chapter = part.strip()
                elif i % 3 == 2:  # 章节标题
                    current_title = part.strip()
            
            logger.info(f"处理教材文本，共{len(result)}个章节")
            return result
        except Exception as e:
            logger.error(f"处理教材文本出错: {e}")
            return []
    
    def process_question_bank(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理题库数据
        
        Args:
            data (List[Dict[str, Any]]): 原始题库数据
            
        Returns:
            List[Dict[str, Any]]: 处理后的题库数据
        """
        try:
            processed_data = []
            
            for item in data:
                # 确保必要字段存在
                if 'question' not in item or not item['question']:
                    continue
                
                # 处理问题类型
                if 'type' not in item or not item['type']:
                    # 尝试根据问题内容推断类型
                    if '计算' in item['question']:
                        item['type'] = '计算题'
                    elif '选择' in item['question'] or '判断' in item['question']:
                        item['type'] = '选择题'
                    else:
                        item['type'] = '其他'
                
                # 确保答案字段存在
                if 'answer' not in item:
                    item['answer'] = ''
                
                # 添加难度级别（如果不存在）
                if 'difficulty' not in item:
                    item['difficulty'] = 'medium'
                
                processed_data.append(item)
            
            logger.info(f"处理题库数据，共{len(processed_data)}道题目")
            return processed_data
        except Exception as e:
            logger.error(f"处理题库数据出错: {e}")
            return []
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        将文本分块
        
        Args:
            text (str): 输入文本
            chunk_size (int): 块大小（字符数）
            overlap (int): 重叠大小（字符数）
            
        Returns:
            List[str]: 文本块列表
        """
        try:
            if not text:
                return []
            
            # 分割文本为句子
            sentences = re.split(r'(?<=[。！？.!?])\s*', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                # 如果当前块加上新句子不超过块大小，则添加到当前块
                if len(current_chunk) + len(sentence) <= chunk_size:
                    current_chunk += sentence
                else:
                    # 保存当前块
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # 开始新块
                    current_chunk = sentence
            
            # 添加最后一个块
            if current_chunk:
                chunks.append(current_chunk)
            
            # 处理重叠
            if overlap > 0 and len(chunks) > 1:
                overlapped_chunks = []
                
                for i in range(len(chunks)):
                    if i == 0:
                        overlapped_chunks.append(chunks[i])
                    else:
                        # 获取前一个块的末尾部分
                        prev_end = chunks[i-1][-overlap:] if len(chunks[i-1]) > overlap else chunks[i-1]
                        # 将前一个块的末尾部分添加到当前块的开头
                        overlapped_chunks.append(prev_end + chunks[i])
                
                chunks = overlapped_chunks
            
            logger.info(f"文本分块，共{len(chunks)}个块")
            return chunks
        except Exception as e:
            logger.error(f"文本分块出错: {e}")
            return [text] if text else []
    
    def prepare_data_for_embedding(self, data: List[Dict[str, Any]], key: str) -> List[str]:
        """
        准备用于嵌入的数据
        
        Args:
            data (List[Dict[str, Any]]): 数据列表
            key (str): 要提取的键
            
        Returns:
            List[str]: 提取的文本列表
        """
        try:
            texts = []
            
            for item in data:
                if key in item and item[key]:
                    if isinstance(item[key], str):
                        texts.append(item[key])
                    elif isinstance(item[key], list):
                        texts.extend([t for t in item[key] if isinstance(t, str)])
            
            logger.info(f"准备嵌入数据，共{len(texts)}条")
            return texts
        except Exception as e:
            logger.error(f"准备嵌入数据出错: {e}")
            return []
    
    def save_processed_data(self, data: Any, name: str) -> bool:
        """
        保存处理后的数据
        
        Args:
            data (Any): 数据
            name (str): 数据名称
            
        Returns:
            bool: 是否成功
        """
        try:
            file_path = os.path.join(self.data_dir, f"{name}.json")
            save_json(data, file_path)
            logger.info(f"保存处理后的数据: {name}")
            return True
        except Exception as e:
            logger.error(f"保存处理后的数据出错 {name}: {e}")
            return False
    
    def load_processed_data(self, name: str) -> Any:
        """
        加载处理后的数据
        
        Args:
            name (str): 数据名称
            
        Returns:
            Any: 加载的数据
        """
        try:
            file_path = os.path.join(self.data_dir, f"{name}.json")
            data = load_json(file_path)
            logger.info(f"加载处理后的数据: {name}")
            return data
        except Exception as e:
            logger.error(f"加载处理后的数据出错 {name}: {e}")
            return None