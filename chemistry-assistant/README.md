# Chemistry Assistant (化学助手)

一个基于人工智能的化学学习和问答助手，支持化学知识查询、化学计算、教材内容检索和题库练习。

## 功能特点

- **多模态问答**：支持图像和文字输入，采用多模型协同推理生成权威答案
  - 图像理解：通义视觉模型识别化学题目图片
  - 并行推理：通义千问3和DeepSeek-R1同时生成答案
  - 智能融合：GLM-4-Plus对多个答案进行比较分析与融合
- **智能问答**：回答化学相关问题，提供详细解释和步骤
- **化学计算**：支持摩尔质量计算、化学方程式平衡等功能
- **知识检索**：从内置教材和题库中检索相关内容
- **多模型支持**：支持本地模型和多种外部API（OpenAI、智谱、Claude等）
- **用户友好界面**：提供命令行和Web界面两种交互方式

## 系统架构

```
chemistry-assistant/
├── main.py                 # 主入口文件
├── config.py               # 配置文件
├── core/                   # 核心模块
│   ├── controller.py       # 控制器
│   ├── agent_manager.py    # Agent管理器
│   ├── task_router.py      # 任务路由器
│   └── multimodal_processor.py # 多模态处理器
├── agents/                 # 智能体模块
│   ├── local_model_agent.py # 本地模型Agent
│   ├── external_agent.py   # 外部API Agent
│   ├── retriever_agent.py  # 检索Agent
│   └── tools_agent.py      # 工具Agent
├── tools/                  # 工具模块
│   ├── chemistry_solver.py # 化学计算工具
│   ├── rag_retriever.py    # RAG检索工具
│   └── knowledge_api.py    # 知识API工具
├── models/                 # 模型模块
│   ├── local_chat_model.py # 本地聊天模型
│   └── embedding_model.py  # 嵌入模型
├── data/                   # 数据目录
│   ├── textbooks/          # 教材数据
│   ├── question_bank/      # 题库数据
│   └── vector_store/       # 向量存储
├── ui/                     # 用户界面
│   └── app.py              # Web应用
└── utils/                  # 工具包
    ├── logger.py           # 日志工具
    ├── helpers.py          # 辅助函数
    ├── data_processor.py   # 数据处理
    └── conversation.py     # 对话管理
```

### 多模态处理流程

1. **输入判断**：自动识别输入类型（图像/文字）
2. **图像理解**：通义视觉模型提取题干内容
3. **并行推理**：通义千问3和DeepSeek-R1同时生成答案
4. **智能融合**：GLM-4-Plus比较分析并生成最终答案

## 安装指南

### 环境要求

- Python 3.8+
- CUDA支持（可选，用于GPU加速）

### 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/yourusername/chemistry-assistant.git
cd chemistry-assistant
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置

编辑`config.py`文件，设置模型路径、API密钥等配置项。

## 使用方法

### Web界面模式

```bash
python main.py --mode web
```

然后在浏览器中访问 http://localhost:8501

#### 多模态问答功能
- 选择"多模态问答"功能
- 可以选择"文字输入"或"图像上传"模式
- 图像上传支持PNG、JPG、JPEG格式
- 系统会自动识别图像中的化学题目并生成权威答案

### 命令行模式

```bash
python main.py --mode cli
```

#### CLI多模态功能
- 输入`multimodal`切换到多模态模式
- 可以输入文字问题或图片文件路径
- 输入`normal`切换回普通模式

## 数据准备

### 教材数据

将化学教材文本文件放入`data/textbooks/`目录。

### 题库数据

将化学题库JSON文件放入`data/question_bank/`目录。

### 向量存储初始化

```bash
python main.py --init-vector-store
```

## 开发指南

### 添加新功能

1. 在相应模块中实现功能
2. 在`config.py`中添加相关配置
3. 在`main.py`或`ui/app.py`中添加接口

### 添加新模型

1. 在`models/`目录下创建新的模型类
2. 在`config.py`中添加模型配置
3. 在`agents/`中实现相应的Agent

## 许可证

[MIT License](LICENSE)

## 贡献指南

欢迎提交Issue和Pull Request！

## 联系方式

- 邮箱：your.email@example.com
- GitHub：[yourusername](https://github.com/yourusername)