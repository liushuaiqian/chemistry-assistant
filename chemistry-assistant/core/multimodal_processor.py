#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多模态处理器
实现图文混合输入、多模型推理与智能决策的协同问答能力
"""

import base64
import requests
import json
from typing import Union, Dict, Any, List, Tuple
from config import MODEL_CONFIG
from utils.logger import setup_logger
from .llm_manager import LLMManager
from langchain_core.messages import HumanMessage, SystemMessage

class MultimodalProcessor:
    """
    多模态处理器类
    负责处理图像和文本输入，协调多个模型进行推理和结果融合
    """
    
    def __init__(self):
        """
        初始化多模态处理器
        """
        self.logger = setup_logger('multimodal_processor')
        
        # 初始化LLM管理器
        self.llm_manager = LLMManager()
        
        # 加载配置（保留用于视觉API调用）
        self.tongyi_vision_config = MODEL_CONFIG.get('tongyi_vision', {})
        self.tongyi_config = MODEL_CONFIG.get('tongyi', {})
        self.deepseek_config = MODEL_CONFIG.get('deepseek', {})
        self.glm4_plus_config = MODEL_CONFIG.get('zhipu', {})  # GLM-4-Plus通过智谱API调用
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """
        验证配置的有效性
        """
        try:
            # 检查通义视觉配置
            if not self.tongyi_vision_config.get('api_key'):
                self.logger.warning("通义视觉API密钥未配置")
            
            # 检查通义千问配置
            if not self.tongyi_config.get('api_key'):
                self.logger.warning("通义千问API密钥未配置")
            
            # 检查DeepSeek配置
            if not self.deepseek_config.get('api_key'):
                self.logger.warning("DeepSeek API密钥未配置")
            
            # 检查智谱AI配置
            if not self.glm4_plus_config.get('api_key'):
                self.logger.warning("智谱AI API密钥未配置")
                
            self.logger.info("配置验证完成")
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {str(e)}")
            # 不抛出异常，允许系统继续运行

    def process_image_and_text(self, image_base64, text_query):
        """
        处理base64编码的图像和文本查询
        
        Args:
            image_base64 (str): base64编码的图像字符串
            text_query (str): 用户输入的文本查询
            
        Returns:
            str: 处理后的回复
        """
        # 1. 从图像中提取文本
        image_text = self._extract_text_from_image(image_base64, image_format='jpeg')
        
        if "图像识别失败" in image_text or "图像处理出错" in image_text:
            return image_text
        
        # 2. 组合图像文本和用户问题
        if text_query:
            combined_query = f"根据以下图片内容：\n{image_text}\n\n请回答问题：{text_query}"
        else:
            combined_query = image_text

        # 3. 并行调用Tongyi和DeepSeek模型
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_tongyi = executor.submit(self._call_tongyi_model, combined_query)
            future_deepseek = executor.submit(self._call_deepseek_model, combined_query)
            
            tongyi_answer = future_tongyi.result()
            deepseek_answer = future_deepseek.result()
            
        # 4. 融合答案
        fused_answer, _ = self._fuse_answers(combined_query, tongyi_answer, deepseek_answer)
        
        return fused_answer
    
    def process_input(self, input_data: Union[str, bytes], input_type: str = 'auto') -> str:
        """
        处理用户输入（图像或文字）
        
        Args:
            input_data: 输入数据（文字字符串或图像字节数据）
            input_type: 输入类型 ('text', 'image', 'auto')
            
        Returns:
            str: 最终的权威答复
        """
        try:
            # 1. 判断输入类型并提取题干
            if input_type == 'auto':
                input_type = self._detect_input_type(input_data)
            
            if input_type == 'image':
                question_text = self._extract_text_from_image(input_data)
                self.logger.info(f"从图像中提取的题干: {question_text}")
            else:
                question_text = input_data
                self.logger.info(f"直接输入的题干: {question_text}")
            
            # 2. 并行调用两个语言模型生成回答
            tongyi_answer = self._call_tongyi_model(question_text)
            deepseek_answer = self._call_deepseek_model(question_text)
            
            self.logger.info(f"通义千问回答: {tongyi_answer[:100]}...")
            self.logger.info(f"DeepSeek回答: {deepseek_answer[:100]}...")
            
            # 3. 使用GLM-4-Plus融合两个回答
            final_answer, comparison = self._fuse_answers(question_text, tongyi_answer, deepseek_answer)
            
            self.logger.info(f"最终融合答案: {final_answer[:100]}...")
            
            return final_answer, comparison
            
        except Exception as e:
            self.logger.error(f"处理输入时出错: {str(e)}")
            return f"处理过程中出现错误: {str(e)}"
    
    def _detect_input_type(self, input_data: Union[str, bytes]) -> str:
        """
        自动检测输入类型
        
        Args:
            input_data: 输入数据
            
        Returns:
            str: 'text' 或 'image'
        """
        if isinstance(input_data, bytes):
            return 'image'
        elif isinstance(input_data, str):
            # 检查是否为base64编码的图像
            try:
                if input_data.startswith('data:image/'):
                    return 'image'
                base64.b64decode(input_data)
                return 'image'
            except:
                return 'text'
        return 'text'
    
    def _extract_text_from_image(self, image_data: Union[str, bytes], image_format: str = 'jpeg') -> str:
        """
        使用通义视觉模型从图像中提取题干
        
        Args:
            image_data: 图像数据
            
        Returns:
            str: 提取的题干文本
        """
        try:
            # 处理图像数据
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                image_base64 = image_data
            
            # 构建请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.tongyi_vision_config['api_key']}"
            }
            
            data = {
                "model": self.tongyi_vision_config['model'],
                "input": {
                    "messages": [
                        {
                            "role": "system", 
                            "content": [{"text": "你是一个专业的化学助手，擅长识别和分析化学题目。请在识别化学公式时使用MathJax格式，例如：$H_2SO_4$、$CaCO_3$等。"}]
                        },
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:image/{image_format};base64,{image_base64}"},
                                {"text": "请仔细分析这张图片中的化学题目，提取完整的题干内容。如果图片中包含化学方程式、分子式或其他化学符号，请准确识别并转录，并使用MathJax格式表示化学公式，例如：$H_2SO_4$、$$2H_2 + O_2 \\rightarrow 2H_2O$$。"}
                            ]
                        }
                    ]
                },
                "parameters": {
                    "temperature": 0.1,
                    "top_p": 0.8
                }
            }
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                # 新格式的响应中content是一个列表，需要提取text字段
                content = result["output"]["choices"][0]["message"]["content"]
                extracted_text = ""
                
                if isinstance(content, list) and len(content) > 0:
                    # 查找text类型的内容
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            extracted_text = item["text"]
                            break
                    # 如果没有找到text字段，返回第一个字符串内容
                    if not extracted_text:
                        for item in content:
                            if isinstance(item, str):
                                extracted_text = item
                                break
                elif isinstance(content, str):
                    extracted_text = content
                else:
                    extracted_text = str(content)
                
                # 清理编码问题
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
                
                return clean_text(extracted_text)
            else:
                self.logger.error(f"视觉模型API错误: {response.status_code} - {response.text}")
                return "图像识别失败，请重新上传或输入文字题目。"
                
        except Exception as e:
            self.logger.error(f"图像文本提取出错: {str(e)}")
            return "图像处理出错，请重新上传或输入文字题目。"
    
    def _call_tongyi_model(self, question: str) -> str:
        """
        调用通义千问模型生成回答
        
        Args:
            question: 题干文本
            
        Returns:
            str: 通义千问的回答
        """
        try:
            # 使用LangChain LLM管理器调用通义千问
            if self.llm_manager.is_model_available('tongyi'):
                return self.llm_manager.call_chemistry_expert('tongyi', question)
            else:
                # 回退到原始API调用方式
                return self._call_tongyi_api_fallback(question)
                
        except Exception as e:
            self.logger.error(f"调用通义千问模型出错: {str(e)}")
            return "通义千问模型调用出错。"
    
    def _call_tongyi_api_fallback(self, question: str) -> str:
        """
        通义千问API的回退调用方式
        
        Args:
            question: 题干文本
            
        Returns:
            str: 通义千问的回答
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.tongyi_config['api_key']}"
            }
            
            data = {
                "model": self.tongyi_config['model'],
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的高中化学老师，擅长解答各种化学问题。请提供详细、准确的解答，包括必要的化学原理、计算步骤和结论。在回答中，请将所有的化学方程式、离子方程式或分子式使用MathJax格式包裹：行内公式使用 $...$ 格式，例如：$H_2SO_4$、$CaCO_3$；独立公式使用 $$...$$ 格式，例如：$$2H_2 + O_2 \\rightarrow 2H_2O$$；化学反应方程式使用 \\ce{{}} 命令，例如：$\\ce{{H2SO4 + 2NaOH -> Na2SO4 + 2H2O}}$。"
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ]
                },
                "parameters": {
                    "temperature": 0.7,
                    "top_p": 0.8
                }
            }
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["output"]["text"]
            else:
                self.logger.error(f"通义千问API错误: {response.status_code} - {response.text}")
                return "通义千问模型调用失败。"
                
        except Exception as e:
            self.logger.error(f"调用通义千问API出错: {str(e)}")
            return "通义千问模型调用失败。"
    
    def _call_deepseek_model(self, question: str) -> str:
        """
        调用DeepSeek模型生成回答
        
        Args:
            question: 题干文本
            
        Returns:
            str: DeepSeek的回答
        """
        try:
            # 使用LangChain LLM管理器调用DeepSeek
            if self.llm_manager.is_model_available('deepseek'):
                return self.llm_manager.call_chemistry_expert('deepseek', question)
            else:
                # 回退到原始API调用方式
                return self._call_deepseek_api_fallback(question)
                
        except Exception as e:
            self.logger.error(f"调用DeepSeek模型出错: {str(e)}")
            return "DeepSeek模型调用出错。"
    
    def _call_deepseek_api_fallback(self, question: str) -> str:
        """
        DeepSeek API的回退调用方式
        
        Args:
            question: 题干文本
            
        Returns:
            str: DeepSeek的回答
        """
        try:
            import dashscope
            messages = [
                {
                    'role': 'system',
                    'content': '你是一个专业的化学专家，具有深厚的理论基础和丰富的实践经验。请从科学严谨的角度分析和解答化学问题，提供准确的答案和详细的解题思路。在回答中，请将所有的化学方程式、离子方程式或分子式使用MathJax格式包裹：行内公式使用 $...$ 格式，例如：$H_2SO_4$、$CaCO_3$；独立公式使用 $$...$$ 格式，例如：$$2H_2 + O_2 \\rightarrow 2H_2O$$；化学反应方程式使用 \\ce{{}} 命令，例如：$\\ce{{H2SO4 + 2NaOH -> Na2SO4 + 2H2O}}$。'
                },
                {
                    'role': 'user', 
                    'content': question
                }
            ]

            response = dashscope.Generation.call(
                api_key=self.deepseek_config.get('api_key'),
                model=self.deepseek_config.get('model', 'deepseek-v2'),
                messages=messages,
                result_format='message'
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                self.logger.error(f"DeepSeek API错误: {response.status_code} - {response.message}")
                return "DeepSeek模型调用失败。"

        except Exception as e:
            self.logger.error(f"调用DeepSeek API出错: {str(e)}")
            return "DeepSeek模型调用失败。"
    
    def _fuse_answers(self, question: str, answer1: str, answer2: str) -> Tuple[str, str]:
        """
        使用LLM管理器融合两个模型的回答
        
        Args:
            question: 原始题目
            answer1: 通义千问的回答
            answer2: DeepSeek的回答
            
        Returns:
            Tuple[str, str]: (融合后的最终答案, 对比分析)
        """
        try:
            # 构建答案字典
            answers = {
                '通义千问': answer1,
                'DeepSeek': answer2
            }
            
            # 使用LLM管理器进行答案融合
            fused_answer, comparison = self.llm_manager.fuse_answers(question, answers)
            return fused_answer, comparison
            
        except Exception as e:
            self.logger.error(f"答案融合出错: {str(e)}")
            # 如果融合失败，使用内置融合逻辑
            return self._fallback_fuse_answers(question, answer1, answer2)
    
    def _fallback_fuse_answers(self, question: str, tongyi_answer: str, deepseek_answer: str) -> Tuple[str, str]:
        """
        回退的答案融合方法
        
        Args:
            question: 原始题目
            tongyi_answer: 通义千问的回答
            deepseek_answer: DeepSeek的回答
            
        Returns:
            Tuple[str, str]: (融合后的最终答案, 对比分析)
        """
        try:
            # 构建融合提示
            fusion_prompt = f"""作为一个权威的化学专家，请分析以下两个AI模型对同一化学问题的回答，并生成一个融合的权威答复。

原始问题：
{question}

模型A（通义千问）的回答：
{tongyi_answer}

模型B（DeepSeek）的回答：
{deepseek_answer}

请你：
1. 比较两个回答的准确性、完整性和科学性
2. 识别各个回答中的优点和不足
3. 融合两个回答的优点，生成一个更准确、更完整的权威答复
4. 如果回答有冲突，请基于化学原理做出正确的判断
5. 在最终答复中，请将所有的化学方程式、离子方程式或分子式使用MathJax格式包裹：
   - 行内公式使用 $...$ 格式，例如：$H_2SO_4$、$CaCO_3$
   - 独立公式使用 $$...$$ 格式，例如：$$2H_2 + O_2 \\rightarrow 2H_2O$$
   - 化学反应方程式使用 \\ce{{}} 命令，例如：$\\ce{{H2SO4 + 2NaOH -> Na2SO4 + 2H2O}}$
   - 离子方程式也使用 \\ce{{}} 命令，例如：$\\ce{{H+ + OH- -> H2O}}$

最终答复："""
            
            # 使用智谱AI进行融合
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.glm4_plus_config['api_key']}"
            }
            
            data = {
                "model": self.glm4_plus_config.get('model', 'glm-4-plus'),
                "messages": [
                    {
                        "role": "user",
                        "content": fusion_prompt
                    }
                ],
                "temperature": 0.3,
                "top_p": 0.8
            }
            
            response = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                fused_answer = result["choices"][0]["message"]["content"]
                
                # 生成对比分析
                comparison = f"""### 模型答案对比分析

**模型A (通义千问) 的回答:**
```
{tongyi_answer}
```

**模型B (DeepSeek) 的回答:**
```
{deepseek_answer}
```

**融合分析:**
已通过GLM-4-Plus模型对两个回答进行了深度分析和融合，生成了更准确、更完整的权威答复。
"""
                
                return fused_answer, comparison
            else:
                self.logger.error(f"GLM-4-Plus API错误: {response.status_code} - {response.text}")
                # 如果API调用失败，返回简单合并
                comparison = f"""### 模型答案对比分析

**模型A (通义千问) 的回答:**
```
{tongyi_answer}
```

**模型B (DeepSeek) 的回答:**
```
{deepseek_answer}
```

"""
                combined_answer = f"**通义千问回答：**\n{tongyi_answer}\n\n**DeepSeek回答：**\n{deepseek_answer}"
                return combined_answer, comparison
                
        except Exception as e:
            self.logger.error(f"回退融合方法出错: {str(e)}")
            # 最终回退：简单合并
            comparison = f"""### 模型答案对比分析

**模型A (通义千问) 的回答:**
```
{tongyi_answer}
```

**模型B (DeepSeek) 的回答:**
```
{deepseek_answer}
```

"""
            combined_answer = f"**通义千问回答：**\n{tongyi_answer}\n\n**DeepSeek回答：**\n{deepseek_answer}"
            return combined_answer, comparison