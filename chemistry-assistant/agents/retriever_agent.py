#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检索Agent
负责教材/题库检索
"""

from tools.rag_retriever import RAGRetriever

class RetrieverAgent:
    """
    检索Agent类
    负责从教材和题库中检索相关信息
    """
    
    def __init__(self):
        """
        初始化检索Agent
        """
        self.retriever = RAGRetriever()
        self.name = "检索Agent"
    
    def process(self, query, task_info, context=None):
        """
        处理用户查询
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            context (dict, optional): 上下文信息，包含其他Agent的处理结果
            
        Returns:
            str: 处理结果
        """
        # 从教材中检索相关内容
        textbook_results = self.retriever.search_textbooks(query, top_k=3)
        
        # 从题库中检索相关题目
        question_results = self.retriever.search_question_bank(query, top_k=2)
        
        # 整合检索结果
        retrieval_results = self._format_results(textbook_results, question_results)
        
        return retrieval_results
    
    def _format_results(self, textbook_results, question_results):
        """
        格式化检索结果
        
        Args:
            textbook_results (list): 教材检索结果
            question_results (list): 题库检索结果
            
        Returns:
            str: 格式化后的结果
        """
        formatted_result = "检索结果:\n\n"
        
        # 添加教材检索结果
        if textbook_results:
            formatted_result += "教材相关内容:\n"
            for i, result in enumerate(textbook_results, 1):
                formatted_result += f"[{i}] {result['title']}\n"
                formatted_result += f"相关度: {result['score']:.2f}\n"
                formatted_result += f"内容: {result['content']}\n\n"
        else:
            formatted_result += "未找到相关教材内容\n\n"
        
        # 添加题库检索结果
        if question_results:
            formatted_result += "相关题目:\n"
            for i, result in enumerate(question_results, 1):
                formatted_result += f"[{i}] 题目: {result['question']}\n"
                formatted_result += f"相关度: {result['score']:.2f}\n"
                if 'answer' in result:
                    formatted_result += f"参考答案: {result['answer']}\n\n"
                else:
                    formatted_result += "\n"
        else:
            formatted_result += "未找到相关题目\n"
        
        return formatted_result