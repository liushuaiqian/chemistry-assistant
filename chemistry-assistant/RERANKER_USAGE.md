# 文本排序器使用指南

## 概述

本项目已成功集成了基于 DashScope `gte-rerank-v2` 模型的文本排序器，实现了**双阶段检索**功能：

1. **第一阶段**：向量检索 - 快速从大量文档中筛选出候选文档
2. **第二阶段**：文本排序 - 使用专业排序模型对候选文档进行精确排序

这种架构显著提升了检索的准确性和相关性。

## 功能特性

### 🚀 核心优势

- **提高检索精度**：通过专业排序模型提升文档相关性排序
- **保持检索效率**：向量检索快速筛选，排序模型精确排序
- **无缝集成**：与现有RAG系统完美融合
- **智能降级**：排序器不可用时自动降级为传统向量检索

### 📋 支持的功能

- 教材知识检索排序
- 题库问题检索排序
- 综合检索排序（同时检索教材和题库）
- LangChain文档对象排序
- 自定义文档列表排序

## 配置要求

### API密钥配置

在 `config.py` 文件中配置通义API密钥：

```python
MODEL_CONFIG = {
    'tongyi': {
        'api_key': 'your-dashscope-api-key',
        # 其他配置...
    }
}
```

### 依赖安装

确保已安装 `dashscope` 库：

```bash
pip install dashscope>=1.14.0
```

## 使用方法

### 1. 启动时启用双阶段检索

#### 命令行启动

```bash
# 启用双阶段检索（默认）
python main.py --mode web

# 禁用双阶段检索，使用传统模式
python main.py --mode web --disable-reranker
```

#### 编程接口

```python
from core.controller import Controller
from core.chemistry_chain import ChemistryAnalysisChain
from tools.rag_retriever import RAGRetriever

# 启用双阶段检索
controller = Controller(use_reranker=True)
chain = ChemistryAnalysisChain(use_reranker=True)
retriever = RAGRetriever(use_reranker=True)

# 禁用双阶段检索
controller = Controller(use_reranker=False)
chain = ChemistryAnalysisChain(use_reranker=False)
retriever = RAGRetriever(use_reranker=False)
```

### 2. 直接使用文本排序器

```python
from tools.text_reranker import TextReranker

# 初始化排序器
reranker = TextReranker()

# 检查可用性
if reranker.is_available():
    # 对文档进行排序
    query = "什么是化学键"
    documents = [
        "化学键是原子间相互结合的作用力",
        "量子力学是研究微观粒子运动规律的物理学分支",
        "共价键是原子间通过共享电子对形成的化学键"
    ]
    
    # 获取排序结果和分数
    ranked_docs = reranker.rerank_with_scores(query, documents, top_n=3)
    
    for doc, score in ranked_docs:
        print(f"分数: {score:.4f}, 文档: {doc}")
else:
    print("排序器不可用，请检查API密钥配置")
```

### 3. 使用RAG检索器的双阶段检索

```python
from tools.rag_retriever import RAGRetriever

# 初始化支持双阶段检索的RAG检索器
retriever = RAGRetriever(use_reranker=True)

# 综合检索（推荐）
query = "化学键的类型有哪些"
results = retriever.retrieve_comprehensive(
    query=query,
    textbook_k=3,      # 从教材检索3个文档
    question_k=2,      # 从题库检索2个文档
    rerank_top_n=4     # 排序后返回前4个
)

# 单独从教材检索
textbook_results = retriever.retrieve_from_textbooks(
    query=query,
    k=5,               # 向量检索返回5个候选
    rerank_top_n=3     # 排序后返回前3个
)

# 单独从题库检索
question_results = retriever.retrieve_from_questions(
    query=query,
    k=5,
    rerank_top_n=3
)

# 获取排序器状态信息
reranker_info = retriever.get_reranker_info()
print(f"排序器状态: {reranker_info}")
```

### 4. 在化学分析链中使用

```python
from core.chemistry_chain import ChemistryAnalysisChain

# 初始化支持双阶段检索的化学分析链
chain = ChemistryAnalysisChain(use_reranker=True)

# 处理问题（自动使用双阶段检索）
result = chain.process_simple("请解释离子键的形成机理")
print(result)

# 并行模型处理（每个模型都会使用双阶段检索）
parallel_result = chain._parallel_model_call("什么是共价键")
for model_name, model_result in parallel_result.items():
    if model_result['success']:
        print(f"模型 {model_name}:")
        print(f"  RAG使用: {model_result.get('rag_used', False)}")
        print(f"  检索文档数: {model_result.get('rag_docs_count', 0)}")
        print(f"  答案: {model_result['answer'][:100]}...")
```

## 性能优化

### 检索参数调优

```python
# 针对不同场景的参数建议

# 快速检索（适合实时对话）
results = retriever.retrieve_comprehensive(
    query=query,
    textbook_k=2,
    question_k=1,
    rerank_top_n=3
)

# 精确检索（适合深度分析）
results = retriever.retrieve_comprehensive(
    query=query,
    textbook_k=5,
    question_k=3,
    rerank_top_n=6
)

# 平衡模式（推荐）
results = retriever.retrieve_comprehensive(
    query=query,
    textbook_k=3,
    question_k=2,
    rerank_top_n=4
)
```

### 成本控制

- 排序器调用会产生API费用，建议合理设置 `rerank_top_n` 参数
- 对于简单查询，可以禁用排序器以节省成本
- 系统会自动缓存排序结果（如果配置了缓存）

## 测试和验证

### 运行测试脚本

```bash
# 运行完整的功能测试
python test_reranker.py
```

测试脚本会验证：
- 文本排序器基本功能
- RAG检索器双阶段检索
- 化学分析链集成
- 控制器集成

### 手动测试

```python
# 测试排序器可用性
from tools.text_reranker import TextReranker
reranker = TextReranker()
print(f"排序器可用: {reranker.is_available()}")
print(f"模型信息: {reranker.get_model_info()}")

# 测试检索效果对比
from tools.rag_retriever import RAGRetriever

# 传统检索
traditional_retriever = RAGRetriever(use_reranker=False)
traditional_results = traditional_retriever.retrieve_from_textbooks("化学键", k=3)

# 双阶段检索
advanced_retriever = RAGRetriever(use_reranker=True)
advanced_results = advanced_retriever.retrieve_from_textbooks("化学键", k=3)

print("传统检索结果:")
for i, doc in enumerate(traditional_results, 1):
    print(f"{i}. {doc[:100]}...")

print("\n双阶段检索结果:")
for i, doc in enumerate(advanced_results, 1):
    print(f"{i}. {doc[:100]}...")
```

## 故障排除

### 常见问题

1. **排序器不可用**
   - 检查通义API密钥是否正确配置
   - 确认网络连接正常
   - 验证API密钥是否有足够的配额

2. **检索结果不理想**
   - 调整 `textbook_k` 和 `question_k` 参数
   - 增加 `rerank_top_n` 值
   - 检查知识库内容是否充足

3. **性能问题**
   - 减少初始检索的文档数量
   - 降低 `rerank_top_n` 值
   - 考虑使用缓存机制

### 日志调试

系统会输出详细的日志信息，包括：
- 排序器初始化状态
- 检索过程的详细信息
- 排序结果统计
- 错误和警告信息

查看日志以诊断问题：

```python
import logging
logging.basicConfig(level=logging.INFO)

# 运行你的代码，观察日志输出
```

## 最佳实践

1. **合理配置参数**：根据应用场景调整检索和排序参数
2. **监控API使用**：定期检查API调用量和费用
3. **性能测试**：在生产环境前进行充分的性能测试
4. **降级策略**：确保排序器不可用时系统仍能正常工作
5. **定期更新**：关注模型更新和API变化

## 技术架构

```
用户查询
    ↓
向量检索 (FAISS)
    ↓
候选文档 (k*3)
    ↓
gte-rerank-v2 排序
    ↓
精确排序结果 (top_n)
    ↓
LLM 生成答案
```

这种双阶段架构在保持检索效率的同时，显著提升了结果的准确性和相关性。