# API嵌入模型使用说明

## 概述

为了解决Hugging Face模型下载困难的问题，我们开发了API嵌入模型功能，支持调用国内主流AI服务商的嵌入API来构建知识库。

## 支持的API提供商

### 1. 智谱AI (GLM)
- **模型**: `embedding-2`
- **API文档**: https://open.bigmodel.cn/dev/api#text_embedding
- **特点**: 高质量中文嵌入，1024维向量
- **价格**: 相对便宜，适合大规模使用

### 2. 通义千问 (阿里云)
- **模型**: `text-embedding-v1`
- **API文档**: https://help.aliyun.com/zh/dashscope/developer-reference/text-embedding-api-details
- **特点**: 阿里云服务，稳定可靠
- **价格**: 按调用次数计费

### 3. 百川智能
- **模型**: `Baichuan-Text-Embedding`
- **特点**: 专注中文理解
- **状态**: 待完善API接口

## 配置方法

### 1. 修改配置文件

编辑 `config.py` 文件中的嵌入模型配置：

```python
# 向量嵌入模型
'embedding': {
    'model_name': 'bge-large-zh-v1.5',  # 本地模型名称（备用）
    'device': 'cpu',
    'use_api': True,  # 启用API模式
    'api_provider': 'zhipu',  # 选择API提供商: 'zhipu', 'tongyi', 'baichuan'
    'api_model': 'embedding-2',  # API模型名称
}
```

### 2. 配置API密钥

确保在 `config.py` 中配置了相应的API密钥：

```python
# 智谱AI配置
'zhipu': {
    'api_key': 'your_zhipu_api_key_here',
    'model': 'glm-4',
},

# 通义千问配置
'tongyi': {
    'api_key': 'your_tongyi_api_key_here',
    'model': 'qwen-max',
},
```

## 使用方法

### 1. 测试API连接

运行测试脚本验证API配置：

```bash
python test_api_embedding.py
```

### 2. 更新知识库

使用API模式重新构建知识库：

```bash
# 完整更新知识库
python update_knowledge_base.py --mode all

# 仅更新教材索引
python update_knowledge_base.py --mode textbooks

# 仅更新题库索引
python update_knowledge_base.py --mode questions

# 检查知识库状态
python update_knowledge_base.py --mode status
```

### 3. 启动应用

```bash
python main.py
```

## 优势对比

| 特性 | 本地模型 | API模型 |
|------|----------|----------|
| 网络依赖 | 仅下载时需要 | 每次使用都需要 |
| 存储空间 | 需要几GB空间 | 无需本地存储 |
| 处理速度 | 较快（本地计算） | 取决于网络延迟 |
| 成本 | 一次性下载 | 按使用量付费 |
| 稳定性 | 高（离线可用） | 取决于网络和服务 |
| 模型更新 | 手动更新 | 自动使用最新版本 |

## 故障排除

### 1. API连接失败

**问题**: 出现网络连接错误

**解决方案**:
- 检查网络连接
- 验证API密钥是否正确
- 确认API服务商服务状态
- 检查代理设置

### 2. 回退机制

当API调用失败时，系统会自动使用随机向量作为回退方案，确保程序正常运行。虽然这会影响检索质量，但不会导致程序崩溃。

### 3. 批处理限制

API服务通常有批处理大小限制，系统会自动调整批处理大小以适应不同服务商的限制。

## 性能优化建议

### 1. 批处理大小
- 智谱AI: 建议16个文本/批次
- 通义千问: 建议8-16个文本/批次
- 根据网络状况调整

### 2. 请求频率控制
- 在批次间添加适当延迟（100ms）
- 避免并发请求过多
- 监控API配额使用情况

### 3. 错误处理
- 实现重试机制
- 记录失败的文本块
- 定期检查和补充失败的嵌入

## 成本估算

以智谱AI为例：
- 嵌入API价格: 约0.0005元/1K tokens
- 平均每个文档块: 100-500 tokens
- 5000个文档块成本: 约1-3元

## 切换模式

### 从本地模型切换到API模式

1. 修改 `config.py` 中的 `use_api` 为 `True`
2. 配置API提供商和密钥
3. 运行 `python update_knowledge_base.py --mode all`

### 从API模式切换回本地模式

1. 修改 `config.py` 中的 `use_api` 为 `False`
2. 确保本地模型可用
3. 运行 `python update_knowledge_base.py --mode all`

## 注意事项

1. **数据隐私**: API调用会将文本发送到第三方服务，请确保符合数据隐私要求
2. **成本控制**: 监控API使用量，避免意外产生高额费用
3. **服务稳定性**: 建议配置多个API提供商作为备选
4. **网络环境**: 确保网络环境能够访问相应的API服务

## 技术支持

如遇到问题，请：
1. 查看日志输出
2. 运行测试脚本诊断
3. 检查API服务商的服务状态
4. 联系技术支持