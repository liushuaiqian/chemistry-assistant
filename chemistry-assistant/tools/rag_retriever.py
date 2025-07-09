#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAG检索器
提供FAISS检索接口，用于检索教材和题库
"""

import os
import json
import numpy as np
from config import KNOWLEDGE_CONFIG
from models.embedding_model import EmbeddingModel

class RAGRetriever:
    """
    RAG检索器类
    负责从向量数据库中检索相关内容
    """
    
    def __init__(self):
        """
        初始化RAG检索器
        """
        self.embedding_model = EmbeddingModel()
        self.vector_store_path = KNOWLEDGE_CONFIG['vector_store_path']
        self.textbooks_path = KNOWLEDGE_CONFIG['textbooks_path']
        self.question_bank_path = KNOWLEDGE_CONFIG['question_bank_path']
        
        # 初始化FAISS索引
        self._init_faiss()
    
    def _init_faiss(self):
        """
        初始化FAISS索引
        如果索引不存在，则创建索引
        """
        try:
            import faiss
            
            # 检查向量存储目录是否存在
            if not os.path.exists(self.vector_store_path):
                os.makedirs(self.vector_store_path, exist_ok=True)
            
            # 教材索引路径
            textbook_index_path = os.path.join(self.vector_store_path, 'textbook_index.faiss')
            textbook_mapping_path = os.path.join(self.vector_store_path, 'textbook_mapping.json')
            
            # 题库索引路径
            question_index_path = os.path.join(self.vector_store_path, 'question_index.faiss')
            question_mapping_path = os.path.join(self.vector_store_path, 'question_mapping.json')
            
            # 加载或创建教材索引
            if os.path.exists(textbook_index_path) and os.path.exists(textbook_mapping_path):
                # 加载现有索引
                self.textbook_index = faiss.read_index(textbook_index_path)
                with open(textbook_mapping_path, 'r', encoding='utf-8') as f:
                    self.textbook_mapping = json.load(f)
                print(f"已加载教材索引，包含 {self.textbook_index.ntotal} 个向量")
            else:
                # 创建新索引
                print("教材索引不存在，需要先创建索引")
                self.textbook_index = None
                self.textbook_mapping = {}
            
            # 加载或创建题库索引
            if os.path.exists(question_index_path) and os.path.exists(question_mapping_path):
                # 加载现有索引
                self.question_index = faiss.read_index(question_index_path)
                with open(question_mapping_path, 'r', encoding='utf-8') as f:
                    self.question_mapping = json.load(f)
                print(f"已加载题库索引，包含 {self.question_index.ntotal} 个向量")
            else:
                # 创建新索引
                print("题库索引不存在，需要先创建索引")
                self.question_index = None
                self.question_mapping = {}
                
        except ImportError:
            print("未安装FAISS库，请先安装: pip install faiss-cpu 或 pip install faiss-gpu")
            self.textbook_index = None
            self.textbook_mapping = {}
            self.question_index = None
            self.question_mapping = {}
    
    def create_textbook_index(self):
        """
        创建教材索引
        读取教材文件并创建向量索引
        """
        try:
            import faiss
            
            # 检查教材目录是否存在
            if not os.path.exists(self.textbooks_path):
                print(f"教材目录不存在: {self.textbooks_path}")
                return
            
            # 读取教材文件
            textbook_chunks = []
            textbook_mapping = {}
            chunk_id = 0
            
            # 遍历教材目录中的所有文件
            for root, _, files in os.walk(self.textbooks_path):
                for file in files:
                    if file.endswith('.txt') or file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 将内容分块
                            chunks = self._split_text(content, chunk_size=500)
                            
                            # 添加到映射
                            for i, chunk in enumerate(chunks):
                                textbook_mapping[str(chunk_id)] = {
                                    'file': file,
                                    'path': file_path,
                                    'chunk_index': i,
                                    'title': file.replace('.txt', '').replace('.md', ''),
                                    'content': chunk
                                }
                                textbook_chunks.append(chunk)
                                chunk_id += 1
                        except Exception as e:
                            print(f"读取文件出错 {file_path}: {e}")
            
            if not textbook_chunks:
                print("未找到教材内容")
                return
            
            # 生成向量嵌入
            embeddings = []
            for chunk in textbook_chunks:
                embedding = self.embedding_model.get_embedding(chunk)
                embeddings.append(embedding)
            
            # 创建FAISS索引
            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings).astype('float32'))
            
            # 保存索引和映射
            faiss.write_index(index, os.path.join(self.vector_store_path, 'textbook_index.faiss'))
            with open(os.path.join(self.vector_store_path, 'textbook_mapping.json'), 'w', encoding='utf-8') as f:
                json.dump(textbook_mapping, f, ensure_ascii=False, indent=2)
            
            self.textbook_index = index
            self.textbook_mapping = textbook_mapping
            
            print(f"已创建教材索引，包含 {len(textbook_chunks)} 个文本块")
            
        except Exception as e:
            print(f"创建教材索引出错: {e}")
    
    def create_question_bank_index(self):
        """
        创建题库索引
        读取题库文件并创建向量索引
        """
        try:
            import faiss
            
            # 检查题库目录是否存在
            if not os.path.exists(self.question_bank_path):
                print(f"题库目录不存在: {self.question_bank_path}")
                return
            
            # 读取题库文件
            questions = []
            question_mapping = {}
            question_id = 0
            
            # 遍历题库目录中的所有文件
            for root, _, files in os.walk(self.question_bank_path):
                for file in files:
                    if file.endswith('.txt'):
                        # 处理文本格式题库
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 分割问题
                            question_blocks = content.split('\n\n')
                            for block in question_blocks:
                                if '答案' in block or '解析' in block:
                                    # 尝试分离问题和答案
                                    parts = block.split('答案:', 1) if '答案:' in block else block.split('答案：', 1)
                                    if len(parts) == 2:
                                        question_text = parts[0].strip()
                                        answer_text = parts[1].strip()
                                        
                                        question_mapping[str(question_id)] = {
                                            'file': file,
                                            'question': question_text,
                                            'answer': answer_text
                                        }
                                        questions.append(question_text)
                                        question_id += 1
                        except Exception as e:
                            print(f"读取文件出错 {file_path}: {e}")
                    
                    elif file.endswith('.jsonl') or file.endswith('.json'):
                        # 处理JSON格式题库
                        file_path = os.path.join(root, file)
                        try:
                            if file.endswith('.jsonl'):
                                # 逐行读取JSONL文件
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        try:
                                            item = json.loads(line)
                                            if 'question' in item:
                                                question_text = item['question']
                                                answer_text = item.get('answer', '')
                                                
                                                question_mapping[str(question_id)] = {
                                                    'file': file,
                                                    'question': question_text,
                                                    'answer': answer_text
                                                }
                                                questions.append(question_text)
                                                question_id += 1
                                        except json.JSONDecodeError:
                                            continue
                            else:
                                # 读取整个JSON文件
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    if isinstance(data, list):
                                        for item in data:
                                            if 'question' in item:
                                                question_text = item['question']
                                                answer_text = item.get('answer', '')
                                                
                                                question_mapping[str(question_id)] = {
                                                    'file': file,
                                                    'question': question_text,
                                                    'answer': answer_text
                                                }
                                                questions.append(question_text)
                                                question_id += 1
                        except Exception as e:
                            print(f"读取文件出错 {file_path}: {e}")
            
            if not questions:
                print("未找到题库内容")
                return
            
            # 生成向量嵌入
            embeddings = []
            for question in questions:
                embedding = self.embedding_model.get_embedding(question)
                embeddings.append(embedding)
            
            # 创建FAISS索引
            dimension = len(embeddings[0])
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings).astype('float32'))
            
            # 保存索引和映射
            faiss.write_index(index, os.path.join(self.vector_store_path, 'question_index.faiss'))
            with open(os.path.join(self.vector_store_path, 'question_mapping.json'), 'w', encoding='utf-8') as f:
                json.dump(question_mapping, f, ensure_ascii=False, indent=2)
            
            self.question_index = index
            self.question_mapping = question_mapping
            
            print(f"已创建题库索引，包含 {len(questions)} 个问题")
            
        except Exception as e:
            print(f"创建题库索引出错: {e}")
    
    def search_textbooks(self, query, top_k=3):
        """
        搜索教材内容
        
        Args:
            query (str): 查询文本
            top_k (int): 返回的结果数量
            
        Returns:
            list: 检索结果列表
        """
        if self.textbook_index is None:
            return [{"title": "索引未初始化", "content": "请先创建教材索引", "score": 0.0}]
        
        try:
            # 获取查询的向量表示
            query_vector = self.embedding_model.get_embedding(query)
            
            # 执行搜索
            distances, indices = self.textbook_index.search(
                np.array([query_vector]).astype('float32'), top_k
            )
            
            # 整理结果
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:  # -1表示无效结果
                    item = self.textbook_mapping.get(str(idx), {})
                    results.append({
                        "title": item.get("title", "未知标题"),
                        "content": item.get("content", "未知内容"),
                        "file": item.get("file", "未知文件"),
                        "score": 1.0 - float(distances[0][i])  # 转换距离为相似度分数
                    })
            
            return results
            
        except Exception as e:
            print(f"搜索教材出错: {e}")
            return [{"title": "搜索出错", "content": str(e), "score": 0.0}]
    
    def search_question_bank(self, query, top_k=3):
        """
        搜索题库内容
        
        Args:
            query (str): 查询文本
            top_k (int): 返回的结果数量
            
        Returns:
            list: 检索结果列表
        """
        if self.question_index is None:
            return [{"question": "索引未初始化", "answer": "请先创建题库索引", "score": 0.0}]
        
        try:
            # 获取查询的向量表示
            query_vector = self.embedding_model.get_embedding(query)
            
            # 执行搜索
            distances, indices = self.question_index.search(
                np.array([query_vector]).astype('float32'), top_k
            )
            
            # 整理结果
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:  # -1表示无效结果
                    item = self.question_mapping.get(str(idx), {})
                    results.append({
                        "question": item.get("question", "未知问题"),
                        "answer": item.get("answer", "未知答案"),
                        "file": item.get("file", "未知文件"),
                        "score": 1.0 - float(distances[0][i])  # 转换距离为相似度分数
                    })
            
            return results
            
        except Exception as e:
            print(f"搜索题库出错: {e}")
            return [{"question": "搜索出错", "answer": str(e), "score": 0.0}]
    
    def _split_text(self, text, chunk_size=500, overlap=50):
        """
        将文本分割成固定大小的块
        
        Args:
            text (str): 要分割的文本
            chunk_size (int): 每个块的大小（字符数）
            overlap (int): 相邻块之间的重叠字符数
            
        Returns:
            list: 文本块列表
        """
        if not text:
            return []
        
        # 按段落分割
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果段落加上当前块超过了块大小，保存当前块并开始新块
            if len(current_chunk) + len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果段落本身就超过块大小，直接分割
                if len(paragraph) > chunk_size:
                    # 分割长段落
                    for i in range(0, len(paragraph), chunk_size - overlap):
                        chunks.append(paragraph[i:i + chunk_size])
                    # 更新当前块为最后一个块的重叠部分
                    current_chunk = paragraph[-(min(overlap, len(paragraph))):]
                else:
                    # 开始新块，包含上一个块的结尾（重叠）
                    if chunks and overlap > 0:
                        current_chunk = chunks[-1][-overlap:] + "\n" + paragraph
                    else:
                        current_chunk = paragraph
            else:
                # 添加段落到当前块
                if current_chunk:
                    current_chunk += "\n"
                current_chunk += paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks