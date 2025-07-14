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
   - 当前支持：qwen3 (通义千问) 和 deepseek-r1
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
    
    def __init__(self):
        """
        初始化化学分析链
        """
        self.logger = logging.getLogger(__name__)
        self.llm_manager = LLMManager()
        self.rag_retriever = RAGRetriever()
        
        # 初始化视觉模型配置
        self.vision_config = MODEL_CONFIG.get('tongyi_vision', {})
        
        # 配置并行处理的模型列表
        self.parallel_models = ['tongyi', 'deepseek']  # qwen3通过tongyi调用，deepseek-r1
        
        # 初始化线程池用于并行处理
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(self.parallel_models))
        
        self._setup_prompts()
        self._setup_chains()
    
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
            processed_question = self._process_multimodal_input(question, image_data)
            if isinstance(processed_question, dict) and 'error' in processed_question:
                return processed_question
            
            self.logger.info(f"[并行处理] 开始处理问题: {processed_question[:100]}...")
            
            # 第二步：并行调用多个模型
            parallel_results = self._parallel_model_call(processed_question)
            
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
            Union[str, Dict]: 处理后的问题文本或错误信息
        """
        try:
            # 处理图片输入
            if image_data:
                self.logger.info("[多模态处理] 检测到图片输入，开始视觉识别...")
                extracted_text = self.extract_text_from_image(image_data)
                
                if "识别失败" in extracted_text or "处理出错" in extracted_text:
                    return {'error': extracted_text}
                
                # 图片+文字组合
                if question and question.strip():
                    combined_question = f"图片内容：\n{extracted_text}\n\n补充问题：{question}"
                else:
                    combined_question = f"请分析以下化学问题：\n{extracted_text}"
                    
                self.logger.info(f"[多模态处理] 图片识别完成，内容长度: {len(extracted_text)}")
                return combined_question
            else:
                # 纯文字输入
                if not question or not question.strip():
                    return {'error': "请提供问题文本或上传图片。"}
                return question.strip()
                
        except Exception as e:
            self.logger.error(f"[多模态处理] 输入处理失败: {str(e)}")
            return {'error': f"输入处理失败: {str(e)}"}

    def _parallel_model_call(self, question: str) -> Dict[str, Dict[str, Any]]:
        """
        并行调用多个模型进行问题处理
        
        Args:
            question: 处理后的问题文本
            
        Returns:
            Dict[str, Dict]: 各模型的处理结果
        """
        self.logger.info(f"[并行调用] 开始并行调用 {len(self.parallel_models)} 个模型")
        
        # 为每个模型创建处理任务
        future_to_model = {}
        results = {}
        
        for model_name in self.parallel_models:
            if self.llm_manager.is_model_available(model_name):
                try:
                    future = self.executor.submit(self._single_model_process, model_name, question)
                    future_to_model[future] = model_name
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
            for future in concurrent.futures.as_completed(future_to_model, timeout=120):  # 2分钟超时
                model_name = future_to_model[future]
                try:
                    result = future.result(timeout=30)  # 单个任务30秒超时
                    results[model_name] = result
                    self.logger.info(f"[并行调用] 模型 {model_name} 处理完成")
                except concurrent.futures.TimeoutError:
                    self.logger.error(f"[并行调用] 模型 {model_name} 处理超时")
                    results[model_name] = {
                        'error': f"模型 {model_name} 处理超时",
                        'answer': '',
                        'processing_time': 30,
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
                    results[model_name] = {
                        'error': f"模型 {model_name} 整体超时未完成",
                        'answer': '',
                        'processing_time': 120,
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
    
    def _single_model_process(self, model_name: str, question: str) -> Dict[str, Any]:
        """
        单个模型的处理逻辑
        
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
            
            # 构建专门的化学问题处理提示
            prompt = f"""
你是一个专业的化学助手，请详细分析并回答以下化学问题。

问题：{question}

请提供：
1. 问题分析和解题思路
2. 详细的解答步骤
3. 相关的化学原理和公式（使用LaTeX格式）
4. 最终答案
5. 解题要点总结

请确保回答准确、完整、易懂。
"""
            
            messages = [HumanMessage(content=prompt)]
            response = self.llm_manager.call_model(model_name, messages, temperature=0.3)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"[{model_name}] 处理完成，耗时: {processing_time:.2f}秒")
            
            return {
                'answer': response,
                'processing_time': processing_time,
                'model_name': model_name,
                'success': True
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"[{model_name}] 处理失败: {str(e)}")
            return {
                'error': f"模型 {model_name} 处理失败: {str(e)}",
                'answer': '',
                'processing_time': processing_time,
                'model_name': model_name,
                'success': False
            }
    
    def _integrate_results(self, parallel_results: Dict[str, Dict[str, Any]], question: str) -> str:
        """
        整合多个模型的结果
        
        Args:
            parallel_results: 并行处理结果
            question: 原始问题
            
        Returns:
            str: 整合后的最终答案
        """
        try:
            # 过滤出成功的结果
            successful_results = {k: v for k, v in parallel_results.items() 
                                if v.get('success', False) and v.get('answer', '').strip()}
            
            if not successful_results:
                return "所有模型处理失败，无法生成答案。"
            
            if len(successful_results) == 1:
                # 只有一个成功结果，直接返回
                model_name, result = list(successful_results.items())[0]
                return f"**{model_name} 模型回答：**\n\n{result['answer']}"
            
            # 多个结果需要整合
            self.logger.info(f"[结果整合] 开始整合 {len(successful_results)} 个模型的结果")
            
            # 构建整合提示
            integration_prompt = f"""
你是一个化学专家，现在需要整合多个AI模型对同一化学问题的回答，生成一个最优的综合答案。

原始问题：{question}

各模型回答：
"""
            
            for model_name, result in successful_results.items():
                integration_prompt += f"\n**{model_name} 模型回答：**\n{result['answer']}\n\n---\n"
            
            integration_prompt += """
请基于以上多个模型的回答，生成一个综合的、最优的答案。要求：
1. 整合各模型的优点，去除重复内容
2. 确保科学准确性
3. 保持逻辑清晰和结构完整
4. 如果模型间有分歧，请指出并给出最合理的解释
5. 使用LaTeX格式表示化学公式

综合答案：
"""
            
            # 使用最佳可用模型进行整合
            integration_model = self._select_best_model(['tongyi', 'deepseek', 'zhipu'])
            if integration_model:
                messages = [HumanMessage(content=integration_prompt)]
                integrated_answer = self.llm_manager.call_model(integration_model, messages, temperature=0.2)
                self.logger.info(f"[结果整合] 使用 {integration_model} 完成结果整合")
                # 使用统一的OutputCleaner进行清理
                from utils.output_cleaner import clean_model_output
                return clean_model_output(integrated_answer)
            else:
                # 如果无法整合，返回第一个结果
                first_model, first_result = list(successful_results.items())[0]
                from utils.output_cleaner import clean_output
                return clean_output(f"**{first_model} 模型回答：**\n\n{first_result['answer']}")
                
        except Exception as e:
            self.logger.error(f"[结果整合] 整合失败: {str(e)}")
            # 返回第一个可用结果
            if parallel_results:
                for model_name, result in parallel_results.items():
                    if result.get('answer', '').strip():
                        from utils.output_cleaner import clean_output
                        return clean_output(f"**{model_name} 模型回答：**\n\n{result['answer']}")
            return "结果整合失败，无法生成答案。"
    
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
            'features': [
                '多模态输入处理（图片+文字）',
                '并行模型调用（提高速度）',
                '智能结果整合',
                '模型对比分析',
                '视觉识别支持',
                '错误恢复机制'
            ],
            'advantages': [
                '并行处理提高响应速度',
                '多模型结果提高准确性',
                '支持图片识别',
                '模块化设计易扩展'
            ]
        }