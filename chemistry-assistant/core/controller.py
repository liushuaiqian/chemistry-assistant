#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主控制器
负责Agent路由分发逻辑
"""

from .agent_manager import AgentManager
from .task_router import TaskRouter
from .multimodal_processor import MultimodalProcessor

class Controller:
    """
    主控制器类
    负责接收用户查询并协调各个Agent的工作
    """
    
    def __init__(self):
        """
        初始化控制器
        """
        self.agent_manager = AgentManager()
        self.task_router = TaskRouter()
        self.multimodal_processor = MultimodalProcessor()
        
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
            import base64
            from io import BytesIO
            
            image_pil = task_info['image']
            # 将PIL图像转换为bytes
            buffered = BytesIO()
            image_pil.save(buffered, format="JPEG")
            # 将bytes转换为base64字符串
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # 调用多模态处理器处理图像和文本
            # 注意：这里我们假设multimodal_processor有一个可以处理base64图像和文本的方法
            # 我们将在下一步中创建这个方法
            return self.multimodal_processor.process_image_and_text(img_str, query)
        else:
            # 对于纯文本输入，也使用多模态处理器
            return self.multimodal_processor.process_input(query, 'text')
    
    def get_available_agents(self):
        """
        获取所有可用的Agent列表
        
        Returns:
            list: Agent名称列表
        """
        return self.agent_manager.get_available_agents()
    
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