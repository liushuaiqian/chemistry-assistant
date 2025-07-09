#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多模态处理器
实现图文混合输入、多模型推理与智能决策的协同问答能力
"""

import base64
import requests
import json
from typing import Union, Dict, Any, List
from config import MODEL_CONFIG
from utils.logger import setup_logger

class MultimodalProcessor:
    """
    多模态处理器类
    负责处理图像和文本输入，协调多个模型进行推理和结果融合
    """
    
    def __init__(self):
        """
        初始化多模态处理器
        """
        self.logger = setup_logger(__name__)
        
        # 加载各模型配置
        self.tongyi_vision_config = MODEL_CONFIG.get('tongyi_vision', {})
        self.tongyi_config = MODEL_CONFIG.get('tongyi', {})
        self.deepseek_config = MODEL_CONFIG.get('deepseek', {})
        self.glm4_plus_config = MODEL_CONFIG.get('glm4_plus', {})

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
        fused_answer = self._fuse_answers(combined_query, tongyi_answer, deepseek_answer)
        
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
            final_answer = self._fuse_answers(question_text, tongyi_answer, deepseek_answer)
            
            self.logger.info(f"最终融合答案: {final_answer[:100]}...")
            
            return final_answer
            
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
                            "content": [{"text": "你是一个专业的化学助手，擅长识别和分析化学题目。"}]
                        },
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:image/{image_format};base64,{image_base64}"},
                                {"text": "请仔细分析这张图片中的化学题目，提取完整的题干内容。如果图片中包含化学方程式、分子式或其他化学符号，请准确识别并转录。"}
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
                if isinstance(content, list) and len(content) > 0:
                    # 查找text类型的内容
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            return item["text"]
                    # 如果没有找到text字段，返回第一个字符串内容
                    for item in content:
                        if isinstance(item, str):
                            return item
                elif isinstance(content, str):
                    return content
                else:
                    return str(content)
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
                            "content": "你是一个专业的高中化学老师，擅长解答各种化学问题。请提供详细、准确的解答，包括必要的化学原理、计算步骤和结论。"
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
            self.logger.error(f"调用通义千问模型出错: {str(e)}")
            return "通义千问模型调用出错。"
    
    def _call_deepseek_model(self, question: str) -> str:
        """
        调用DeepSeek模型生成回答（通过通义API）
        
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
                    'content': '你是一个专业的化学专家，具有深厚的理论基础和丰富的实践经验。请从科学严谨的角度分析和解答化学问题，提供准确的答案和详细的解题思路。'
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
            self.logger.error(f"调用DeepSeek模型出错: {str(e)}")
            return "DeepSeek模型调用出错。"
    
    def _fuse_answers(self, question: str, answer1: str, answer2: str) -> str:
        """
        使用GLM-4-Plus融合两个模型的回答
        
        Args:
            question: 原始题目
            answer1: 通义千问的回答
            answer2: DeepSeek的回答
            
        Returns:
            str: 融合后的最终答案
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.glm4_plus_config['api_key']}"
            }
            
            fusion_prompt = f"""
作为一个权威的化学专家，请分析以下两个AI模型对同一化学问题的回答，并生成一个融合的权威答复。

原始问题：
{question}

模型A（通义千问）的回答：
{answer1}

模型B（DeepSeek）的回答：
{answer2}

请你：
1. 比较两个回答的准确性、完整性和科学性
2. 识别两个回答中的优点和不足
3. 融合两个回答的优点，生成一个更准确、更完整的权威答复
4. 如果两个回答有冲突，请基于化学原理做出正确的判断
5. 在最终答复中，请将所有的化学方程式、离子方程式或分子式使用LaTeX格式包裹，例如，单个公式使用`$...$`，多行或独立的公式使用`$$...$$`。

最终答复：
"""
            
            data = {
                "model": self.glm4_plus_config['model'],
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
                return result["choices"][0]["message"]["content"]
            else:
                self.logger.error(f"GLM-4-Plus API错误: {response.status_code} - {response.text}")
                # 如果融合失败，返回两个回答的简单合并
                return f"**通义千问回答：**\n{answer1}\n\n**DeepSeek回答：**\n{answer2}"
                
        except Exception as e:
            self.logger.error(f"答案融合出错: {str(e)}")
            # 如果融合失败，返回两个回答的简单合并
            return f"**通义千问回答：**\n{answer1}\n\n**DeepSeek回答：**\n{answer2}"