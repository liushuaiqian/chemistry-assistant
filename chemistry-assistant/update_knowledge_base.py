#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识库更新脚本
用于强制重新构建知识库索引
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.rag_retriever import RAGRetriever
from config import KNOWLEDGE_CONFIG
from utils import get_logger

def main():
    """
    完整更新知识库
    """
    print("开始更新知识库...")
    
    # 使用force_recreate参数强制重新创建知识库
    print("强制重新创建知识库索引...")
    retriever = RAGRetriever(force_recreate=True)
    
    print("知识库更新完成!")
    return retriever

def update_textbooks_only():
    """
    仅更新教材索引
    """
    print("开始更新教材索引...")
    
    # 创建RAGRetriever实例并强制重新创建教材索引
    retriever = RAGRetriever()
    retriever.create_textbook_index(force_recreate=True)
    
    print("教材索引更新完成!")
    return retriever

def update_questions_only():
    """
    仅更新题库索引
    """
    print("开始更新题库索引...")
    
    # 创建RAGRetriever实例并强制重新创建题库索引
    retriever = RAGRetriever()
    retriever.create_question_bank_index(force_recreate=True)
    
    print("题库索引更新完成!")
    return retriever

def clean_and_update():
    """
    清理现有索引并重新创建
    """
    print("开始清理并更新知识库...")
    
    # 删除现有的向量存储
    vector_store_path = KNOWLEDGE_CONFIG['vector_store_path']
    if os.path.exists(vector_store_path):
        print(f"删除现有向量存储: {vector_store_path}")
        shutil.rmtree(vector_store_path)
    
    # 重新创建知识库
    print("重新创建知识库索引...")
    retriever = RAGRetriever()
    
    print("知识库清理并更新完成!")
    return retriever

def check_knowledge_base_status():
    """
    检查知识库状态
    """
    print("检查知识库状态...")
    
    vector_store_path = KNOWLEDGE_CONFIG['vector_store_path']
    textbooks_path = os.path.join(vector_store_path, 'textbooks')
    questions_path = os.path.join(vector_store_path, 'questions')
    
    print(f"向量存储路径: {vector_store_path}")
    print(f"教材索引存在: {os.path.exists(textbooks_path)}")
    print(f"题库索引存在: {os.path.exists(questions_path)}")
    
    if os.path.exists(textbooks_path):
        textbooks_files = os.listdir(textbooks_path)
        print(f"教材索引文件: {textbooks_files}")
    
    if os.path.exists(questions_path):
        questions_files = os.listdir(questions_path)
        print(f"题库索引文件: {questions_files}")
    
    # 检查数据源路径
    textbooks_data_path = KNOWLEDGE_CONFIG['textbooks_path']
    question_bank_data_path = KNOWLEDGE_CONFIG['question_bank_path']
    
    print(f"\n数据源路径:")
    print(f"教材数据路径: {textbooks_data_path} (存在: {os.path.exists(textbooks_data_path)})")
    print(f"题库数据路径: {question_bank_data_path} (存在: {os.path.exists(question_bank_data_path)})")
    
    # 统计数据文件数量
    if os.path.exists(textbooks_data_path):
        textbook_files = []
        for root, dirs, files in os.walk(textbooks_data_path):
            for file in files:
                if file.endswith(('.txt', '.md', '.pdf', '.xlsx', '.xls')):
                    textbook_files.append(file)
        print(f"教材数据文件数量: {len(textbook_files)}")
    
    if os.path.exists(question_bank_data_path):
        question_files = []
        for root, dirs, files in os.walk(question_bank_data_path):
            for file in files:
                if file.endswith(('.txt', '.md', '.pdf', '.xlsx', '.xls')):
                    question_files.append(file)
        print(f"题库数据文件数量: {len(question_files)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='知识库更新脚本')
    parser.add_argument('--mode', choices=['all', 'textbooks', 'questions', 'clean', 'status'], 
                       default='all', help='更新模式: all(强制重新创建), textbooks(仅更新教材), questions(仅更新题库), clean(清理后重建), status(检查状态)')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'all':
            main()
        elif args.mode == 'textbooks':
            update_textbooks_only()
        elif args.mode == 'questions':
            update_questions_only()
        elif args.mode == 'clean':
            clean_and_update()
        elif args.mode == 'status':
            check_knowledge_base_status()
    except Exception as e:
        print(f"更新过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)