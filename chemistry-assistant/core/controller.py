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

class Controller:
    """
    主控制器类
    负责接收用户查询并协调各个Agent的工作
    """
    
    def __init__(self):
        """
        初始化控制器
        """
        import logging
        self.logger = logging.getLogger(__name__)
        
        try:
            self.logger.info("开始初始化Controller组件...")
            
            # 初始化LLM管理器（优先级最高）
            self.logger.info("初始化LLM管理器...")
            self.llm_manager = LLMManager()
            self.logger.info("LLM管理器初始化成功")
            
            # 初始化化学分析链
            self.logger.info("初始化化学分析链...")
            self.chemistry_chain = ChemistryAnalysisChain()
            self.logger.info("化学分析链初始化成功")
            
            # 初始化多模态处理器
            self.logger.info("初始化多模态处理器...")
            self.multimodal_processor = MultimodalProcessor()
            self.logger.info("多模态处理器初始化成功")
            
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
            use_chain (bool): 是否使用链式处理
            image_data: 图像数据（PIL Image对象）
            
        Returns:
            tuple: (回复, 对比分析, 链式分析结果)
        """
        self.logger.info(f"[LangChain处理] 开始处理查询: {query[:50]}...")
        self.logger.info(f"[LangChain处理] 使用链式处理: {use_chain}")
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
                # 如果有图像，先进行图像识别
                processed_query = query
                if image_data is not None:
                    self.logger.info("[LangChain处理] 检测到图像输入，开始图像识别...")
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
                        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
                        self.logger.info(f"[LangChain处理] 图像转换成功，base64长度: {len(img_str)}")
                        
                        # 使用多模态处理器提取图像文本
                        extracted_text = self.multimodal_processor._extract_text_from_image(img_str)
                        self.logger.info(f"[LangChain处理] 图像文本提取完成: {extracted_text[:100]}...")
                        
                        # 组合查询
                        if query.strip():
                            processed_query = f"图像内容：{extracted_text}\n\n用户问题：{query}"
                        else:
                            processed_query = f"请分析以下图像内容：{extracted_text}"
                        
                        self.logger.info(f"[LangChain处理] 组合查询完成，长度: {len(processed_query)}")
                        
                    except Exception as e:
                        self.logger.error(f"[LangChain处理] 图像处理失败: {str(e)}")
                        return f"图像处理失败: {str(e)}", "", {}
                
                # 使用化学分析链进行处理
                self.logger.info("[LangChain处理] 开始调用化学分析链...")
                chain_result = self.chemistry_chain.process_question_chain(processed_query)
                self.logger.info("[LangChain处理] 化学分析链处理完成")
                
                if 'error' in chain_result:
                    self.logger.error(f"[LangChain处理] 链式处理出错: {chain_result['error']}")
                    return chain_result['error'], "", chain_result
                
                return chain_result.get('solution', '处理完成但无解答'), "", chain_result
                
            except Exception as e:
                self.logger.error(f"[LangChain处理] 处理过程中发生异常: {str(e)}")
                import traceback
                self.logger.error(f"[LangChain处理] 异常堆栈: {traceback.format_exc()}")
                return f"LangChain处理失败: {str(e)}", "", {}
        else:
            # 使用传统多模态处理器
            self.logger.info("[LangChain处理] 使用传统多模态处理器")
            response, comparison = self.multimodal_processor.process_input(query, 'text')
            return response, comparison, {}