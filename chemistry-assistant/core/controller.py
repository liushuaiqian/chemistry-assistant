#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主控制器
负责Agent路由分发逻辑
"""

from .agent_manager import AgentManager
from .task_router import TaskRouter
from .multimodal_processor import MultimodalProcessor
from .llm_manager import LLMManager
from .chemistry_chain import ChemistryAnalysisChain
from tools.knowledge_api import KnowledgeAPI

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
            
            # 初始化Agent管理器（暂时跳过知识库相关功能）
            self.logger.info("初始化Agent管理器...")
            try:
                self.agent_manager = AgentManager()
                self.logger.info("Agent管理器初始化成功")
            except Exception as e:
                self.logger.warning(f"Agent管理器初始化失败，将使用简化模式: {e}")
                self.agent_manager = None
            
            # 初始化任务路由器
            self.logger.info("初始化任务路由器...")
            try:
                self.task_router = TaskRouter()
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