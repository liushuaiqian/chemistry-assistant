#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAG检索器
提供FAISS检索接口，用于检索教材和题库
"""

import os
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from config import KNOWLEDGE_CONFIG
from models.embedding_model import EmbeddingModel
from .text_reranker import TextReranker
from .adaptive_retrieval_strategy import AdaptiveRetrievalStrategy

class RAGRetriever:
    """
    基于LangChain的RAG检索器
    """

    def __init__(self, force_recreate=False, use_reranker=True, enable_adaptive=True):
        self.embedding_model = EmbeddingModel()
        self.vector_store_path = KNOWLEDGE_CONFIG['vector_store_path']
        if not os.path.exists(self.vector_store_path):
            os.makedirs(self.vector_store_path)
        self.textbooks_path = KNOWLEDGE_CONFIG['textbooks_path']
        self.question_bank_path = KNOWLEDGE_CONFIG['question_bank_path']
        self.force_recreate = force_recreate
        
        # 初始化文本排序器
        self.use_reranker = use_reranker
        if use_reranker:
            self.text_reranker = TextReranker()
            if self.text_reranker.is_available():
                print("文本排序器已启用，将使用双阶段检索（向量检索+排序）")
            else:
                print("文本排序器不可用，使用传统向量检索")
                self.use_reranker = False
        else:
            self.text_reranker = None
            print("使用传统向量检索模式")

        self.textbook_db = self._load_vector_store('textbooks')
        self.question_db = self._load_vector_store('questions')
        
        # 初始化自适应检索策略
        self.enable_adaptive = enable_adaptive
        if enable_adaptive:
            try:
                from .chemistry_solver import ChemistrySolver
                chemistry_solver = ChemistrySolver()
                self.adaptive_strategy = AdaptiveRetrievalStrategy(self, chemistry_solver)
                print("自适应检索策略已启用")
            except Exception as e:
                print(f"自适应检索策略初始化失败: {e}，使用传统检索模式")
                self.adaptive_strategy = None
                self.enable_adaptive = False
        else:
            self.adaptive_strategy = None
            print("使用传统检索模式（未启用自适应）")

    def _load_vector_store(self, name):
        index_path = os.path.join(self.vector_store_path, name)
        if os.path.exists(index_path) and not self.force_recreate:
            print(f"Loading existing {name} vector store.")
            return FAISS.load_local(index_path, self.embedding_model, allow_dangerous_deserialization=True)
        else:
            if self.force_recreate:
                print(f"Force recreating {name} vector store...")
            else:
                print(f"{name} vector store not found. Automatically creating it...")
            if name == 'textbooks':
                return self._create_index('textbooks', self.textbooks_path)
            elif name == 'questions':
                return self._create_index('questions', self.question_bank_path)
            else:
                print(f"Unknown vector store name: {name}")
                return None

    def _create_index(self, name, data_path):
        print(f"Creating {name} index from path: {data_path}")
        if not os.path.exists(data_path):
            print(f"Data path not found: {data_path}")
            return None
    
        documents = []
        
        # 处理文本文件 (.txt)
        try:
            text_loader = DirectoryLoader(
                data_path, 
                glob="**/*.txt",
                loader_cls=UnstructuredFileLoader,
                show_progress=True,
                silent_errors=True
            )
            text_docs = text_loader.load()
            documents.extend(text_docs)
            print(f"Loaded {len(text_docs)} text files")
        except Exception as e:
            print(f"Error loading text files: {e}")
        
        # 处理Markdown文件 - 使用TextLoader
        try:
            from langchain_community.document_loaders import TextLoader
            md_files = []
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        try:
                            loader = TextLoader(file_path, encoding='utf-8')
                            md_docs = loader.load()
                            md_files.extend(md_docs)
                            print(f"Loaded markdown file: {file}")
                        except Exception as e:
                            print(f"Error loading {file_path}: {e}")
            documents.extend(md_files)
            print(f"Total markdown files loaded: {len(md_files)}")
        except Exception as e:
            print(f"Error processing markdown files: {e}")
        
        # 处理PDF文件
        try:
            from langchain_community.document_loaders import PyPDFLoader
            pdf_files = []
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        try:
                            loader = PyPDFLoader(file_path)
                            pdf_docs = loader.load()
                            pdf_files.extend(pdf_docs)
                            print(f"Loaded PDF file: {file}")
                        except Exception as e:
                            print(f"Error loading {file_path}: {e}")
            documents.extend(pdf_files)
            print(f"Total PDF files loaded: {len(pdf_files)}")
        except ImportError:
            print("PyPDFLoader not available, skipping .pdf files")
        
        # 处理Excel文件 - 使用pandas读取然后转换为文档
        try:
            import pandas as pd
            from langchain.schema import Document
            excel_files = []
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(root, file)
                        try:
                            # 使用pandas读取Excel文件
                            df = pd.read_excel(file_path)
                            # 将DataFrame转换为文本
                            content = df.to_string(index=False)
                            # 创建Document对象
                            doc = Document(
                                page_content=content,
                                metadata={"source": file_path, "file_type": "excel"}
                            )
                            excel_files.append(doc)
                            print(f"Loaded Excel file: {file}")
                        except Exception as e:
                            print(f"Error loading {file_path}: {e}")
            documents.extend(excel_files)
            print(f"Total Excel files loaded: {len(excel_files)}")
        except ImportError:
            print("pandas not available, skipping Excel files")
    
        if not documents:
            print("No documents found to index.")
            return None
    
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(documents)
    
        if not docs:
            print("No document chunks created after splitting.")
            return None
    
        print(f"Creating FAISS index for {len(docs)} document chunks from {len(documents)} documents.")
        db = FAISS.from_documents(docs, self.embedding_model)
        index_path = os.path.join(self.vector_store_path, name)
        db.save_local(index_path)
        print(f"{name} index created successfully.")
        return db

    def create_textbook_index(self, force_recreate=False):
        if force_recreate:
            self.force_recreate = True
        self.textbook_db = self._create_index('textbooks', self.textbooks_path)

    def create_question_bank_index(self, force_recreate=False):
        if force_recreate:
            self.force_recreate = True
        self.question_db = self._create_index('questions', self.question_bank_path)

    def search_textbooks(self, query, k=3):
        if self.textbook_db:
            return self.textbook_db.similarity_search(query, k=k)
        return []

    def retrieve_from_textbooks(self, query, k=5, rerank_top_n=None):
        """
        从教材中检索相关信息
        
        Args:
            query (str): 查询文本
            k (int): 向量检索返回的文档数量
            rerank_top_n (int): 排序后返回的文档数量，默认为k
        """
        if self.textbook_db is None:
            return []
        
        try:
            # 第一阶段：向量检索
            if self.use_reranker and self.text_reranker.is_available():
                # 使用更大的k值进行初步检索
                initial_k = max(k * 3, 20)  # 扩大检索范围
                docs = self.textbook_db.similarity_search(query, k=initial_k)
                
                if docs:
                    # 第二阶段：文本排序
                    rerank_top_n = rerank_top_n or k
                    ranked_docs = self.text_reranker.rerank_langchain_docs(
                        query, docs, top_n=rerank_top_n
                    )
                    return [doc.page_content for doc in ranked_docs]
                else:
                    return []
            else:
                # 传统向量检索
                docs = self.textbook_db.similarity_search(query, k=k)
                return [doc.page_content for doc in docs]
                
        except Exception as e:
            print(f"教材检索错误: {e}")
            return []

    def search_question_bank(self, query, k=3):
        if self.question_db:
            return self.question_db.similarity_search(query, k=k)
        return []

    def retrieve_from_questions(self, query, k=5, rerank_top_n=None):
        """
        从题库中检索相关信息
        
        Args:
            query (str): 查询文本
            k (int): 向量检索返回的文档数量
            rerank_top_n (int): 排序后返回的文档数量，默认为k
        """
        if self.question_db is None:
            return []
        
        try:
            # 第一阶段：向量检索
            if self.use_reranker and self.text_reranker.is_available():
                # 使用更大的k值进行初步检索
                initial_k = max(k * 3, 20)  # 扩大检索范围
                docs = self.question_db.similarity_search(query, k=initial_k)
                
                if docs:
                    # 第二阶段：文本排序
                    rerank_top_n = rerank_top_n or k
                    ranked_docs = self.text_reranker.rerank_langchain_docs(
                        query, docs, top_n=rerank_top_n
                    )
                    return [doc.page_content for doc in ranked_docs]
                else:
                    return []
            else:
                # 传统向量检索
                docs = self.question_db.similarity_search(query, k=k)
                return [doc.page_content for doc in docs]
                
        except Exception as e:
            print(f"题库检索错误: {e}")
            return []

    def retrieve_comprehensive(self, query, textbook_k=3, question_k=2, rerank_top_n=None):
        """
        综合检索：同时从教材和题库中检索信息
        
        Args:
            query (str): 查询文本
            textbook_k (int): 从教材检索的文档数量
            question_k (int): 从题库检索的文档数量
            rerank_top_n (int): 排序后返回的总文档数量
        
        Returns:
            List[str]: 检索到的文档内容列表
        """
        all_docs = []
        
        # 从教材检索
        textbook_docs = self.retrieve_from_textbooks(query, k=textbook_k)
        all_docs.extend(textbook_docs)
        
        # 从题库检索
        question_docs = self.retrieve_from_questions(query, k=question_k)
        all_docs.extend(question_docs)
        
        # 如果启用了排序器，对所有文档进行重新排序
        if self.use_reranker and self.text_reranker.is_available() and all_docs:
            try:
                total_docs = len(all_docs)
                rerank_top_n = rerank_top_n or min(total_docs, textbook_k + question_k)
                
                ranked_results = self.text_reranker.rerank_with_scores(
                    query, all_docs, top_n=rerank_top_n
                )
                
                return [doc for doc, score in ranked_results]
            except Exception as e:
                print(f"综合检索排序错误: {e}")
                return all_docs[:rerank_top_n] if rerank_top_n else all_docs
        
        return all_docs
    
    def get_retriever(self, db_name='textbooks', **kwargs):
        db = self.textbook_db if db_name == 'textbooks' else self.question_db
        if db:
            return db.as_retriever(**kwargs)
        return None
    
    async def adaptive_retrieve(self, query: str, user_feedback: dict = None):
        """
        自适应检索主接口
        
        Args:
            query (str): 查询文本
            user_feedback (dict): 用户反馈，用于策略调整
        
        Returns:
            检索结果，包含文档、策略信息和性能数据
        """
        if self.enable_adaptive and self.adaptive_strategy:
            try:
                return await self.adaptive_strategy.adaptive_retrieve(query, user_feedback)
            except Exception as e:
                print(f"自适应检索错误，降级到传统检索: {e}")
                # 降级到传统检索
                docs = self.retrieve_comprehensive(query)
                from .adaptive_retrieval_strategy import RetrievalResult, ComplexityAnalysis
                from .query_complexity_analyzer import QueryComplexity
                
                fallback_analysis = ComplexityAnalysis(
                    complexity=QueryComplexity.MODERATE,
                    score=0.5,
                    reasoning="自适应检索失败，使用传统检索",
                    features={},
                    recommended_strategy="standard_retrieval"
                )
                
                return RetrievalResult(
                    documents=docs,
                    strategy_used="fallback_traditional",
                    complexity_analysis=fallback_analysis,
                    retrieval_steps=[{"step": "traditional_fallback", "success": True}],
                    total_time=0.0,
                    confidence_score=0.6
                )
        else:
            # 传统检索模式
            docs = self.retrieve_comprehensive(query)
            from .adaptive_retrieval_strategy import RetrievalResult, ComplexityAnalysis
            from .query_complexity_analyzer import QueryComplexity
            
            traditional_analysis = ComplexityAnalysis(
                complexity=QueryComplexity.MODERATE,
                score=0.5,
                reasoning="使用传统检索模式",
                features={},
                recommended_strategy="traditional_retrieval"
            )
            
            return RetrievalResult(
                documents=docs,
                strategy_used="traditional_retrieval",
                complexity_analysis=traditional_analysis,
                retrieval_steps=[{"step": "traditional_retrieval", "success": True}],
                total_time=0.0,
                confidence_score=0.7
            )
    
    def analyze_query_complexity(self, query: str):
        """
        分析查询复杂度（同步接口）
        
        Args:
            query (str): 查询文本
        
        Returns:
            ComplexityAnalysis: 复杂度分析结果
        """
        if self.enable_adaptive and self.adaptive_strategy:
            return self.adaptive_strategy.complexity_analyzer.analyze_complexity(query)
        else:
            # 返回默认分析
            from .query_complexity_analyzer import ComplexityAnalysis, QueryComplexity
            return ComplexityAnalysis(
                complexity=QueryComplexity.MODERATE,
                score=0.5,
                reasoning="自适应功能未启用",
                features={},
                recommended_strategy="traditional_retrieval"
            )
    
    def get_adaptive_performance_report(self):
        """
        获取自适应检索性能报告
        
        Returns:
            Dict: 性能报告
        """
        if self.enable_adaptive and self.adaptive_strategy:
            return self.adaptive_strategy.get_performance_report()
        else:
            return {
                "message": "自适应检索功能未启用",
                "total_queries": 0,
                "strategy_distribution": {},
                "average_response_times": {},
                "success_rates": {}
            }
    
    def get_reranker_info(self):
        """
        获取排序器信息
        
        Returns:
            Dict: 排序器状态信息
        """
        if self.text_reranker:
            return {
                'enabled': self.use_reranker,
                'available': self.text_reranker.is_available(),
                'model_info': self.text_reranker.get_model_info()
            }
        else:
            return {
                'enabled': False,
                'available': False,
                'model_info': None
            }
    
    def get_adaptive_info(self):
        """
        获取自适应检索信息
        
        Returns:
            Dict: 自适应检索状态信息
        """
        return {
            'enabled': self.enable_adaptive,
            'available': self.adaptive_strategy is not None,
            'reranker_enabled': self.use_reranker,
            'supported_strategies': [
                'basic_vector_search',
                'standard_retrieval_with_rerank',
                'enhanced_retrieval_with_calculation',
                'multi_round_retrieval',
                'comprehensive_analysis_retrieval'
            ] if self.enable_adaptive else ['traditional_retrieval']
        }