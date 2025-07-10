# LangChain 集成指南

## 概述

本项目已成功集成 LangChain 框架，提供了更强大、更灵活的大语言模型调用和管理能力。

## 🚀 新功能特性

### 1. 统一的 LLM 管理器
- **文件**: `core/llm_manager.py`
- **功能**: 统一管理多种大语言模型（OpenAI、通义千问、智谱AI、DeepSeek）
- **优势**: 简化 API 调用、统一错误处理、自动重试机制

### 2. 化学分析链
- **文件**: `core/chemistry_chain.py`
- **功能**: 实现化学问题的链式分析工作流
- **步骤**: 问题分类 → 多角度分析 → 解答生成
- **优势**: 更结构化的问题处理流程

### 3. 增强的控制器
- **文件**: `core/controller.py`
- **新方法**: 
  - `process_with_chain()`: 链式处理
  - `get_available_models()`: 获取模型信息
  - `call_specific_model()`: 调用指定模型

### 4. 改进的用户界面
- **文件**: `ui/app_gradio.py`
- **新增**: LangChain 链式处理选项
- **功能**: 动态模型选择、链式分析结果展示

## 📦 依赖安装

### 新增依赖
```bash
pip install langchain>=0.1.0
pip install langchain-openai>=0.0.5
pip install langchain-community>=0.0.20
pip install langchain-core>=0.1.23
pip install dashscope>=1.14.0
```

### 完整安装
```bash
pip install -r requirements.txt
```

## ⚙️ 配置说明

### API 密钥配置
确保在 `config.py` 中正确配置以下 API 密钥：

```python
# OpenAI API
OPENAI_API_KEY = "your_openai_api_key"
OPENAI_BASE_URL = "https://api.openai.com/v1"

# 通义千问 API
TONGYI_API_KEY = "your_tongyi_api_key"

# 智谱AI API
ZHIPU_API_KEY = "your_zhipu_api_key"

# DeepSeek API
DEEPSEEK_API_KEY = "your_deepseek_api_key"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

## 🎯 使用方法

### 1. 基本使用

#### 启动 Web 界面
```bash
python ui/app_gradio.py
```

#### 运行演示脚本
```bash
python demo_langchain.py
```

### 2. 编程接口使用

#### LLM 管理器
```python
from core.llm_manager import LLMManager

# 初始化管理器
llm_manager = LLMManager()

# 获取可用模型
models = llm_manager.get_available_models()
print(f"可用模型: {models}")

# 调用化学专家
response = llm_manager.call_chemistry_expert(
    model_name="gpt-3.5-turbo",
    question="什么是化学平衡？"
)
print(response)

# 融合多个模型的答案
answers = {
    "model1": "答案1",
    "model2": "答案2"
}
fused, comparison = llm_manager.fuse_answers("问题", answers)
```

#### 化学分析链
```python
from core.chemistry_chain import ChemistryAnalysisChain

# 初始化分析链
chain = ChemistryAnalysisChain()

# 获取链信息
info = chain.get_chain_info()
print(f"链信息: {info}")

# 链式处理问题
result = chain.process_question_chain("计算pH值的问题")
print(f"分类: {result['classification']}")
print(f"分析: {result['analysis']}")
print(f"解答: {result['solution']}")
```

#### 控制器集成
```python
from core.controller import Controller

# 初始化控制器
controller = Controller()

# 获取系统信息
models_info = controller.get_available_models()
print(f"系统模型: {models_info}")

# 链式处理
response, comparison, chain_result = controller.process_with_chain(
    question="化学问题",
    use_chain=True
)

# 调用指定模型
response = controller.call_specific_model(
    model_name="gpt-3.5-turbo",
    question="化学问题"
)
```

## 🔧 高级配置

### 自定义模型配置
在 `core/llm_manager.py` 中可以调整模型参数：

```python
# 模型参数配置
MODEL_CONFIGS = {
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.9
}
```

### 链式处理自定义
在 `core/chemistry_chain.py` 中可以修改处理步骤：

```python
# 自定义处理步骤
CHAIN_STEPS = [
    "问题分类",
    "知识检索", 
    "多角度分析",
    "解答生成",
    "结果验证"
]
```

## 🐛 故障排除

### 常见问题

1. **模型调用失败**
   - 检查 API 密钥是否正确
   - 确认网络连接正常
   - 查看错误日志

2. **依赖安装问题**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. **链式处理错误**
   - 确保至少有一个可用的模型
   - 检查问题格式是否正确
   - 查看详细错误信息

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 性能优化

### 1. 模型选择策略
- 简单问题：使用轻量级模型
- 复杂问题：使用高性能模型
- 对比分析：使用多模型融合

### 2. 缓存机制
- LangChain 自带缓存功能
- 减少重复 API 调用
- 提高响应速度

### 3. 并发处理
- 支持异步模型调用
- 并行处理多个请求
- 优化资源利用

## 🔄 迁移说明

### 从旧版本迁移
1. **保持兼容性**: 旧的 API 调用方式仍然可用
2. **渐进式升级**: 可以逐步迁移到新的 LangChain 接口
3. **回退机制**: 新功能失败时自动回退到旧实现

### 迁移步骤
1. 安装新依赖
2. 更新配置文件
3. 测试新功能
4. 逐步迁移代码

## 📈 未来规划

### 短期目标
- [ ] 添加更多模型支持
- [ ] 优化链式处理性能
- [ ] 增强错误处理机制

### 长期目标
- [ ] 实现自定义链构建
- [ ] 添加模型微调支持
- [ ] 集成向量数据库

## 🤝 贡献指南

欢迎贡献代码和建议！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📞 支持

如有问题或建议，请：
- 查看本指南
- 运行演示脚本
- 检查日志输出
- 提交 Issue

---

**注意**: 本集成保持了与原有功能的完全兼容性，您可以安全地使用新功能而不影响现有工作流程。