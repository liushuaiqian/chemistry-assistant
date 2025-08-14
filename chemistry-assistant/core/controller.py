#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主控制器
负责Agent路由分发逻辑
"""

# from .agent_manager import AgentManager  # 临时禁用
# from .task_router import TaskRouter  # 临时禁用
from .multimodal_processor import MultimodalProcessor
from .llm_manager import LLMManager
from .chemistry_chain import ChemistryAnalysisChain
from tools.knowledge_api import KnowledgeAPI
from agents.tools_agent import ToolsAgent

class Controller:
    """
    主控制器类
    负责接收用户查询并协调各个Agent的工作
    """
    
    def __init__(self, use_reranker=True, enable_adaptive=True):
        """
        初始化控制器
        
        Args:
            use_reranker (bool): 是否启用文本排序器进行双阶段检索
            enable_adaptive (bool): 是否启用自适应检索
        """
        import logging
        self.logger = logging.getLogger(__name__)
        self.use_reranker = use_reranker
        self.enable_adaptive = enable_adaptive
        
        try:
            self.logger.info("开始初始化Controller组件...")
            
            # 初始化LLM管理器（优先级最高）
            self.logger.info("初始化LLM管理器...")
            self.llm_manager = LLMManager()
            self.logger.info("LLM管理器初始化成功")
            
            # 初始化化学分析链，支持双阶段检索和自适应检索
            self.logger.info("初始化化学分析链...")
            self.chemistry_chain = ChemistryAnalysisChain(use_reranker=use_reranker, enable_adaptive=enable_adaptive)
            self.logger.info("化学分析链初始化成功")
            
            # 初始化多模态处理器
            self.logger.info("初始化多模态处理器...")
            self.multimodal_processor = MultimodalProcessor()
            self.logger.info("多模态处理器初始化成功")
            
            # 初始化知识库API
            self.logger.info("初始化知识库API...")
            self.knowledge_api = KnowledgeAPI()
            self.logger.info("知识库API初始化成功")
            
            # 初始化化学工具Agent（用于程序化化学计算）
            self.logger.info("初始化化学工具Agent...")
            self.tools_agent = ToolsAgent()
            self.logger.info("化学工具Agent初始化成功")
            
            # 初始化Agent管理器（暂时跳过知识库相关功能）
            self.logger.info("初始化Agent管理器...")
            try:
                # self.agent_manager = AgentManager()  # 临时禁用
                self.logger.info("Agent管理器初始化成功")
            except Exception as e:
                self.logger.warning(f"Agent管理器初始化失败，将使用简化模式: {e}")
                self.agent_manager = None
            
            # 初始化任务路由器
            self.logger.info("初始化任务路由器...")
            try:
                # self.task_router = TaskRouter()  # 临时禁用
                self.logger.info("任务路由器初始化成功")
            except Exception as e:
                self.logger.warning(f"任务路由器初始化失败，将使用简化模式: {e}")
                self.task_router = None
            
            self.logger.info("Controller初始化完成")
            
        except Exception as e:
            self.logger.error(f"Controller初始化失败: {e}")
            raise e
        
    def process_query(self, query, task_info=None):
        """
        处理用户查询
        
        Args:
            query (str): 用户输入的查询文本
            task_info (dict, optional): 任务相关信息，如首选模型等
            
        Returns:
            str: 处理后的回复
        """
        # 初始化任务信息
        if task_info is None:
            task_info = {}
        
        # 针对“化学计算”功能，优先走程序化工具链（即使存在图像输入）
        try:
            function_choice = task_info.get('function', '')
        except Exception:
            function_choice = ''
        
        if function_choice == "化学计算":
            # 仅当文本为空且存在图像时，退回到多模态识别
            if (not query or not str(query).strip()) and task_info.get('image') is not None:
                try:
                    import base64
                    from io import BytesIO
                    from PIL import Image

                    image_pil = task_info['image']
                    if not isinstance(image_pil, Image.Image):
                        return "图像格式不支持，请上传有效的图片文件。", ""
                    buffered = BytesIO()
                    if image_pil.mode != 'RGB':
                        image_pil = image_pil.convert('RGB')
                    image_pil.save(buffered, format="JPEG", quality=85)
                    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    response = self.multimodal_processor.process_image_and_text(img_str, "请识别图像中的化学内容并提取关键信息")
                    return response, "已通过视觉模块识别图像，但化学计算建议提供明确的文本描述以获得更准确结果"
                except Exception as e:
                    self.logger.error(f"化学计算图像识别失败: {e}")
                    return f"图像处理失败: {str(e)}", ""
            
            # 使用化学工具Agent处理文本化学计算
            try:
                result = self.tools_agent.process(query, task_info)
                return result, "化学计算由程序化工具完成"
            except Exception as e:
                self.logger.error(f"化学计算处理失败: {e}")
                return f"化学计算处理失败: {str(e)}", ""
        
        # 非“化学计算”则保持原有逻辑
        
        # 检查任务信息中是否包含图像
        if task_info and 'image' in task_info and task_info['image'] is not None:
            try:
                import base64
                from io import BytesIO
                from PIL import Image
                
                image_pil = task_info['image']
                self.logger.info(f"处理图像输入，图像类型: {type(image_pil)}")
                
                # 确保是PIL图像对象
                if not isinstance(image_pil, Image.Image):
                    self.logger.error(f"图像类型不正确: {type(image_pil)}")
                    return "图像格式不支持，请上传有效的图片文件。", ""
                
                # 将PIL图像转换为bytes
                buffered = BytesIO()
                # 确保图像格式为RGB
                if image_pil.mode != 'RGB':
                    image_pil = image_pil.convert('RGB')
                image_pil.save(buffered, format="JPEG", quality=85)
                # 将bytes转换为base64字符串
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                self.logger.info(f"图像转换成功，base64长度: {len(img_str)}")
                
                # 调用多模态处理器处理图像和文本
                response = self.multimodal_processor.process_image_and_text(img_str, query)
                return response, "图像识别和分析完成"
                
            except Exception as e:
                self.logger.error(f"图像处理失败: {e}")
                return f"图像处理失败: {str(e)}", ""
        else:
            # 对于纯文本输入，也使用多模态处理器
            response, comparison = self.multimodal_processor.process_input(query, 'text')
            return response, comparison
    
    async def process_with_adaptive_retrieval(self, question: str, user_feedback: dict = None) -> dict:
        """
        使用自适应检索处理问题
        
        Args:
            question (str): 用户问题
            user_feedback (dict): 用户反馈，用于策略调整
        
        Returns:
            dict: 处理结果
        """
        try:
            self.logger.info(f"开始自适应检索处理: {question[:50]}...")
            
            if self.enable_adaptive:
                result = await self.chemistry_chain.process_with_adaptive_retrieval(question, user_feedback)
                
                self.logger.info(f"自适应检索完成，策略: {result.get('retrieval_info', {}).get('strategy_used', 'unknown')}")
                return {
                    'success': True,
                    'answer': result['answer'],
                    'retrieval_info': result['retrieval_info'],
                    'processing_info': {
                        'method': 'adaptive_retrieval',
                        'parallel_models_used': list(result.get('parallel_results', {}).keys()),
                        'context_length': len(result.get('context_used', ''))
                    }
                }
            else:
                # 降级到传统处理
                self.logger.info("自适应检索未启用，使用传统处理")
                result = self.process_query(question)
                return {
                    'success': True,
                    'answer': result[0] if isinstance(result, tuple) else result,
                    'retrieval_info': {'strategy_used': 'traditional', 'note': '自适应检索未启用'},
                    'processing_info': {'method': 'traditional'}
                }
                
        except Exception as e:
            self.logger.error(f"自适应检索处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'answer': f"处理过程中出现错误: {str(e)}",
                'retrieval_info': {'strategy_used': 'error'},
                'processing_info': {'method': 'error_fallback'}
            }
    
    def analyze_query_complexity(self, question: str) -> dict:
        """
        分析查询复杂度
        
        Args:
            question (str): 用户问题
        
        Returns:
            dict: 复杂度分析结果
        """
        try:
            self.logger.info(f"分析查询复杂度: {question[:50]}...")
            
            if self.enable_adaptive:
                analysis = self.chemistry_chain.analyze_query_complexity(question)
                self.logger.info(f"复杂度分析完成: {analysis.get('complexity', 'unknown')}")
                return {
                    'success': True,
                    'analysis': analysis
                }
            else:
                return {
                    'success': False,
                    'message': '自适应检索功能未启用',
                    'analysis': {
                        'complexity': 'unknown',
                        'score': 0.5,
                        'reasoning': '自适应检索功能未启用',
                        'recommended_strategy': 'traditional_retrieval'
                    }
                }
                
        except Exception as e:
            self.logger.error(f"复杂度分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': {
                    'complexity': 'error',
                    'score': 0.0,
                    'reasoning': f'分析过程出错: {str(e)}',
                    'recommended_strategy': 'fallback'
                }
            }
    
    def get_adaptive_performance_report(self) -> dict:
        """
        获取自适应检索性能报告
        
        Returns:
            dict: 性能报告
        """
        try:
            if self.enable_adaptive:
                report = self.chemistry_chain.get_adaptive_performance_report()
                return {
                    'success': True,
                    'report': report
                }
            else:
                return {
                    'success': False,
                    'message': '自适应检索功能未启用',
                    'report': {}
                }
                
        except Exception as e:
            self.logger.error(f"获取性能报告失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'report': {}
            }
    
    def get_system_info(self) -> dict:
        """
        获取系统信息
        
        Returns:
            dict: 系统配置和状态信息
        """
        try:
            return {
                'controller_status': 'active',
                'llm_manager': self.llm_manager.get_manager_info() if hasattr(self.llm_manager, 'get_manager_info') else 'available',
                'chemistry_chain': self.chemistry_chain.get_chain_info() if hasattr(self.chemistry_chain, 'get_chain_info') else 'available',
                'reranker_enabled': self.use_reranker,
                'adaptive_enabled': self.enable_adaptive,
                'available_functions': [
                    'process_query',
                    'process_with_chain', 
                    'process_multimodal_input',
                    'process_with_adaptive_retrieval',
                    'analyze_query_complexity',
                    'get_adaptive_performance_report',
                    'get_system_info'
                ],
                'supported_features': [
                    '多模型并行处理',
                    '视觉识别',
                    'RAG检索',
                    '双阶段检索' if self.use_reranker else '传统检索',
                    '自适应检索' if self.enable_adaptive else '固定策略检索',
                    '查询复杂度分析' if self.enable_adaptive else '基础查询处理',
                    '化学计算',
                    '错误恢复'
                ]
            }
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {
                'controller_status': 'error',
                'error': str(e),
                'available_functions': [],
                'supported_features': []
            }
    
    def get_available_agents(self):
        """
        获取所有可用的Agent列表
        
        Returns:
            list: Agent名称列表
        """
        if self.agent_manager:
            return self.agent_manager.get_available_agents()
        else:
            return ["LLM模型", "化学分析链"]  # 简化模式下的可用选项
    
    def process_multimodal_input(self, input_data, input_type='auto'):
        """
        处理多模态输入（图像或文字）
        
        Args:
            input_data: 输入数据（文字字符串或图像字节数据）
            input_type: 输入类型 ('text', 'image', 'auto')
            
        Returns:
            str: 处理后的回复
        """
        return self.multimodal_processor.process_input(input_data, input_type)
    
    def process_with_chain(self, query, function_type="智能问答", image_data=None):
        """
        使用LangChain链式处理查询
        
        Args:
            query (str): 用户查询
            function_type (str): 功能类型
            image_data: 图像数据（PIL Image对象）
            
        Returns:
            tuple: (回复, 对比分析, 链式分析结果)
        """
        self.logger.info(f"[LangChain处理] 开始处理查询: {query[:50]}...")
        self.logger.info(f"[LangChain处理] 功能类型: {function_type}")
        self.logger.info(f"[LangChain处理] 是否包含图像: {image_data is not None}")
        
        if function_type == "信息检索":
            self.logger.info("[LangChain处理] 执行信息检索...")
            try:
                result = self.chemistry_chain.invoke_rag_chain(query)
                # 对于RAG，我们直接返回结果，不进行后续的链式分析
                return result, "", {}
            except Exception as e:
                self.logger.error(f"[LangChain处理] 信息检索失败: {e}")
                return f"信息检索失败: {str(e)}", "", {}

        if function_type == "智能问答":
            try:
                # 准备图像数据
                image_base64 = None
                if image_data is not None:
                    self.logger.info("[LangChain处理] 检测到图像输入，开始图像转换...")
                    try:
                        import base64
                        from io import BytesIO
                        from PIL import Image
                        
                        # 确保是PIL图像对象
                        if not isinstance(image_data, Image.Image):
                            self.logger.error(f"[LangChain处理] 图像类型不正确: {type(image_data)}")
                            return "图像格式不支持，请上传有效的图片文件。", "", {}
                        
                        # 将PIL图像转换为base64
                        buffered = BytesIO()
                        if image_data.mode != 'RGB':
                            image_data = image_data.convert('RGB')
                        image_data.save(buffered, format="JPEG", quality=85)
                        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
                        self.logger.info(f"[LangChain处理] 图像转换成功，base64长度: {len(image_base64)}")
                        
                    except Exception as e:
                        self.logger.error(f"[LangChain处理] 图像处理失败: {str(e)}")
                        return f"图像处理失败: {str(e)}", "", {}
                
                # 使用化学分析链的新方法进行处理
                self.logger.info("[LangChain处理] 开始调用化学分析链的process_with_vision方法...")
                result = self.chemistry_chain.process_with_vision(
                    question=query,
                    image_data=image_base64,
                    function_type=function_type
                )
                self.logger.info("[LangChain处理] 化学分析链处理完成")
                
                return result, "", {"solution": result}
                
            except Exception as e:
                self.logger.error(f"[LangChain处理] 处理过程中发生异常: {str(e)}")
                import traceback
                self.logger.error(f"[LangChain处理] 异常堆栈: {traceback.format_exc()}")
                return f"处理过程中发生异常: {str(e)}", "", {}
    
    def search_external_knowledge(self, query: str) -> dict:
        """
        搜索外部知识库
        
        Args:
            query (str): 搜索查询
            
        Returns:
            dict: 搜索结果
        """
        try:
            self.logger.info(f"开始搜索外部知识库: {query[:50]}...")
            
            # 使用Metaso知识库搜索
            result = self.knowledge_api.search_knowledge_base(query)
            
            if result.get('success'):
                self.logger.info(f"外部知识库搜索成功，获得答案长度: {len(result.get('answer', ''))}")
                return {
                    'success': True,
                    'source': 'metaso_knowledge_base',
                    'answer': result.get('answer', ''),
                    'references': result.get('references', []),
                    'result_id': result.get('result_id', ''),
                    'session_id': result.get('session_id', ''),
                    'balance': result.get('balance', 0)
                }
            else:
                self.logger.warning(f"外部知识库搜索失败: {result.get('error', '未知错误')}")
                return {
                    'success': False,
                    'source': 'metaso_knowledge_base',
                    'error': result.get('error', '未知错误'),
                    'answer': '',
                    'references': []
                }
                
        except Exception as e:
            self.logger.error(f"外部知识库搜索异常: {str(e)}")
            return {
                'success': False,
                'source': 'metaso_knowledge_base',
                'error': f'搜索异常: {str(e)}',
                'answer': '',
                'references': []
            }
    
    def get_comprehensive_knowledge(self, query: str) -> dict:
        """
        获取综合知识信息，结合多个知识源
        
        Args:
            query (str): 查询内容
            
        Returns:
            dict: 综合知识结果
        """
        try:
            self.logger.info(f"开始获取综合知识信息: {query[:50]}...")
            
            # 使用知识API获取综合信息
            result = self.knowledge_api.get_comprehensive_info(query)
            
            # 格式化返回结果
            formatted_result = {
                'success': True,
                'query': query,
                'combined_answer': result.get('combined_answer', ''),
                'sources': []
            }
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"获取综合知识异常: {str(e)}")
            return {
                'success': False,
                'error': f'知识获取异常: {str(e)}',
                'combined_answer': '抱歉，知识获取过程中发生错误，请稍后重试。',
                'sources': []
            }
    
    def process_comprehensive_retrieval(self, query: str, enable_local_rag=True, enable_metaso=True, enable_tongyi=True, enable_pubchem=True) -> dict:
        """
        处理综合检索请求，并行调用多个知识库
        
        Args:
            query (str): 用户查询
            enable_local_rag (bool): 是否启用本地RAG知识库
            enable_metaso (bool): 是否启用Metaso API
            enable_tongyi (bool): 是否启用通义千问智能体
            enable_pubchem (bool): 是否启用PubChem数据库
            
        Returns:
            dict: 综合检索结果
        """
        try:
            self.logger.info(f"开始综合检索: {query[:50]}...")
            
            # 使用化学分析链的RAG检索器进行综合检索
            if hasattr(self.chemistry_chain, 'rag_retriever'):
                result = self.chemistry_chain.rag_retriever.retrieve_with_external_knowledge(
                    query=query,
                    k=5,
                    include_tongyi=enable_tongyi,
                    include_metaso=enable_metaso,
                    include_pubchem=enable_pubchem
                )
                
                # 如果不启用本地RAG，移除本地文档结果
                if not enable_local_rag:
                    result['local_documents'] = []
                    if 'combined_answer' in result:
                        # 移除本地知识库部分
                        combined_answer = result['combined_answer']
                        if '### 本地知识库检索结果:' in combined_answer:
                            parts = combined_answer.split('### 本地知识库检索结果:')
                            if len(parts) > 1:
                                # 保留第一部分（如果有）和外部知识库部分
                                external_part = parts[1].split('### ')[1:] if '### ' in parts[1] else []
                                if external_part:
                                    result['combined_answer'] = '### ' + '### '.join(external_part)
                                else:
                                    result['combined_answer'] = parts[0] if parts[0].strip() else ''
                
                # 更新成功状态和来源信息
                result['success'] = True
                
                # 构建详细的回答
                if result.get('combined_answer'):
                    # 使用LLM整合所有检索结果
                    integrated_answer = self._integrate_retrieval_results(query, result)
                    result['combined_answer'] = integrated_answer
                
                self.logger.info(f"综合检索完成，使用了{len(result.get('sources', []))}个知识源")
                return result
            else:
                self.logger.warning("RAG检索器不可用，使用简化模式")
                return {
                    'success': False,
                    'error': 'RAG检索器不可用',
                    'combined_answer': '抱歉，检索系统暂时不可用，请稍后重试。',
                    'sources': []
                }
                
        except Exception as e:
            self.logger.error(f"综合检索异常: {str(e)}")
            return {
                'success': False,
                'error': f'检索异常: {str(e)}',
                'combined_answer': '抱歉，检索过程中发生错误，请稍后重试。',
                'sources': []
            }
    
    def _integrate_retrieval_results(self, query: str, retrieval_result: dict) -> str:
        """
        使用LLM整合多个知识源的检索结果
        
        Args:
            query (str): 原始查询
            retrieval_result (dict): 检索结果
            
        Returns:
            str: 整合后的回答
        """
        try:
            # 构建整合提示
            integration_prompt = f"""请基于以下多个知识源的信息，为用户问题提供一个综合、准确的回答。

用户问题：{query}

检索到的信息：
{retrieval_result.get('combined_answer', '')}

请要求：
1. 综合所有相关信息，提供准确、完整的回答
2. 如果不同知识源有冲突信息，请指出并说明
3. 保持回答的逻辑性和可读性
4. 如果信息不足，请诚实说明

请提供综合回答："""
            
            # 使用LLM管理器生成整合回答
            if hasattr(self, 'llm_manager') and self.llm_manager:
                # 构建消息列表
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=integration_prompt)]
                
                # 选择可用的模型进行整合
                available_models = self.llm_manager.get_available_models()
                preferred_models = ['qwen', 'tongyi', 'zhipu', 'openai']
                
                selected_model = None
                for model in preferred_models:
                    if model in available_models:
                        selected_model = model
                        break
                
                if selected_model:
                    integrated_response = self.llm_manager.call_model(
                        selected_model,
                        messages,
                        temperature=0.3
                    )
                    return integrated_response
                else:
                    self.logger.warning("没有可用的LLM模型进行结果整合")
                    return retrieval_result.get('combined_answer', '未能获取到有效信息')
            else:
                # 如果LLM不可用，返回原始结果
                return retrieval_result.get('combined_answer', '未能获取到有效信息')
                
        except Exception as e:
            self.logger.error(f"结果整合异常: {str(e)}")
            return retrieval_result.get('combined_answer', '信息整合失败，但检索到了相关内容。')
            
            # 添加Metaso知识库结果
            metaso_result = result.get('metaso_result')
            if metaso_result and metaso_result.get('success'):
                formatted_result['sources'].append({
                    'name': 'Metaso知识库',
                    'answer': metaso_result.get('answer', ''),
                    'references': metaso_result.get('references', []),
                    'result_id': metaso_result.get('result_id', ''),
                    'balance': metaso_result.get('balance', 0)
                })
            
            # 添加PubChem结果
            pubchem_result = result.get('pubchem_result')
            if pubchem_result and 'error' not in pubchem_result:
                formatted_result['sources'].append({
                    'name': 'PubChem数据库',
                    'compound_info': pubchem_result
                })
            
            self.logger.info(f"综合知识信息获取成功，包含{len(formatted_result['sources'])}个知识源")
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"获取综合知识信息异常: {str(e)}")
            return {
                'success': False,
                'query': query,
                'error': f'获取信息异常: {str(e)}',
                'combined_answer': '',
                'sources': []
            }
        else:
            # 使用传统多模态处理器
            self.logger.info("[LangChain处理] 使用传统多模态处理器")
            response, comparison = self.multimodal_processor.process_input(query, 'text')
            return response, comparison, {}