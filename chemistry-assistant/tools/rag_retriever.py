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

class RAGRetriever:
    """
    基于LangChain的RAG检索器
    """

    def __init__(self, force_recreate=False):
        self.embedding_model = EmbeddingModel()
        self.vector_store_path = KNOWLEDGE_CONFIG['vector_store_path']
        if not os.path.exists(self.vector_store_path):
            os.makedirs(self.vector_store_path)
        self.textbooks_path = KNOWLEDGE_CONFIG['textbooks_path']
        self.question_bank_path = KNOWLEDGE_CONFIG['question_bank_path']
        self.force_recreate = force_recreate

        self.textbook_db = self._load_vector_store('textbooks')
        self.question_db = self._load_vector_store('questions')

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

    def search_question_bank(self, query, k=3):
        if self.question_db:
            return self.question_db.similarity_search(query, k=k)
        return []

    def get_retriever(self, db_name='textbooks', **kwargs):
        db = self.textbook_db if db_name == 'textbooks' else self.question_db
        if db:
            return db.as_retriever(**kwargs)
        return None