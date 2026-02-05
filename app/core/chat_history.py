"""
对话历史管理 - 使用 Neo4j 存储对话历史
"""
from typing import List, Optional
from datetime import datetime
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.core.graph import execute_cypher


class Neo4jChatMessageHistory(BaseChatMessageHistory):
    """
    使用 Neo4j 存储和检索对话历史
    
    存储结构：
    - (Session)-[:HAS_MESSAGE]->(Message)
    - Message 节点包含: role, content, timestamp
    """
    
    def __init__(self, session_id: str):
        """
        初始化对话历史管理器
        
        Args:
            session_id: 会话ID，用于区分不同的对话
        """
        self.session_id = session_id
        self._ensure_session_exists()
    
    def _ensure_session_exists(self):
        """确保会话节点存在"""
        query = """
        MERGE (s:Session {id: $session_id})
        ON CREATE SET s.created_at = $timestamp
        RETURN s
        """
        execute_cypher(query, {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_message(self, message: BaseMessage) -> None:
        """
        添加一条消息到对话历史
        
        Args:
            message: 要添加的消息
        """
        query = """
        MATCH (s:Session {id: $session_id})
        CREATE (m:Message {
            role: $role,
            content: $content,
            timestamp: $timestamp
        })
        CREATE (s)-[:HAS_MESSAGE]->(m)
        RETURN m
        """
        execute_cypher(query, {
            "session_id": self.session_id,
            "role": message.type,
            "content": message.content,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_messages(self, messages: List[BaseMessage]) -> None:
        """批量添加消息"""
        for message in messages:
            self.add_message(message)
    
    @property
    def messages(self) -> List[BaseMessage]:
        """
        获取会话的所有消息历史
        
        Returns:
            消息列表，按时间排序
        """
        query = """
        MATCH (s:Session {id: $session_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN m.role as role, m.content as content, m.timestamp as timestamp
        ORDER BY m.timestamp
        """
        results = execute_cypher(query, {"session_id": self.session_id})
        
        messages = []
        for r in results:
            role = r['role']
            content = r['content']
            
            if role == 'human':
                messages.append(HumanMessage(content=content))
            elif role == 'ai':
                messages.append(AIMessage(content=content))
            elif role == 'system':
                messages.append(SystemMessage(content=content))
        
        return messages
    
    def clear(self) -> None:
        """清空会话的所有消息"""
        query = """
        MATCH (s:Session {id: $session_id})-[:HAS_MESSAGE]->(m:Message)
        DETACH DELETE m
        """
        execute_cypher(query, {"session_id": self.session_id})
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        query = """
        MATCH (s:Session {id: $session_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN count(m) as count
        """
        result = execute_cypher(query, {"session_id": self.session_id})
        return result[0]['count'] if result else 0
    
    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        """
        获取最近的 N 条消息
        
        Args:
            limit: 要获取的消息数量
            
        Returns:
            最近的消息列表
        """
        query = """
        MATCH (s:Session {id: $session_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN m.role as role, m.content as content, m.timestamp as timestamp
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """
        results = execute_cypher(query, {
            "session_id": self.session_id,
            "limit": limit
        })
        
        messages = []
        for r in reversed(results):  # 反转以保持时间顺序
            role = r['role']
            content = r['content']
            
            if role == 'human':
                messages.append(HumanMessage(content=content))
            elif role == 'ai':
                messages.append(AIMessage(content=content))
            elif role == 'system':
                messages.append(SystemMessage(content=content))
        
        return messages


def get_session_history(session_id: str) -> Neo4jChatMessageHistory:
    """
    获取或创建会话历史管理器
    
    Args:
        session_id: 会话ID
        
    Returns:
        对话历史管理器实例
    """
    return Neo4jChatMessageHistory(session_id)
