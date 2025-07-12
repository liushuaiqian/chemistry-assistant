#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学分析链
基于LangChain实现的化学问题分析工作流
"""

import logging
from typing import Dict, Any, List, Tuple
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage
from .llm_manager import LLMManager
from tools.rag_retriever import RAGRetriever

class ChemistryAnalysisChain:
    """
    化学分析链类
    实现化学问题的链式分析处理
    """
    
    def __init__(self):
        """
        初始化化学分析链
        """
        self.logger = logging.getLogger(__name__)
        self.llm_manager = LLMManager()
        self.rag_retriever = RAGRetriever()
        self._setup_chains()
    
    def _create_rag_chain(self):
        """
        创建RAG检索链
        """
        retriever = self.rag_retriever.get_retriever(db_name='textbooks')
        if not retriever:
            return None

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | self.rag_prompt
            | self.llm_manager.get_model('zhipu')
            | StrOutputParser()
        )
        return rag_chain

    def _setup_chains(self):
        """
        设置分析链
        """
        self._rag_chain = self._create_rag_chain()

        # 问题分类提示模板
        self.classification_prompt = PromptTemplate(
            input_variables=["question"],
            template="""
你是一个化学教育专家。请分析以下化学问题的类型和难度级别。

问题: {question}

请按以下格式回答：
类型: [有机化学/无机化学/物理化学/分析化学/生物化学]
难度: [基础/中等/困难]
关键概念: [列出3-5个相关的化学概念]
解题策略: [简述解题思路]
"""
        )
        
        # 多角度分析提示模板
        self.analysis_prompt = PromptTemplate(
            input_variables=["question", "classification"],
            template="""
基于问题分类信息，请从多个角度分析这个化学问题：

问题: {question}

分类信息: {classification}

请提供：
1. 理论基础分析
2. 实验角度分析（如适用）
3. 计算方法分析（如适用）
4. 实际应用联系
5. 常见错误提醒

请确保分析全面且准确。
"""
        )
        
        # RAG 检索加强提示模板
        self.rag_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
你是一个化学专家，请根据以下背景知识来回答问题。
如果背景知识不足以回答问题，请直接说明“知识库中没有相关信息”。

背景知识:
{context}

问题: {question}
"""
        )

        # 解答生成提示模板
        self.solution_prompt = PromptTemplate(
            input_variables=["question", "classification", "analysis"],
            template="""
基于前面的分类和分析，请生成这个化学问题的完整解答：

问题: {question}

分类信息: {classification}

多角度分析: {analysis}

请提供：
1. 详细的解题步骤
2. 必要的化学方程式（使用LaTeX格式）
3. 计算过程（如适用）
4. 最终答案
5. 解题要点总结

确保解答准确、完整、易懂。
"""
        )
    
    def classify_question(self, question: str) -> str:
        """
        分类化学问题
        
        Args:
            question: 化学问题
            
        Returns:
            str: 分类结果
        """
        try:
            # 选择最适合的模型进行分类
            model_name = self._select_best_model(['zhipu', 'openai', 'tongyi'])
            if not model_name:
                return "无可用模型进行问题分类"
            
            prompt = self.classification_prompt.format(question=question)
            messages = [HumanMessage(content=prompt)]
            
            return self.llm_manager.call_model(model_name, messages)
            
        except Exception as e:
            self.logger.error(f"问题分类失败: {str(e)}")
            return f"分类失败: {str(e)}"

    def invoke_rag_chain(self, question: str) -> str:
        """
        直接调用RAG链进行问答
        """
        if not self._rag_chain:
            return "RAG功能未初始化。"
        return self._rag_chain.invoke(question)
    
    def analyze_question(self, question: str, classification: str) -> str:
        """
        多角度分析问题
        
        Args:
            question: 化学问题
            classification: 分类结果
            
        Returns:
            str: 分析结果
        """
        try:
            model_name = self._select_best_model(['zhipu', 'openai', 'tongyi'])
            if not model_name:
                return "无可用模型进行问题分析"
            
            prompt = self.analysis_prompt.format(
                question=question,
                classification=classification
            )
            messages = [HumanMessage(content=prompt)]
            
            return self.llm_manager.call_model(model_name, messages)
            
        except Exception as e:
            self.logger.error(f"问题分析失败: {str(e)}")
            return f"分析失败: {str(e)}"
    
    def generate_solution(self, question: str, classification: str, analysis: str) -> str:
        """
        生成解答
        
        Args:
            question: 化学问题
            classification: 分类结果
            analysis: 分析结果
            
        Returns:
            str: 完整解答
        """
        try:
            model_name = self._select_best_model(['zhipu', 'openai', 'tongyi'])
            if not model_name:
                return "无可用模型生成解答"
            
            prompt = self.solution_prompt.format(
                question=question,
                classification=classification,
                analysis=analysis
            )
            messages = [HumanMessage(content=prompt)]
            
            return self.llm_manager.call_model(model_name, messages, temperature=0.3)
            
        except Exception as e:
            self.logger.error(f"解答生成失败: {str(e)}")
            return f"解答生成失败: {str(e)}"
    
    def process_question_chain(self, question: str) -> Dict[str, str]:
        """
        链式处理化学问题
        
        Args:
            question: 化学问题
            
        Returns:
            Dict[str, str]: 包含各阶段结果的字典
        """
        # 首先进行RAG检索
        if self._rag_chain:
            self.logger.info("[化学分析链] 执行RAG检索...")
            rag_result = self._rag_chain.invoke(question)
            self.logger.info(f"[化学分析链] RAG结果: {rag_result[:100]}...")
            # 将RAG结果作为问题的一部分，或上下文
            question = f"背景知识: {rag_result}\n\n问题: {question}"


        try:
            self.logger.info(f"[化学分析链] 开始链式处理问题: {question[:50]}...")
            self.logger.info(f"[化学分析链] 问题长度: {len(question)}")
            

            
            # 第一步：问题分类
            self.logger.info("[化学分析链] 步骤1: 问题分类")
            classification = self.classify_question(question)
            self.logger.info(f"[化学分析链] 分类结果长度: {len(classification)}")
            
            # 第二步：多角度分析
            self.logger.info("[化学分析链] 步骤2: 多角度分析")
            analysis = self.analyze_question(question, classification)
            self.logger.info(f"[化学分析链] 分析结果长度: {len(analysis)}")
            
            # 第三步：生成解答
            self.logger.info("[化学分析链] 步骤3: 生成解答")
            solution = self.generate_solution(question, classification, analysis)
            self.logger.info(f"[化学分析链] 解答结果长度: {len(solution)}")
            
            result = {
                'question': question,
                'classification': classification,
                'analysis': analysis,
                'solution': solution,
                'chain_summary': self._generate_chain_summary(classification, analysis, solution)
            }
            
            self.logger.info("[化学分析链] 链式处理完成")
            return result
            
        except Exception as e:
            self.logger.error(f"[化学分析链] 链式处理失败: {str(e)}")
            import traceback
            self.logger.error(f"[化学分析链] 异常堆栈: {traceback.format_exc()}")
            return {
                'question': question,
                'error': f"处理失败: {str(e)}",
                'classification': '',
                'analysis': '',
                'solution': '',
                'chain_summary': ''
            }
    
    def _select_best_model(self, preferred_models: List[str]) -> str:
        """
        选择最佳可用模型
        
        Args:
            preferred_models: 优先模型列表
            
        Returns:
            str: 选中的模型名称
        """
        return "default"
    
    def _generate_chain_summary(self, classification: str, analysis: str, solution: str) -> str:
        """
        生成链式处理摘要
        
        Args:
            classification: 分类结果
            analysis: 分析结果
            solution: 解答结果
            
        Returns:
            str: 处理摘要
        """
        # 清理输入内容的编码问题
        def clean_text(text):
            if not isinstance(text, str):
                text = str(text)
            # 移除控制字符和乱码
            import re
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            # 确保UTF-8编码正确
            try:
                text = text.encode('utf-8').decode('utf-8')
            except UnicodeError:
                text = ''.join(char for char in text if ord(char) < 65536)
            return text
        
        classification = clean_text(classification)
        analysis = clean_text(analysis)
        solution = clean_text(solution)
        
        # 处理LaTeX公式格式
        def format_latex(text):
            if not text:
                return text
            
            # 将\text{}格式转换为普通文本
            import re
            text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
            
            # 确保化学方程式使用正确的LaTeX格式
            # 将化学元素符号包装在\ce{}中
            text = re.sub(r'([A-Z][a-z]?[0-9]*(?:_[0-9]+)?(?:\^[+-]?[0-9]*)?)', r'$\\ce{\1}$', text)
            
            # 处理化学方程式中的箭头
            text = re.sub(r'\\rightarrow', r'$\\rightarrow$', text)
            text = re.sub(r'→', r'$\\rightarrow$', text)
            
            # 处理数学表达式
            text = re.sub(r'\\([a-zA-Z]+)', r'$\\\1$', text)
            
            return text
        
        formatted_classification = format_latex(classification)
        formatted_analysis = format_latex(analysis)
        formatted_solution = format_latex(solution)
        
        return f"""
### 🔬 化学问题链式分析报告

**📋 问题分类**
{formatted_classification}

**🔍 多角度分析**
{formatted_analysis}

**✅ 完整解答**
{formatted_solution}

---
*本报告由LangChain化学分析链自动生成*
"""
    
    def get_chain_info(self) -> Dict[str, Any]:
        """
        获取分析链信息
        
        Returns:
            Dict[str, Any]: 链信息
        """
        return {
            'name': '化学分析链',
            'description': '基于LangChain的化学问题链式分析工具',
            'steps': ['问题分类', '多角度分析', '解答生成'],

            'features': [
                '自动问题分类',
                '多角度分析',
                '链式处理',
                '智能模型选择',
                '错误恢复'
            ]
        }