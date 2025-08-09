# Web UI 格式化器使用指南

## 概述

`web_ui_formatter.py` 是专门为Web界面（如Gradio）设计的统一输出格式化工具。它整合了输出清理、Markdown格式化、LaTeX渲染、化学公式标准化等功能，为Web UI提供一致且美观的输出格式。

## 主要功能

### 1. 统一的输出格式化
- 自动解析JSON字符串、Python字面量和普通字符串
- 智能提取核心答案内容
- 格式化结构化数据（字典、列表等）
- 应用化学和数学公式标准化

### 2. 专门的化学格式化
- 化学公式下标转换（H2O → H₂O）
- 化学反应箭头标准化（-> → →）
- 常见化学物质公式规范化
- LaTeX化学公式清理

### 3. 数学公式处理
- LaTeX公式格式修复
- 数学符号标准化
- 公式标记完整性检查

### 4. 错误和状态消息格式化
- 统一的错误消息格式
- 美观的状态信息显示
- 上下文相关的提示信息

## 使用方法

### 基本导入

```python
from utils.web_ui_formatter import (
    clean_and_format_output,
    format_comparison_output,
    format_chain_result,
    format_error_message,
    format_status_message
)
```

### 主要函数

#### 1. `clean_and_format_output(raw_output, title=None)`

主要的格式化函数，适用于大多数输出场景。

```python
# 处理字典输出
raw_output = {
    "answer": "水的分子式是H2O",
    "confidence": 0.95
}
formatted = clean_and_format_output(raw_output)

# 处理JSON字符串
json_string = '{"answer": "2H2 + O2 → 2H2O"}'
formatted = clean_and_format_output(json_string)

# 添加标题
formatted = clean_and_format_output(raw_output, title="化学分析结果")
```

#### 2. `format_comparison_output(comparison_data)`

专门用于格式化模型对比结果。

```python
comparison = {
    "model_a": "模型A的回答",
    "model_b": "模型B的回答",
    "similarity": 0.85
}
formatted = format_comparison_output(comparison)
```

#### 3. `format_chain_result(chain_data)`

专门用于格式化链式处理结果（如LangChain输出）。

```python
chain_result = {
    "reasoning_content": "推理过程...",
    "final_answer": "最终答案"
}
formatted = format_chain_result(chain_result)
```

#### 4. `format_error_message(error, context="")`

格式化错误消息，提供统一的错误显示格式。

```python
try:
    # 一些可能出错的操作
    pass
except Exception as e:
    error_msg = format_error_message(e, "化学方程式处理")
    return error_msg
```

#### 5. `format_status_message(status, details="")`

格式化状态消息，用于显示处理状态和进度信息。

```python
status_msg = format_status_message(
    "处理完成",
    "已成功处理3个模型的输出"
)
```

## 在Gradio中的使用

### 替换原有的格式化函数

**之前的做法：**
```python
# 在app_gradio.py中定义复杂的格式化逻辑
def clean_and_format_output(raw_output):
    # 大量的格式化代码...
    pass
```

**现在的做法：**
```python
# 直接导入使用
from utils.web_ui_formatter import clean_and_format_output, format_comparison_output

# 在处理函数中使用
def process_question(question, image=None):
    # ... 处理逻辑 ...
    
    # 格式化不同类型的输出
    cleaned_answer = clean_and_format_output(answer)
    cleaned_comparison = format_comparison_output(comparison)
    cleaned_chain_result = format_chain_result(chain_result)
    
    return cleaned_answer, cleaned_comparison, cleaned_chain_result
```

### 错误处理

```python
def submit_question(question, image=None):
    try:
        # 处理逻辑
        result = process_question(question, image)
        return clean_and_format_output(result)
    except Exception as e:
        # 使用统一的错误格式化
        return format_error_message(e, "问题处理")
```

## 格式化效果示例

### 化学公式标准化

**输入：**
```
反应方程式：2H2 + O2 -> 2H2O
化合物：Fe2O3, CaCO3, H2SO4
```

**输出：**
```
反应方程式：2H₂ + O₂ → 2H₂O
化合物：Fe₂O₃, CaCO₃, H₂SO₄
```

### JSON数据格式化

**输入：**
```python
{"answer": "化学反应分析", "confidence": 0.95}
```

**输出：**
```markdown
```json
{
  "answer": "化学反应分析",
  "confidence": 0.95
}
```
```

### 错误消息格式化

**输出：**
```markdown
❌ **处理出错**

**错误上下文**: 化学方程式处理

**错误信息**: 输入格式不正确

请检查输入内容或联系技术支持。
```

## 扩展和自定义

### 添加新的化学公式

在 `apply_chemistry_formatting` 方法中添加新的替换规则：

```python
chemistry_replacements = {
    r'\bYourFormula\b': 'Your₂Formula₃',
    # 添加更多规则...
}
```

### 添加新的数学符号

在 `apply_latex_formatting` 方法中添加新的符号：

```python
math_replacements = {
    r'\\yourSymbol': 'YourSymbol',
    # 添加更多符号...
}
```

## 性能考虑

- 格式化器使用缓存的全局实例，避免重复初始化
- 正则表达式经过优化，减少不必要的匹配
- 错误处理机制确保即使格式化失败也能返回可用的输出

## 维护建议

1. **集中管理**：所有Web UI相关的格式化逻辑都在这个模块中，便于维护和更新
2. **测试覆盖**：使用 `test_web_ui_formatter.py` 进行功能测试
3. **日志记录**：格式化过程中的错误会被记录到日志中，便于调试
4. **向后兼容**：新版本保持与现有接口的兼容性

## 故障排除

### 常见问题

1. **化学公式显示不正确**
   - 检查输入格式是否符合预期
   - 确认正则表达式规则是否正确

2. **LaTeX公式渲染问题**
   - 确保Gradio界面已正确配置MathJax
   - 检查公式标记是否完整

3. **编码问题**
   - 格式化器会自动处理UTF-8编码问题
   - 如果仍有问题，检查输入数据的编码

### 调试方法

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
from utils.web_ui_formatter import web_ui_formatter
result = web_ui_formatter.clean_and_format_for_web(your_data)
```

## 总结

`web_ui_formatter.py` 提供了一个统一、强大且易于使用的Web UI格式化解决方案。通过使用这个模块，你可以：

- 确保所有Web UI输出的一致性
- 简化格式化逻辑的维护
- 提供更好的用户体验
- 轻松扩展新的格式化功能

建议在所有需要格式化输出的Web UI组件中使用这个模块，以保持代码的整洁和功能的一致性。