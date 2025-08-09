#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学分析链 - 重新设计的并行处理架构

设计思路：
1. 多模态输入处理：
   - 图片输入：使用视觉模型（qwen-vl）解析图片内容，提取化学题目文本
   - 文字输入：直接传递，无需额外处理
   - 混合输入：图片解析结果与文字问题结合

2. 并行模型调用架构：
   - 同时调用多个大语言模型进行问题分析和解答
   - 当前支持：qwen3 (通义千问) 和 deepseek-r1 和 文心4.5
   - 架构设计支持后续扩展更多模型
   - 每个模型独立处理，避免相互影响

3. 结果整合与输出：
   - 收集所有模型的响应结果
   - 使用专门的整合算法融合多个答案
   - 生成综合性的最终回答
   - 提供模型对比分析（可选）

4. 核心优势：
   - 并行处理提高响应速度
   - 多模型结果提高答案准确性和全面性
   - 模块化设计便于扩展和维护
   - 支持视觉识别的多模态处理

5. 处理流程：
   输入 → 模态处理（视觉/文本） → 并行模型调用 → 结果整合 → 输出
"""

import logging
import base64
import requests
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Tuple, Union
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage
from .llm_manager import LLMManager
from tools.rag_retriever import RAGRetriever
from config import MODEL_CONFIG
from utils.output_cleaner import clean_output, clean_model_output, clean_parallel_output, format_output

class ChemistryAnalysisChain:
    """
    化学分析链类 - 并行处理架构
    实现多模态输入处理和并行模型调用
    """
    
    def __init__(self, use_reranker=True, enable_adaptive=True):
        """
        初始化化学分析链
        
        Args:
            use_reranker (bool): 是否启用文本排序器进行双阶段检索
            enable_adaptive (bool): 是否启用自适应检索
        """
        self.logger = logging.getLogger(__name__)
        self.llm_manager = LLMManager()
        
        # 初始化RAG检索器，支持双阶段检索和自适应检索
        self.rag_retriever = RAGRetriever(use_reranker=use_reranker, enable_adaptive=enable_adaptive)
        self.use_reranker = use_reranker
        self.enable_adaptive = enable_adaptive
        
        # 初始化视觉模型配置
        self.vision_config = MODEL_CONFIG.get('tongyi_vision', {})
        
        # 配置并行处理的模型列表
        self.parallel_models = ['tongyi', 'deepseek', 'qianfan', 'ernie_x1']  # qwen3通过tongyi调用，deepseek-r1，新增ERNIE-X1-Turbo-32K
        
        # 初始化线程池用于并行处理
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max(4, len(self.parallel_models)))
        
        self._setup_prompts()
        self._setup_chains()
        
        # 记录排序器和自适应检索状态
        reranker_info = self.rag_retriever.get_reranker_info()
        adaptive_info = self.rag_retriever.get_adaptive_info()
        
        if adaptive_info['enabled'] and adaptive_info['available']:
            self.logger.info("化学分析链已启用自适应检索系统")
            if reranker_info['enabled'] and reranker_info['available']:
                self.logger.info("- 双阶段检索（向量检索+文本排序）已启用")
            self.logger.info(f"- 支持策略: {', '.join(adaptive_info['supported_strategies'])}")
        elif reranker_info['enabled'] and reranker_info['available']:
            self.logger.info("化学分析链已启用双阶段检索（向量检索+文本排序）")
        else:
            self.logger.info("化学分析链使用传统向量检索模式")
    
    def _setup_prompts(self):
        """
        设置提示模板
        """
        # 问题分类提示模板
        self.classification_prompt = PromptTemplate(
            input_variables=["question"],
            template="""
你是一个化学教育专家。请分析以下化学问题的类型和难度级别。

问题: {question}

请按以下格式回答：
类型: [有机化学/无机化学/物理化学/分析化学/生物化学]
难度: [基础/中等/困难]
关键概念: [列出3-5个相关的化学概念]
解题策略: [简述解题思路]
"""
        )
        
        # 多角度分析提示模板
        self.analysis_prompt = PromptTemplate(
            input_variables=["question", "classification"],
            template="""
基于问题分类信息，请从多个角度分析这个化学问题：

问题: {question}

分类信息: {classification}

请提供：
1. 理论基础分析
2. 实验角度分析（如适用）
3. 计算方法分析（如适用）
4. 实际应用联系
5. 常见错误提醒

请确保分析全面且准确。
"""
        )
        
        # RAG 检索加强提示模板
        self.rag_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
你是一个化学专家，请根据以下背景知识来回答问题。
如果背景知识不足以回答问题，请直接说明"知识库中没有相关信息"。

背景知识:
{context}

问题: {question}
"""
        )

        # 解答生成提示模板
        self.solution_prompt = PromptTemplate(
            input_variables=["question", "classification", "analysis"],
            template="""
基于前面的分类和分析，请生成这个化学问题的完整解答：

问题: {question}

分类信息: {classification}

多角度分析: {analysis}

请提供：
1. 详细的解题步骤
2. 必要的化学方程式（使用LaTeX格式）
3. 计算过程（如适用）
4. 最终答案
5. 解题要点总结

确保解答准确、完整、易懂。
"""
        )
    
    def _create_rag_chain(self):
        """
        创建RAG检索链
        """
        retriever = self.rag_retriever.get_retriever(db_name='textbooks')
        if not retriever:
            return None

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # 创建一个简化的RAG链，直接使用LLM管理器
        def rag_invoke(inputs):
            context = inputs["context"]
            question = inputs["question"]
            prompt_text = self.rag_prompt.format(context=context, question=question)
            messages = [HumanMessage(content=prompt_text)]
            return self.llm_manager.call_model("default", messages)
        
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | RunnableLambda(rag_invoke)
        )
        return rag_chain

    def _setup_chains(self):
        """
        设置分析链
        """
        self._rag_chain = self._create_rag_chain()
    
    def extract_text_from_image(self, image_data: Union[str, bytes], image_format: str = 'jpeg') -> str:
        """
        使用qwen视觉模型从图像中提取文本内容
        
        Args:
            image_data: 图像数据（base64字符串或字节数据）
            image_format: 图像格式
            
        Returns:
            str: 提取的文本内容
        """
        try:
            # 处理图像数据
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                # 如果是base64字符串，去掉可能的前缀
                if image_data.startswith('data:image/'):
                    image_base64 = image_data.split(',')[1]
                else:
                    image_base64 = image_data
            
            # 检查视觉模型配置
            if not self.vision_config.get('api_key'):
                self.logger.error("qwen视觉模型API密钥未配置")
                return "视觉模型未配置，无法识别图片内容。"
            
            # 构建请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.vision_config['api_key']}"
            }
            
            data = {
                "model": self.vision_config.get('model', 'qwen-vl-plus'),
                "input": {
                    "messages": [
                        {
                            "role": "system", 
                            "content": [{
                                "text": "你是一个专业的化学助手，擅长识别和分析化学题目。请仔细识别图片中的所有文字内容，特别是化学公式、方程式和数值。在识别化学公式时使用MathJax格式，例如：$H_2SO_4$、$CaCO_3$等。"
                            }]
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
            
            # 调用qwen视觉API
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                # 解析响应内容
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
                
                self.logger.info(f"视觉模型成功识别图片内容: {extracted_text[:100]}...")
                return extracted_text
            else:
                self.logger.error(f"qwen视觉模型API错误: {response.status_code} - {response.text}")
                return "图像识别失败，请重新上传或输入文字题目。"
                
        except Exception as e:
            self.logger.error(f"图像文本提取出错: {str(e)}")
            return "图像处理出错，请重新上传或输入文字题目。"
    
    def process_with_vision(self, question: str = None, image_data: Union[str, bytes] = None, function_type: str = "智能问答") -> Dict[str, Any]:
        """
        新架构：多模态输入处理 + 并行模型调用
        
        Args:
            question: 文本问题（可选）
            image_data: 图片数据（可选）
            function_type: 功能类型（"信息检索" 或 "智能问答"）
            
        Returns:
            Dict[str, Any]: 包含并行处理结果和整合答案的字典
        """
        try:
            # 第一步：多模态输入处理
            processed_input = self._process_multimodal_input(question, image_data)
            if isinstance(processed_input, dict) and 'error' in processed_input:
                return processed_input
            
            # 处理不同的输入格式
            if isinstance(processed_input, dict) and 'has_image' in processed_input:
                # 有图片的情况
                processed_question = processed_input['question']
                image_data_for_models = processed_input['image_data']
                has_image = True
                
                # 使用qwen-vl提取图片中的文本内容，供非多模态模型使用
                self.logger.info("[图片解析] 开始使用qwen-vl解析图片内容...")
                extracted_text = self.extract_text_from_image(image_data_for_models)
                
                if extracted_text and not extracted_text.startswith(("视觉模型未配置", "图像识别失败", "图像处理出错")):
                    # 将解析出的图片文本与原问题结合
                    if question and question.strip():
                        enhanced_question = f"{question.strip()}\n\n图片内容：{extracted_text}"
                    else:
                        enhanced_question = f"请分析这个化学题目并给出详细的解答思路和步骤。\n\n图片内容：{extracted_text}"
                    
                    self.logger.info(f"[图片解析] 成功解析图片内容，增强问题长度: {len(enhanced_question)} 字符")
                    processed_question_for_text_models = enhanced_question
                else:
                    self.logger.warning("[图片解析] 图片解析失败，非多模态模型将使用原始问题")
                    processed_question_for_text_models = processed_question
            else:
                # 纯文字的情况
                processed_question = processed_input
                processed_question_for_text_models = processed_input
                image_data_for_models = None
                has_image = False
            
            self.logger.info(f"[并行处理] 开始处理问题: {processed_question[:100]}...")
            if has_image:
                self.logger.info("[并行处理] 检测到图片输入，将调用ERNIE VL视觉模型，并为非多模态模型提供图片解析文本")
            
            # 第二步：并行调用多个模型
            parallel_results = self._parallel_model_call(processed_question, processed_question_for_text_models, image_data_for_models, has_image)
            
            # 第三步：结果整合
            integrated_result = self._integrate_results(parallel_results, processed_question)
            
            # 清理所有输出内容
            cleaned_parallel_results = clean_parallel_output(parallel_results)
            cleaned_integrated_result = clean_output(integrated_result)
            cleaned_comparison = clean_output(self._generate_model_comparison(parallel_results))
            
            return {
                'question': clean_output(processed_question),
                'parallel_results': cleaned_parallel_results,
                'integrated_answer': cleaned_integrated_result,
                'model_comparison': cleaned_comparison,
                'processing_info': {
                    'models_used': self.parallel_models,
                    'processing_time': 'calculated_in_implementation',
                    'success_rate': len([r for r in parallel_results.values() if 'error' not in r]) / len(parallel_results)
                }
            }
                
        except Exception as e:
            self.logger.error(f"[并行处理] 处理过程中出错: {str(e)}")
            return {
                'error': f"处理过程中出现错误: {str(e)}",
                'question': question or 'N/A',
                'parallel_results': {},
                'integrated_answer': '',
                'model_comparison': '',
                'processing_info': {}
            }
    
    def _process_multimodal_input(self, question: str = None, image_data: Union[str, bytes] = None) -> Union[str, Dict[str, str]]:
        """
        处理多模态输入（图片+文字）
        
        Args:
            question: 文本问题
            image_data: 图片数据
            
        Returns:
            Union[str, Dict]: 处理后的问题文本或错误信息，如果有图片则返回包含image_data的字典
        """
        try:
            # 处理图片输入
            if image_data:
                self.logger.info("[多模态处理] 检测到图片输入，准备调用ERNIE VL视觉模型...")
                
                # 准备问题文本
                if question and question.strip():
                    final_question = question.strip()
                else:
                    final_question = "请分析这个化学题目并给出详细的解答思路和步骤。"
                    
                self.logger.info(f"[多模态处理] 图片处理准备完成，问题: {final_question[:50]}...")
                
                # 返回包含图片数据的字典，用于ERNIE VL模型调用
                return {
                    'question': final_question,
                    'image_data': image_data,
                    'has_image': True
                }
            else:
                # 纯文字输入
                if not question or not question.strip():
                    return {'error': "请提供问题文本或上传图片。"}
                return question.strip()
                
        except Exception as e:
            self.logger.error(f"[多模态处理] 输入处理失败: {str(e)}")
            return {'error': f"输入处理失败: {str(e)}"}

    def _parallel_model_call(self, question: str, enhanced_question_for_text_models: str = None, image_data: Union[str, bytes] = None, has_image: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        并行调用多个模型进行问题处理
        
        Args:
            question: 原始问题文本（用于ERNIE VL等视觉模型）
            enhanced_question_for_text_models: 增强后的问题文本（包含图片解析内容，用于非多模态模型）
            image_data: 图片数据（可选）
            has_image: 是否包含图片
            
        Returns:
            Dict[str, Dict]: 各模型的处理结果
        """
        # 确定要调用的模型列表
        models_to_call = self.parallel_models.copy()
        if has_image and image_data:
            models_to_call.append('ernie_vl')  # 有图片时增加ERNIE VL模型
            self.logger.info("[并行调用] 检测到图片输入，增加ERNIE VL视觉模型")
        
        self.logger.info(f"[并行调用] 开始并行调用 {len(models_to_call)} 个模型")
        
        # 为每个模型创建处理任务
        future_to_model = {}
        results = {}
        
        for model_name in models_to_call:
            if model_name == 'ernie_vl':
                # 特殊处理ERNIE VL模型
                if has_image and image_data:
                    try:
                        future = self.executor.submit(self._ernie_vl_process, question, image_data)
                        future_to_model[future] = model_name
                        self.logger.info(f"[并行调用] 已提交ERNIE VL视觉模型的处理任务")
                    except Exception as e:
                        self.logger.error(f"[并行调用] 提交ERNIE VL模型任务失败: {str(e)}")
                        results[model_name] = {
                            'error': f"任务提交失败: {str(e)}",
                            'answer': '',
                            'processing_time': 0,
                            'success': False
                        }
            elif self.llm_manager.is_model_available(model_name):
                try:
                    # 为非多模态模型使用增强后的问题文本（如果有图片的话）
                    question_for_model = enhanced_question_for_text_models if (has_image and enhanced_question_for_text_models) else question
                    future = self.executor.submit(self._single_model_process, model_name, question_for_model)
                    future_to_model[future] = model_name
                    if has_image and enhanced_question_for_text_models:
                        self.logger.info(f"[并行调用] 已提交模型 {model_name} 的处理任务（使用图片解析文本）")
                    else:
                        self.logger.info(f"[并行调用] 已提交模型 {model_name} 的处理任务")
                except Exception as e:
                    self.logger.error(f"[并行调用] 提交模型 {model_name} 任务失败: {str(e)}")
                    results[model_name] = {
                        'error': f"任务提交失败: {str(e)}",
                        'answer': '',
                        'processing_time': 0,
                        'success': False
                    }
            else:
                self.logger.warning(f"[并行调用] 模型 {model_name} 不可用，跳过")
                results[model_name] = {
                    'error': f"模型 {model_name} 不可用",
                    'answer': '',
                    'processing_time': 0,
                    'success': False
                }
        
        if not future_to_model:
            self.logger.error("[并行调用] 没有可用的模型任务")
            return results
        
        # 收集结果，增强错误处理
        try:
            for future in concurrent.futures.as_completed(future_to_model, timeout=300):  # 5分钟超时
                model_name = future_to_model[future]
                try:
                    # 为不同模型设置不同的超时时间
                    if model_name in ['deepseek', 'ernie_x1']:
                        timeout = 240  # deepseek和文心x1设置为4分钟
                        self.logger.info(f"[并行调用] 模型 {model_name} 使用4分钟超时")
                    else:
                        timeout = 30   # 其他模型保持30秒超时
                    
                    result = future.result(timeout=timeout)
                    results[model_name] = result
                    self.logger.info(f"[并行调用] 模型 {model_name} 处理完成")
                except concurrent.futures.TimeoutError:
                    timeout_used = 240 if model_name in ['deepseek', 'ernie_x1'] else 30
                    self.logger.error(f"[并行调用] 模型 {model_name} 处理超时（{timeout_used}秒）")
                    results[model_name] = {
                        'error': f"模型 {model_name} 处理超时（{timeout_used}秒）",
                        'answer': '',
                        'processing_time': timeout_used,
                        'success': False
                    }
                except Exception as e:
                    self.logger.error(f"[并行调用] 模型 {model_name} 处理失败: {str(e)}")
                    results[model_name] = {
                        'error': f"处理失败: {str(e)}",
                        'answer': '',
                        'processing_time': 0,
                        'success': False
                    }
        except concurrent.futures.TimeoutError:
            self.logger.error("[并行调用] 整体处理超时，处理未完成的任务")
            # 处理未完成的任务
            for future, model_name in future_to_model.items():
                if model_name not in results:
                    # 为不同模型设置相应的超时时间
                    timeout_used = 240 if model_name in ['deepseek', 'ernie_x1'] else 120
                    results[model_name] = {
                        'error': f"模型 {model_name} 整体超时未完成（{timeout_used}秒）",
                        'answer': '',
                        'processing_time': timeout_used,
                        'success': False
                    }
        except Exception as e:
            self.logger.error(f"[并行调用] 收集结果时发生异常: {str(e)}")
            # 确保所有模型都有结果
            for future, model_name in future_to_model.items():
                if model_name not in results:
                    results[model_name] = {
                        'error': f"模型 {model_name} 收集结果异常: {str(e)}",
                        'answer': '',
                        'processing_time': 0,
                        'success': False
                    }
        
        successful_count = len([r for r in results.values() if r.get('success', False)])
        self.logger.info(f"[并行调用] 完成，成功: {successful_count}/{len(results)}")
        return results
    
    def _ernie_vl_process(self, question: str, image_data: Union[str, bytes]) -> Dict[str, Any]:
        """
        ERNIE VL视觉模型的处理逻辑
        
        Args:
            question: 问题文本
            image_data: 图片数据
            
        Returns:
            Dict[str, Any]: ERNIE VL模型的处理结果
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info("[ERNIE VL] 开始处理视觉问题")
            
            # 调用ERNIE VL模型
            result = self.llm_manager.call_ernie_vl(question, image_data)
            
            processing_time = time.time() - start_time
            
            if result and 'error' not in result:
                self.logger.info(f"[ERNIE VL] 处理成功，耗时: {processing_time:.2f}秒")
                return {
                    'answer': result,
                    'processing_time': processing_time,
                    'success': True,
                    'model_type': 'vision_multimodal'
                }
            else:
                error_msg = result.get('error', '未知错误') if result else '返回结果为空'
                self.logger.error(f"[ERNIE VL] 处理失败: {error_msg}")
                return {
                    'error': f"ERNIE VL处理失败: {error_msg}",
                    'answer': '',
                    'processing_time': processing_time,
                    'success': False,
                    'model_type': 'vision_multimodal'
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"[ERNIE VL] 处理异常: {str(e)}")
            return {
                'error': f"ERNIE VL处理异常: {str(e)}",
                'answer': '',
                'processing_time': processing_time,
                'success': False,
                'model_type': 'vision_multimodal'
            }
    
    def _single_model_process(self, model_name: str, question: str) -> Dict[str, Any]:
        """
        单个模型的处理逻辑，集成RAG检索功能
        
        Args:
            model_name: 模型名称
            question: 问题文本
            
        Returns:
            Dict[str, Any]: 单个模型的处理结果
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"[{model_name}] 开始处理问题")
            
            # 使用RAG检索相关知识
            rag_context = ""
            try:
                # 使用综合检索功能，同时从教材和题库检索
                retrieved_docs = self.rag_retriever.retrieve_comprehensive(
                    query=question,
                    textbook_k=3,
                    question_k=2,
                    rerank_top_n=4
                )
                
                if retrieved_docs:
                    rag_context = "\n\n".join(retrieved_docs[:4])  # 限制上下文长度
                    self.logger.info(f"[{model_name}] RAG检索到{len(retrieved_docs)}个相关文档")
                else:
                    self.logger.info(f"[{model_name}] RAG检索未找到相关文档")
                    
            except Exception as rag_error:
                self.logger.warning(f"[{model_name}] RAG检索失败: {str(rag_error)}")
            
            # 构建增强的化学问题处理提示
            if rag_context:
                prompt = f"""
你是一个专业的化学助手，请根据以下背景知识详细分析并回答化学问题。

背景知识：
{rag_context}

问题：{question}

请基于背景知识提供：
1. 问题分析和解题思路
2. 详细的解答步骤
3. 相关的化学原理和公式
4. 最终答案
5. 解题要点总结

**严格的输出格式要求：**
1. **化学公式格式化**：
   - 所有化学分子式必须使用下标格式：H₂O、CH₄、C₂H₄、H₂SO₄、CaCO₃等
   - 离子公式使用上下标：Ca²⁺、SO₄²⁻、OH⁻等
   - 绝对禁止使用H2O、CH4、C2H4等普通数字格式

2. **化学反应方程式**：
   - 使用标准反应箭头：→（而非->或=>）
   - 完整格式示例：CH₄ + 2O₂ → CO₂ + 2H₂O
   - 可逆反应使用：⇌
   - 条件标注在箭头上方或下方

3. **Markdown结构**：
   - 使用清晰的标题层级（##、###）
   - 重要步骤使用有序列表
   - 关键概念使用**粗体**强调
   - 计算过程使用代码块或表格展示

4. **数学公式**：
   - 复杂计算使用LaTeX格式：$\\Delta H = \\sum H_{{products}} - \\sum H_{{reactants}}$
   - 简单数值计算直接显示：25°C、1.5 mol、98.5%

如果背景知识不足以完全回答问题，请结合你的专业知识进行补充。请严格按照上述格式要求输出答案，确保所有化学公式都使用正确的下标格式，所有反应箭头都使用标准符号。
"""
            else:
                prompt = f"""
你是一个专业的化学助手，请详细分析并回答以下化学问题。

问题：{question}

请提供：
1. 问题分析和解题思路
2. 详细的解答步骤
3. 相关的化学原理和公式
4. 最终答案
5. 解题要点总结

**严格的输出格式要求：**
1. **化学公式格式化**：
   - 所有化学分子式必须使用下标格式：H₂O、CH₄、C₂H₄、H₂SO₄、CaCO₃等
   - 离子公式使用上下标：Ca²⁺、SO₄²⁻、OH⁻等
   - 绝对禁止使用H2O、CH4、C2H4等普通数字格式

2. **化学反应方程式**：
   - 使用标准反应箭头：→（而非->或=>）
   - 完整格式示例：CH₄ + 2O₂ → CO₂ + 2H₂O
   - 可逆反应使用：⇌
   - 条件标注在箭头上方或下方

3. **Markdown结构**：
   - 使用清晰的标题层级（##、###）
   - 重要步骤使用有序列表
   - 关键概念使用**粗体**强调
   - 计算过程使用代码块或表格展示

4. **数学公式**：
   - 复杂计算使用LaTeX格式：$\\Delta H = \\sum H_{{products}} - \\sum H_{{reactants}}$
   - 简单数值计算直接显示：25°C、1.5 mol、98.5%

请严格按照上述格式要求输出答案，确保所有化学公式都使用正确的下标格式，所有反应箭头都使用标准符号。
"""
            
            messages = [HumanMessage(content=prompt)]
            response = self.llm_manager.call_model(model_name, messages, temperature=0.3)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"[{model_name}] 处理完成，耗时: {processing_time:.2f}秒")
            
            return {
                'answer': response,
                'processing_time': processing_time,
                'model_name': model_name,
                'success': True,
                'rag_used': bool(rag_context),
                'rag_docs_count': len(retrieved_docs) if 'retrieved_docs' in locals() else 0
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"[{model_name}] 处理失败: {str(e)}")
            return {
                'error': f"模型 {model_name} 处理失败: {str(e)}",
                'answer': '',
                'processing_time': processing_time,
                'model_name': model_name,
                'success': False,
                'rag_used': False,
                'rag_docs_count': 0
            }
    
    def _integrate_results(self, parallel_results: Dict[str, Dict[str, Any]], question: str) -> str:
        """
        整合多个模型的结果，专门优化Markdown格式输出
        """
        try:
            # 导入输出清理器
            from utils.output_cleaner import output_cleaner
            
            successful_results = {k: v for k, v in parallel_results.items() if v.get('success', False) and v.get('answer', '').strip()}
            if not successful_results:
                return "所有模型处理失败，无法生成答案。"
            
            # 单个模型结果直接返回，但要清理格式
            if len(successful_results) == 1:
                model_name, result = list(successful_results.items())[0]
                cleaned_answer = output_cleaner.clean_model_response(result['answer'])
                return f"## {model_name} 模型回答\n\n{cleaned_answer}"
            
            # 多个模型结果需要融合
            self.logger.info(f"[结果整合] 开始整合 {len(successful_results)} 个模型的结果")
            
            # 为每个模型输出进行专门的清理和格式化
            cleaned_results = {}
            for model_name, result in successful_results.items():
                cleaned_answer = output_cleaner.sanitize_model_output_for_fusion(
                    result['answer'], model_name
                )
                cleaned_results[model_name] = {
                    **result,
                    'answer': cleaned_answer
                }
            
            # 检查答案相似度，避免不必要的融合
            from difflib import SequenceMatcher
            if len(cleaned_results) == 2:
                answers = [r['answer'] for r in cleaned_results.values()]
                similarity = SequenceMatcher(None, answers[0], answers[1]).ratio()
                if similarity > 0.8:
                    first_model = list(cleaned_results.keys())[0]
                    first_answer = cleaned_results[first_model]['answer']
                    return f"## 融合答案（模型答案高度相似）\n\n{first_answer}"
            
            # 构建专业的融合提示词
            fusion_model = None
            if self.llm_manager.is_model_available('moonshot_kimi'):
                fusion_model = 'moonshot_kimi'
                self.logger.info("[结果整合] 使用专门的融合模型 Moonshot-Kimi")
                integration_prompt = self._build_chemistry_fusion_prompt(question, cleaned_results)
            else:
                # 降级到现有模型
                fusion_model = self._select_best_model(['tongyi', 'deepseek', 'zhipu'])
                self.logger.info(f"[结果整合] 融合模型不可用，降级使用 {fusion_model}")
                integration_prompt = self._build_simple_fusion_prompt(question, cleaned_results)
            
            if fusion_model:
                messages = [HumanMessage(content=integration_prompt)]
                integrated_answer = self.llm_manager.call_model(fusion_model, messages, temperature=0.2)
                self.logger.info(f"[结果整合] 使用 {fusion_model} 完成结果整合")
                
                # 对融合结果进行最终清理
                final_answer = output_cleaner.format_final_output(
                    integrated_answer, "融合答案"
                )
                return final_answer
            else:
                # 如果无法整合，返回第一个清理后的结果
                first_model, first_result = list(cleaned_results.items())[0]
                return output_cleaner.format_final_output(
                    first_result['answer'], f"{first_model} 模型回答"
                )
                
        except Exception as e:
            self.logger.error(f"[结果整合] 整合失败: {str(e)}")
            # 返回第一个可用结果
            if parallel_results:
                for model_name, result in parallel_results.items():
                    if result.get('answer', '').strip():
                        from utils.output_cleaner import output_cleaner
                        cleaned = output_cleaner.clean_model_response(result['answer'])
                        return output_cleaner.format_final_output(
                            cleaned, f"{model_name} 模型回答（备用）"
                        )
            return "结果整合失败，无法生成答案。"
    
    def _build_chemistry_fusion_prompt(self, question: str, successful_results: Dict[str, Dict[str, Any]]) -> str:
        """
        为专门的融合模型构建化学领域专业的融合提示词
        
        Args:
            question: 原始化学问题
            successful_results: 成功的模型结果字典
            
        Returns:
            str: 专业的融合提示词
        """
        prompt = f"""你是一位资深的化学教育专家和AI答案评估专家，专门负责整合多个AI模型对化学问题的回答。

**原始化学问题：**
{question}

**评估标准：**
1. 化学概念和原理的准确性
2. 化学计算过程的正确性和完整性
3. 化学公式、方程式的规范性
4. 解释的逻辑性和教学价值
5. 答案的完整性和实用性

**各模型回答分析：**
"""
        
        # 添加各模型的回答（已经过清理和格式化）
        model_labels = ['A', 'B', 'C', 'D', 'E']
        for i, (model_name, result) in enumerate(successful_results.items()):
            label = model_labels[i] if i < len(model_labels) else f"模型{i+1}"
            # 直接使用已经清理和格式化的答案
            prompt += f"\n**模型{label} ({model_name}) 的回答：**\n{result['answer']}\n"
        
        prompt += f"""

**融合任务要求：**
1. **准确性优先**：确保化学概念、公式、计算完全正确
2. **完整性保证**：整合各模型的优点，补充遗漏信息
3. **逻辑清晰**：按照化学问题解答的标准流程组织答案
4. **规范表达**：使用标准的化学术语和规范的化学公式格式
5. **教学价值**：提供清晰的解题思路和知识点解释
6. **分歧处理**：如果模型间有分歧，请分析原因并给出最合理的解释

**严格的输出格式要求：**
1. **化学公式格式化**：
   - 所有化学分子式必须使用下标格式：H₂O、CH₄、C₂H₄、H₂SO₄、CaCO₃等
   - 离子公式使用上下标：Ca²⁺、SO₄²⁻、OH⁻等
   - 绝对禁止使用H2O、CH4、C2H4等普通数字格式

2. **化学反应方程式**：
   - 使用标准反应箭头：→（而非->或=>）
   - 完整格式示例：CH₄ + 2O₂ → CO₂ + 2H₂O
   - 可逆反应使用：⇌
   - 条件标注在箭头上方或下方

3. **Markdown结构**：
   - 使用清晰的标题层级（##、###）
   - 重要步骤使用有序列表
   - 关键概念使用**粗体**强调
   - 计算过程使用代码块或表格展示

4. **数学公式**：
   - 复杂计算使用LaTeX格式：$\\Delta H = \\sum H_{{products}} - \\sum H_{{reactants}}$
   - 简单数值计算直接显示：25°C、1.5 mol、98.5%

5. **内容组织**：
   - 问题分析 → 解题思路 → 详细步骤 → 最终答案 → 知识点总结
   - 每个化学现象都要有科学解释
   - 重要的化学原理要单独说明

**最终融合答案：**
请严格按照上述格式要求输出融合后的答案，确保所有化学公式都使用正确的下标格式，所有反应箭头都使用标准符号。不要添加额外的标题或说明。
"""
        
        return prompt
    
    def _build_simple_fusion_prompt(self, question: str, successful_results: Dict[str, Dict[str, Any]]) -> str:
        """
        为普通模型构建简单的融合提示词
        
        Args:
            question: 原始化学问题
            successful_results: 成功的模型结果字典
            
        Returns:
            str: 简单的融合提示词
        """
        prompt = f"""你是一个化学专家，现在需要整合多个AI模型对同一化学问题的回答，生成一个最优的综合答案。

原始问题：{question}

各模型回答：
"""
        
        # 添加各模型的回答（已经过清理和格式化）
        for model_name, result in successful_results.items():
            prompt += f"\n**{model_name} 模型回答：**\n{result['answer']}\n\n---\n"
        
        prompt += """
请基于以上多个模型的回答，生成一个综合的、最优的答案。

**严格的输出格式要求：**
1. **化学公式格式化**：
   - 所有化学分子式必须使用下标格式：H₂O、CH₄、C₂H₄、H₂SO₄、CaCO₃等
   - 离子公式使用上下标：Ca²⁺、SO₄²⁻、OH⁻等
   - 绝对禁止使用H2O、CH4、C2H4等普通数字格式

2. **化学反应方程式**：
   - 使用标准反应箭头：→（而非->或=>）
   - 完整格式示例：CH₄ + 2O₂ → CO₂ + 2H₂O
   - 可逆反应使用：⇌
   - 条件标注在箭头上方或下方

3. **Markdown结构**：
   - 使用清晰的标题层级（##、###）
   - 重要步骤使用有序列表
   - 关键概念使用**粗体**强调
   - 计算过程使用代码块或表格展示

4. **数学公式**：
   - 复杂计算使用LaTeX格式：$\\Delta H = \\sum H_{{products}} - \\sum H_{{reactants}}$
   - 简单数值计算直接显示：25°C、1.5 mol、98.5%

5. **内容组织**：
   - 问题分析 → 解题思路 → 详细步骤 → 最终答案 → 知识点总结
   - 每个化学现象都要有科学解释
   - 重要的化学原理要单独说明

**综合答案：**
请严格按照上述格式要求输出综合答案，确保所有化学公式都使用正确的下标格式，所有反应箭头都使用标准符号。
"""
        
        return prompt
    
    def _generate_model_comparison(self, parallel_results: Dict[str, Dict[str, Any]]) -> str:
        """
        生成模型对比分析
        
        Args:
            parallel_results: 并行处理结果
            
        Returns:
            str: 模型对比分析报告
        """
        try:
            comparison = "## 📊 模型处理对比分析\n\n"
            
            for model_name, result in parallel_results.items():
                comparison += f"### {model_name.upper()} 模型\n"
                comparison += f"- **处理状态**: {'✅ 成功' if result.get('success', False) else '❌ 失败'}\n"
                comparison += f"- **处理时间**: {result.get('processing_time', 0):.2f}秒\n"
                
                if result.get('success', False):
                    answer_length = len(result.get('answer', ''))
                    comparison += f"- **回答长度**: {answer_length}字符\n"
                    comparison += f"- **回答质量**: {'详细' if answer_length > 500 else '简洁' if answer_length > 100 else '简短'}\n"
                else:
                    comparison += f"- **错误信息**: {result.get('error', 'Unknown error')}\n"
                
                comparison += "\n"
            
            # 添加总体统计
            total_models = len(parallel_results)
            successful_models = len([r for r in parallel_results.values() if r.get('success', False)])
            avg_time = sum(r.get('processing_time', 0) for r in parallel_results.values()) / total_models if total_models > 0 else 0
            
            comparison += f"### 📈 总体统计\n"
            comparison += f"- **成功率**: {successful_models}/{total_models} ({successful_models/total_models*100:.1f}%)\n"
            comparison += f"- **平均处理时间**: {avg_time:.2f}秒\n"
            comparison += f"- **并行处理优势**: 相比串行处理节省约 {max(0, sum(r.get('processing_time', 0) for r in parallel_results.values()) - max(r.get('processing_time', 0) for r in parallel_results.values())):.1f}秒\n"
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"[模型对比] 生成对比分析失败: {str(e)}")
            return "模型对比分析生成失败。"
    
    def process_question_chain(self, question: str) -> Dict[str, str]:
        """
        链式处理化学问题
        
        Args:
            question: 化学问题
            
        Returns:
            Dict[str, str]: 包含各阶段结果的字典
        """
        # 注意：此方法保留用于向后兼容，新架构请使用 process_with_vision
        self.logger.warning("[化学分析链] 使用旧版链式处理方法，建议使用新的并行处理架构")
        
        # 首先进行RAG检索
        if self._rag_chain:
            self.logger.info("[化学分析链] 执行RAG检索...")
            try:
                rag_result = self._rag_chain.invoke(question)
                self.logger.info(f"[化学分析链] RAG结果: {rag_result[:100]}...")
                # 将RAG结果作为问题的一部分，或上下文
                question = f"背景知识: {rag_result}\n\n问题: {question}"
            except Exception as e:
                self.logger.error(f"[化学分析链] RAG检索失败: {str(e)}")
                # 继续处理原问题


        try:
            self.logger.info(f"[化学分析链] 开始链式处理问题: {question[:50]}...")
            self.logger.info(f"[化学分析链] 问题长度: {len(question)}")
            

            
            # 第一步：问题分类
            self.logger.info("[化学分析链] 步骤1: 问题分类")
            classification = self.classify_question(question)
            self.logger.info(f"[化学分析链] 分类结果长度: {len(classification)}")
            
            # 第二步：多角度分析
            self.logger.info("[化学分析链] 步骤2: 多角度分析")
            analysis = self.analyze_question(question, classification)
            self.logger.info(f"[化学分析链] 分析结果长度: {len(analysis)}")
            
            # 第三步：生成解答
            self.logger.info("[化学分析链] 步骤3: 生成解答")
            solution = self.generate_solution(question, classification, analysis)
            self.logger.info(f"[化学分析链] 解答结果长度: {len(solution)}")
            
            result = {
                'question': question,
                'classification': classification,
                'analysis': analysis,
                'solution': solution,
                'chain_summary': self._generate_chain_summary(classification, analysis, solution)
            }
            
            self.logger.info("[化学分析链] 链式处理完成")
            return result
            
        except Exception as e:
            self.logger.error(f"[化学分析链] 链式处理失败: {str(e)}")
            import traceback
            self.logger.error(f"[化学分析链] 异常堆栈: {traceback.format_exc()}")
            return {
                'question': question,
                'error': f"处理失败: {str(e)}",
                'classification': '',
                'analysis': '',
                'solution': '',
                'chain_summary': ''
            }
    
    def classify_question(self, question: str) -> str:
        """
        问题分类方法
        
        Args:
            question: 化学问题
            
        Returns:
            str: 分类结果
        """
        try:
            self.logger.info(f"开始分类问题: {question[:50]}...")
            prompt_text = self.classification_prompt.format(question=question)
            self.logger.debug(f"分类提示文本已生成，长度: {len(prompt_text)}")
            messages = [HumanMessage(content=prompt_text)]
            
            # 选择最佳模型
            model_name = self._select_best_model(['qwen3', 'deepseek-r1', 'wenxin4.5'])
            if not model_name:
                return "分类失败：没有可用的模型"
            
            result = self.llm_manager.call_model(model_name, messages)
            return result if result else "分类失败"
            
        except Exception as e:
            self.logger.error(f"问题分类失败: {str(e)}")
            return f"分类失败: {str(e)}"
    
    def analyze_question(self, question: str, classification: str) -> str:
        """
        多角度分析方法
        
        Args:
            question: 化学问题
            classification: 分类结果
            
        Returns:
            str: 分析结果
        """
        try:
            self.logger.info(f"开始分析问题: {question[:50]}...")
            prompt_text = self.analysis_prompt.format(question=question, classification=classification)
            self.logger.debug(f"分析提示文本已生成，长度: {len(prompt_text)}")
            messages = [HumanMessage(content=prompt_text)]
            
            # 选择最佳模型
            model_name = self._select_best_model(['qwen3', 'deepseek-r1', 'wenxin4.5'])
            if not model_name:
                return "分析失败：没有可用的模型"
            
            result = self.llm_manager.call_model(model_name, messages)
            return result if result else "分析失败"
            
        except Exception as e:
            self.logger.error(f"问题分析失败: {str(e)}")
            return f"分析失败: {str(e)}"
    
    def generate_solution(self, question: str, classification: str, analysis: str) -> str:
        """
        生成解答方法
        
        Args:
            question: 化学问题
            classification: 分类结果
            analysis: 分析结果
            
        Returns:
            str: 解答结果
        """
        try:
            self.logger.info(f"开始生成解答: {question[:50]}...")
            prompt_text = self.solution_prompt.format(
                question=question, 
                classification=classification, 
                analysis=analysis
            )
            self.logger.debug(f"解答提示文本已生成，长度: {len(prompt_text)}")
            messages = [HumanMessage(content=prompt_text)]
            
            # 选择最佳模型
            model_name = self._select_best_model(['qwen3', 'deepseek-r1', 'wenxin4.5'])
            if not model_name:
                return "解答失败：没有可用的模型"
            
            result = self.llm_manager.call_model(model_name, messages)
            return result if result else "解答失败"
            
        except Exception as e:
            self.logger.error(f"生成解答失败: {str(e)}")
            return f"解答失败: {str(e)}"

    def _select_best_model(self, preferred_models: List[str]) -> str:
        """
        选择最佳可用模型
        
        Args:
            preferred_models: 优先模型列表
            
        Returns:
            str: 选中的模型名称
        """
        # 获取可用模型列表
        available_models = self.llm_manager.get_available_models()
        
        # 按优先级选择第一个可用的模型
        for model in preferred_models:
            if model in available_models:
                self.logger.info(f"选择模型: {model}")
                return model
        
        # 如果优先模型都不可用，选择第一个可用模型
        if available_models:
            selected_model = available_models[0]
            self.logger.info(f"使用默认可用模型: {selected_model}")
            return selected_model
        
        # 没有可用模型
        self.logger.error("没有可用的模型")
        return None
    
    def _generate_chain_summary(self, classification: str, analysis: str, solution: str) -> str:
        """
        生成链式处理摘要
        
        Args:
            classification: 分类结果
            analysis: 分析结果
            solution: 解答结果
            
        Returns:
            str: 处理摘要
        """
        # 使用统一的OutputCleaner进行清理
        from utils.output_cleaner import clean_output
        
        classification = clean_output(classification)
        analysis = clean_output(analysis)
        solution = clean_output(solution)
        
        return f"""
### 🔬 化学问题链式分析报告

**📋 问题分类**
{classification}

**🔍 多角度分析**
{analysis}

**✅ 完整解答**
{solution}

---
*本报告由LangChain化学分析链自动生成*
"""
    
    def process_simple(self, question: str = None, image_data: Union[str, bytes] = None) -> str:
        """
        简化接口：返回整合后的答案字符串（兼容旧接口）
        
        Args:
            question: 文本问题
            image_data: 图片数据
            
        Returns:
            str: 整合后的答案
        """
        result = self.process_with_vision(question, image_data)
        
        if isinstance(result, dict):
            if 'error' in result:
                return result['error']
            return result.get('integrated_answer', '处理失败，无法生成答案。')
        else:
            return str(result)
    
    async def process_with_adaptive_retrieval(self, question: str, user_feedback: dict = None) -> Dict[str, Any]:
        """
        使用自适应检索处理问题
        
        Args:
            question (str): 用户问题
            user_feedback (dict): 用户反馈，用于策略调整
        
        Returns:
            Dict[str, Any]: 处理结果，包含答案和检索信息
        """
        try:
            if self.enable_adaptive and self.rag_retriever.enable_adaptive:
                # 使用自适应检索
                retrieval_result = await self.rag_retriever.adaptive_retrieve(question, user_feedback)
                
                # 构建增强的上下文
                context = "\n\n".join(retrieval_result.documents) if retrieval_result.documents else "暂无相关资料"
                
                # 使用并行模型处理
                parallel_results = self._parallel_model_call(question)
                
                # 整合结果
                final_answer = self._integrate_results(parallel_results, question)
                
                return {
                    'answer': final_answer,
                    'retrieval_info': {
                        'strategy_used': retrieval_result.strategy_used,
                        'complexity_analysis': {
                            'complexity': retrieval_result.complexity_analysis.complexity.value,
                            'score': retrieval_result.complexity_analysis.score,
                            'reasoning': retrieval_result.complexity_analysis.reasoning,
                            'recommended_strategy': retrieval_result.complexity_analysis.recommended_strategy
                        },
                        'documents_found': len(retrieval_result.documents),
                        'retrieval_steps': retrieval_result.retrieval_steps,
                        'total_time': retrieval_result.total_time,
                        'confidence_score': retrieval_result.confidence_score
                    },
                    'parallel_results': parallel_results,
                    'context_used': context[:500] + "..." if len(context) > 500 else context
                }
            else:
                # 降级到传统处理
                return await self._process_traditional(question)
                
        except Exception as e:
            self.logger.error(f"自适应检索处理错误: {e}")
            # 降级到传统处理
            return await self._process_traditional(question)
    
    async def _process_traditional(self, question: str) -> Dict[str, Any]:
        """
        传统处理方式（降级处理）
        """
        try:
            # 传统RAG检索
            context_docs = self.rag_retriever.retrieve_comprehensive(question)
            context = "\n\n".join(context_docs) if context_docs else "暂无相关资料"
            
            # 并行模型处理
            parallel_results = self._parallel_model_call(question)
            
            # 整合结果
            final_answer = self._integrate_results(parallel_results, question)
            
            return {
                'answer': final_answer,
                'retrieval_info': {
                    'strategy_used': 'traditional_retrieval',
                    'documents_found': len(context_docs),
                    'note': '使用传统检索模式'
                },
                'parallel_results': parallel_results,
                'context_used': context[:500] + "..." if len(context) > 500 else context
            }
            
        except Exception as e:
            self.logger.error(f"传统处理也失败: {e}")
            return {
                'answer': f"处理过程中出现错误: {str(e)}",
                'retrieval_info': {'strategy_used': 'error', 'error': str(e)},
                'parallel_results': {},
                'context_used': ''
            }
    
    def analyze_query_complexity(self, question: str) -> Dict[str, Any]:
        """
        分析查询复杂度
        
        Args:
            question (str): 用户问题
        
        Returns:
            Dict[str, Any]: 复杂度分析结果
        """
        try:
            complexity_analysis = self.rag_retriever.analyze_query_complexity(question)
            
            return {
                'complexity': complexity_analysis.complexity.value,
                'score': complexity_analysis.score,
                'reasoning': complexity_analysis.reasoning,
                'features': complexity_analysis.features,
                'recommended_strategy': complexity_analysis.recommended_strategy,
                'strategy_description': self.rag_retriever.adaptive_strategy.complexity_analyzer.get_strategy_description(
                    complexity_analysis.recommended_strategy
                ) if self.rag_retriever.adaptive_strategy else "策略描述不可用"
            }
            
        except Exception as e:
            self.logger.error(f"复杂度分析错误: {e}")
            return {
                'complexity': 'moderate',
                'score': 0.5,
                'reasoning': f'分析过程出错: {str(e)}',
                'features': {},
                'recommended_strategy': 'traditional_retrieval',
                'strategy_description': '传统检索'
            }
    
    def get_adaptive_performance_report(self) -> Dict[str, Any]:
        """
        获取自适应检索性能报告
        
        Returns:
            Dict[str, Any]: 性能报告
        """
        return self.rag_retriever.get_adaptive_performance_report()
    
    def get_chain_info(self) -> Dict[str, Any]:
        """
        获取分析链信息
        
        Returns:
            Dict[str, Any]: 链信息
        """
        return {
            'name': '化学分析链 - 并行处理架构',
            'description': '基于LangChain的多模态并行化学问题分析工具',
            'architecture': '多模态输入 → 并行模型调用 → 结果整合',
            'supported_models': self.parallel_models,
            'parallel_models': self.parallel_models,
            'vision_enabled': bool(self.vision_config),
            'rag_enabled': self.rag_retriever is not None,
            'reranker_info': self.rag_retriever.get_reranker_info() if self.rag_retriever else None,
            'adaptive_info': self.rag_retriever.get_adaptive_info() if self.rag_retriever else None,
            'available_llms': list(self.llm_manager.get_available_models().keys()),
            'chain_type': 'parallel_processing_with_adaptive_retrieval' if self.enable_adaptive else 'parallel_processing',
            'supports_multimodal': True,
            'supports_vision': bool(self.vision_config),
            'supports_rag': True,
            'supports_parallel': True,
            'supports_adaptive_retrieval': self.enable_adaptive,
            'features': [
                '多模态输入处理（图片+文字）',
                '并行模型调用（提高速度）',
                '智能结果整合',
                '模型对比分析',
                '视觉识别支持',
                '错误恢复机制',
                '自适应检索策略'
            ],
            'advantages': [
                '并行处理提高响应速度',
                '多模型结果提高准确性',
                '支持图片识别',
                '模块化设计易扩展',
                '自适应检索优化'
            ]
        }