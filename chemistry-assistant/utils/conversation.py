#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
对话管理模块
提供对话历史管理功能
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .logger import get_logger
from .helpers import ensure_dir, generate_id, save_json, load_json

# 获取日志记录器
logger = get_logger('conversation')

class Message:
    """
    消息类
    表示对话中的一条消息
    """
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        """
        初始化消息
        
        Args:
            role (str): 角色（'user' 或 'assistant'）
            content (str): 消息内容
            timestamp (str, optional): 时间戳
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        从字典创建消息
        
        Args:
            data (Dict[str, Any]): 字典数据
            
        Returns:
            Message: 消息对象
        """
        return cls(
            role=data.get('role', ''),
            content=data.get('content', ''),
            timestamp=data.get('timestamp')
        )

class Conversation:
    """
    对话类
    管理对话历史
    """
    
    def __init__(self, conversation_id: Optional[str] = None, title: Optional[str] = None):
        """
        初始化对话
        
        Args:
            conversation_id (str, optional): 对话ID
            title (str, optional): 对话标题
        """
        self.conversation_id = conversation_id or generate_id()
        self.title = title or f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.messages: List[Message] = []
        self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.updated_at = self.created_at
    
    def add_message(self, role: str, content: str) -> Message:
        """
        添加消息
        
        Args:
            role (str): 角色（'user' 或 'assistant'）
            content (str): 消息内容
            
        Returns:
            Message: 添加的消息
        """
        message = Message(role, content)
        self.messages.append(message)
        self.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return message
    
    def get_messages(self) -> List[Message]:
        """
        获取所有消息
        
        Returns:
            List[Message]: 消息列表
        """
        return self.messages
    
    def get_last_message(self) -> Optional[Message]:
        """
        获取最后一条消息
        
        Returns:
            Optional[Message]: 最后一条消息，如果没有则返回None
        """
        if self.messages:
            return self.messages[-1]
        return None
    
    def clear(self) -> None:
        """
        清空对话历史
        """
        self.messages = []
        self.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'conversation_id': self.conversation_id,
            'title': self.title,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        从字典创建对话
        
        Args:
            data (Dict[str, Any]): 字典数据
            
        Returns:
            Conversation: 对话对象
        """
        conversation = cls(
            conversation_id=data.get('conversation_id'),
            title=data.get('title')
        )
        conversation.created_at = data.get('created_at', conversation.created_at)
        conversation.updated_at = data.get('updated_at', conversation.updated_at)
        
        # 加载消息
        messages_data = data.get('messages', [])
        conversation.messages = [Message.from_dict(msg_data) for msg_data in messages_data]
        
        return conversation

class ConversationManager:
    """
    对话管理器
    管理多个对话
    """
    
    def __init__(self, storage_dir: str):
        """
        初始化对话管理器
        
        Args:
            storage_dir (str): 存储目录
        """
        self.storage_dir = storage_dir
        ensure_dir(storage_dir)
        self.conversations: Dict[str, Conversation] = {}
        self.current_conversation_id: Optional[str] = None
        logger.info(f"初始化对话管理器，存储目录: {storage_dir}")
    
    def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """
        创建新对话
        
        Args:
            title (str, optional): 对话标题
            
        Returns:
            Conversation: 创建的对话
        """
        conversation = Conversation(title=title)
        self.conversations[conversation.conversation_id] = conversation
        self.current_conversation_id = conversation.conversation_id
        logger.info(f"创建新对话: {conversation.conversation_id}")
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        获取对话
        
        Args:
            conversation_id (str): 对话ID
            
        Returns:
            Optional[Conversation]: 对话对象，如果不存在则返回None
        """
        return self.conversations.get(conversation_id)
    
    def get_current_conversation(self) -> Optional[Conversation]:
        """
        获取当前对话
        
        Returns:
            Optional[Conversation]: 当前对话对象，如果不存在则返回None
        """
        if self.current_conversation_id:
            return self.get_conversation(self.current_conversation_id)
        return None
    
    def set_current_conversation(self, conversation_id: str) -> bool:
        """
        设置当前对话
        
        Args:
            conversation_id (str): 对话ID
            
        Returns:
            bool: 是否成功
        """
        if conversation_id in self.conversations:
            self.current_conversation_id = conversation_id
            logger.info(f"设置当前对话: {conversation_id}")
            return True
        return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话
        
        Args:
            conversation_id (str): 对话ID
            
        Returns:
            bool: 是否成功
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            
            # 如果删除的是当前对话，则重置当前对话ID
            if self.current_conversation_id == conversation_id:
                self.current_conversation_id = None
            
            # 删除存储文件
            file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.info(f"删除对话: {conversation_id}")
            return True
        return False
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        列出所有对话
        
        Returns:
            List[Dict[str, Any]]: 对话列表
        """
        return [
            {
                'conversation_id': conv.conversation_id,
                'title': conv.title,
                'message_count': len(conv.messages),
                'created_at': conv.created_at,
                'updated_at': conv.updated_at,
                'is_current': conv.conversation_id == self.current_conversation_id
            }
            for conv in self.conversations.values()
        ]
    
    def save_conversation(self, conversation_id: str) -> bool:
        """
        保存对话
        
        Args:
            conversation_id (str): 对话ID
            
        Returns:
            bool: 是否成功
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        try:
            file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
            save_json(conversation.to_dict(), file_path)
            logger.info(f"保存对话: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"保存对话出错 {conversation_id}: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        加载对话
        
        Args:
            conversation_id (str): 对话ID
            
        Returns:
            Optional[Conversation]: 加载的对话对象，如果不存在则返回None
        """
        try:
            file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
            if not os.path.exists(file_path):
                return None
            
            data = load_json(file_path)
            if not data:
                return None
            
            conversation = Conversation.from_dict(data)
            self.conversations[conversation_id] = conversation
            logger.info(f"加载对话: {conversation_id}")
            return conversation
        except Exception as e:
            logger.error(f"加载对话出错 {conversation_id}: {e}")
            return None
    
    def save_all_conversations(self) -> bool:
        """
        保存所有对话
        
        Returns:
            bool: 是否全部成功
        """
        success = True
        for conversation_id in self.conversations:
            if not self.save_conversation(conversation_id):
                success = False
        return success
    
    def load_all_conversations(self) -> bool:
        """
        加载所有对话
        
        Returns:
            bool: 是否成功
        """
        try:
            # 清空当前对话
            self.conversations = {}
            self.current_conversation_id = None
            
            # 获取存储目录中的所有JSON文件
            files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
            
            for file in files:
                conversation_id = file[:-5]  # 去掉.json后缀
                self.load_conversation(conversation_id)
            
            logger.info(f"加载所有对话，共{len(self.conversations)}个")
            return True
        except Exception as e:
            logger.error(f"加载所有对话出错: {e}")
            return False