#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM管理器
基于LangChain框架统一管理各种大语言模型的调用
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi
from langchain_core.language_models.chat_models import BaseChatModel
from config import MODEL_CONFIG
from utils.output_cleaner import clean_output, clean_model_output

class LLMManager:
    """
    LLM管理器类
    统一管理和调用各种大语言模型
    """
    
    def __init__(self):
        """
        初始化LLM管理器
        """
        self.logger = logging.getLogger(__name__)
        self.models: Dict[str, BaseChatModel] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """
        初始化所有可用的模型
        """
        try:
            # 初始化OpenAI模型
            if 'openai' in MODEL_CONFIG and MODEL_CONFIG['openai'].get('api_key'):
                self.models['openai'] = ChatOpenAI(
                    api_key=MODEL_CONFIG['openai']['api_key'],
                    model=MODEL_CONFIG['openai'].get('model', 'gpt-3.5-turbo'),
                    temperature=0.7,
                    max_tokens=2000
                )
                self.logger.info("OpenAI模型初始化成功")
            
            # 初始化通义千问模型
            if 'tongyi' in MODEL_CONFIG and MODEL_CONFIG['tongyi'].get('api_key'):
                self.models['tongyi'] = ChatTongyi(
                    dashscope_api_key=MODEL_CONFIG['tongyi']['api_key'],
                    model=MODEL_CONFIG['tongyi'].get('model', 'qwen-turbo'),
                    temperature=0.7,
                    max_tokens=2000
                )
                self.logger.info("通义千问模型初始化成功")
            
            # 初始化智谱AI模型（通过OpenAI兼容接口）
            if 'zhipu' in MODEL_CONFIG and MODEL_CONFIG['zhipu'].get('api_key'):
                self.models['zhipu'] = ChatOpenAI(
                    api_key=MODEL_CONFIG['zhipu']['api_key'],
                    base_url=MODEL_CONFIG['zhipu'].get('api_base', 'https://open.bigmodel.cn/api/paas/v4/'),
                    model=MODEL_CONFIG['zhipu'].get('model', 'glm-4'),
                    temperature=0.3,
                    max_tokens=2000
                )
                self.logger.info("智谱AI模型初始化成功")
            
            # 初始化DeepSeek模型（通过通义接口）
            if 'deepseek' in MODEL_CONFIG and MODEL_CONFIG['deepseek'].get('api_key'):
                self.models['deepseek'] = ChatTongyi(
                    dashscope_api_key=MODEL_CONFIG['deepseek']['api_key'],
                    model=MODEL_CONFIG['deepseek'].get('model', 'deepseek-v2'),
                    temperature=0.7,
                    max_tokens=2000
                )
                self.logger.info("DeepSeek模型初始化成功")
                
        except Exception as e:
            self.logger.error(f"模型初始化失败: {str(e)}")
    
    def is_model_available(self, model_name: str) -> bool:
        """
        检查指定模型是否可用
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 模型是否可用
        """
        return model_name in self.models
    
    def get_available_models(self) -> List[str]:
        """
        获取所有可用模型的列表
        
        Returns:
            List[str]: 可用模型名称列表
        """
        return list(self.models.keys())
    
    def call_model(self, model_name: str, messages: List[BaseMessage], **kwargs) -> str:
        """
        调用指定的模型
        
        Args:
            model_name: 模型名称
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            str: 模型响应
        """
        self.logger.info(f"[LLM管理器] 开始调用模型: {model_name}")
        self.logger.info(f"[LLM管理器] 消息数量: {len(messages)}")
        
        if model_name not in self.models:
            error_msg = f"模型 {model_name} 未初始化或不可用"
            self.logger.error(f"[LLM管理器] {error_msg}")
            self.logger.error(f"[LLM管理器] 可用模型: {list(self.models.keys())}")
            return f"错误: 模型 {model_name} 不可用"
        
        try:
            model = self.models[model_name]
            self.logger.info(f"[LLM管理器] 模型对象类型: {type(model)}")
            
            self.logger.info(f"[LLM管理器] 开始调用模型API...")
            response = model.invoke(messages, **kwargs)
            self.logger.info(f"[LLM管理器] 模型API调用成功")
            self.logger.info(f"[LLM管理器] 响应类型: {type(response)}")
            
            # 处理响应内容 - 只处理真正的编码问题，不破坏原始内容结构
            content = response.content
            self.logger.info(f"[LLM管理器] 响应内容长度: {len(content)}")
            
            # 基础编码处理
            if isinstance(content, bytes):
                # 如果是字节类型，尝试解码为UTF-8
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    # 如果UTF-8解码失败，尝试其他编码
                    try:
                        content = content.decode('gbk')
                    except UnicodeDecodeError:
                        content = content.decode('utf-8', errors='ignore')
            elif not isinstance(content, str):
                content = str(content)
            
            # 只移除真正的控制字符，保留正常的换行和制表符
            import re
            content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
            
            # 确保UTF-8编码正确
            try:
                content = content.encode('utf-8').decode('utf-8')
            except UnicodeError:
                # 如果编码有问题，只清理无法编码的字符
                content = ''.join(char for char in content if ord(char) < 65536)
            
            self.logger.info(f"[LLM管理器] 内容清理完成，最终长度: {len(content)}")
            return content
            
        except Exception as e:
            self.logger.error(f"[LLM管理器] 调用模型 {model_name} 失败: {str(e)}")
            import traceback
            self.logger.error(f"[LLM管理器] 异常堆栈: {traceback.format_exc()}")
            return f"模型调用失败: {str(e)}"
    
    def call_chemistry_expert(self, model_name: str, question: str, context: str = "") -> str:
        """
        以化学专家身份调用模型
        
        Args:
            model_name: 模型名称
            question: 化学问题
            context: 上下文信息
            
        Returns:
            str: 专家回答
        """
        system_prompt = (
            "你是一个专业的高中化学老师，擅长解答各种化学问题。"
            "请提供详细、准确的解答，包括必要的化学原理、计算步骤和结论。"
            "在回答中，请将所有的化学方程式、离子方程式或分子式使用MathJax格式包裹："
            "- 行内公式使用 $...$ 格式，例如：$H_2SO_4$、$CaCO_3$"
            "- 独立公式使用 $$...$$ 格式，例如：$$2H_2 + O_2 \\rightarrow 2H_2O$$"
            "- 化学反应方程式使用 \\ce{} 命令，例如：$\\ce{H2SO4 + 2NaOH -> Na2SO4 + 2H2O}$"
            "- 离子方程式也使用 \\ce{} 命令，例如：$\\ce{H+ + OH- -> H2O}$"
            "请确保所有化学符号、下标、上标都使用正确的LaTeX语法。"
        )
        
        messages = [SystemMessage(content=system_prompt)]
        if context:
            messages.append(HumanMessage(content=f"背景信息: {context}"))
        messages.append(HumanMessage(content=question))
        
        return self.call_model(model_name, messages)
    
    def fuse_answers(self, question: str, answers: Dict[str, str]) -> Tuple[str, str]:
        """
        融合多个模型的答案
        
        Args:
            question: 原始问题
            answers: 各模型的答案字典 {model_name: answer}
            
        Returns:
            Tuple[str, str]: (融合后的答案, 对比分析)
        """
        if len(answers) < 2:
            # 如果只有一个答案，直接返回
            answer = list(answers.values())[0] if answers else "无可用答案"
            return answer, ""
        
        # 构建融合提示
        fusion_prompt = f"""
作为一个权威的化学专家，请分析以下多个AI模型对同一化学问题的回答，并生成一个融合的权威答复。

原始问题：
{question}

"""
        
        model_labels = ['A', 'B', 'C', 'D', 'E']
        comparison_text = "### 模型答案对比分析\n\n"
        
        for i, (model_name, answer) in enumerate(answers.items()):
            label = model_labels[i] if i < len(model_labels) else f"模型{i+1}"
            fusion_prompt += f"模型{label}（{model_name}）的回答：\n{answer}\n\n"
            comparison_text += f"**模型{label} ({model_name}) 的回答:**\n```\n{answer}\n```\n\n"
        
        fusion_prompt += """
请你：
1. 比较各个回答的准确性、完整性和科学性
2. 识别各个回答中的优点和不足
3. 融合各个回答的优点，生成一个更准确、更完整的权威答复
4. 如果回答有冲突，请基于化学原理做出正确的判断
5. 在最终答复中，请将所有的化学方程式、离子方程式或分子式使用MathJax格式包裹：
   - 行内公式使用 $...$ 格式，例如：$H_2SO_4$、$CaCO_3$
   - 独立公式使用 $$...$$ 格式，例如：$$2H_2 + O_2 \\rightarrow 2H_2O$$
   - 化学反应方程式使用 \\ce{} 命令，例如：$\\ce{H2SO4 + 2NaOH -> Na2SO4 + 2H2O}$
   - 离子方程式也使用 \\ce{} 命令，例如：$\\ce{H+ + OH- -> H2O}$

最终答复：
"""
        
        # 使用最可靠的模型进行融合（优先级：zhipu > openai > tongyi）
        fusion_model = None
        for preferred_model in ['zhipu', 'openai', 'tongyi']:
            if preferred_model in self.models:
                fusion_model = preferred_model
                break
        
        if not fusion_model:
            # 如果没有可用的融合模型，返回简单合并
            combined_answer = "\n\n---\n\n".join([f"**{name}回答：**\n{ans}" for name, ans in answers.items()])
            return clean_output(combined_answer), clean_output(comparison_text)
        
        try:
            messages = [HumanMessage(content=fusion_prompt)]
            fused_answer = self.call_model(fusion_model, messages, temperature=0.3)
            return clean_model_output(fused_answer), clean_output(comparison_text)
        except Exception as e:
            self.logger.error(f"答案融合失败: {str(e)}")
            # 融合失败时返回简单合并
            combined_answer = "\n\n---\n\n".join([f"**{name}回答：**\n{ans}" for name, ans in answers.items()])
            return clean_output(combined_answer), clean_output(comparison_text)