"""
带记忆功能的笔记管理 Agent - 支持持续性对话
"""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from app.tools.note_tools import (
    save_note, query_notes, create_relation, list_recent_notes, 
    get_entity_info, execute_raw_cypher, get_graph_schema
)
from app.core.chat_history import get_session_history
from config import config
from pydantic import SecretStr
import uuid


class NoteAgentWithMemory:
    """
    带记忆功能的笔记智能体
    - 支持持续性对话（对话历史存储在 Neo4j）
    - 具备读写图谱的能力
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        初始化 Agent
        
        Args:
            session_id: 会话ID，如果为 None 则自动生成
        """
        self.session_id = session_id or str(uuid.uuid4())
        
        # 1. 初始化 LLM
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=SecretStr(config.LLM_API_KEY) if config.LLM_API_KEY else None,
            base_url=config.LLM_BASE_URL,
            temperature=0.7,
        )
        
        # 2. 定义工具集
        self.tools = [
            save_note,
            query_notes,
            create_relation,
            list_recent_notes,
            get_entity_info,
            execute_raw_cypher,
            get_graph_schema
        ]
        
        # 3. 创建系统提示词
        system_prompt = """你是一个智能笔记助手，基于 Neo4j 图数据库工作。
            
你的核心能力：
1. **直接执行 Cypher 语句（推荐）**：
   - 当用户需要复杂的查询或操作时，优先使用 `execute_raw_cypher` 工具直接编写和执行 Cypher 语句
   - 在执行复杂查询前，可以先调用 `get_graph_schema` 了解数据库结构
   - Cypher 语句应该使用参数化查询（$param）来避免注入问题
   
2. **自动记录**：当用户输入笔记时，调用 `save_note`。你需要智能提取文本中的"重要实体"(entities)和"标签"(tags)。
   - 实体：人名、技术名词、项目名、地点等（如 "Python", "LangChain", "张三"）。
   - 标签：主题分类（如 "学习", "会议", "灵感"）。

3. **信息检索**：
   - 简单查询可以使用 `query_notes` 或 `get_entity_info`
   - 复杂查询（如多跳关系、聚合统计等）应该直接编写 Cypher 语句
   
4. **关系管理**：
   - 当用户明确指出两个事物的关系时，调用 `create_relation`
   - 也可以直接用 Cypher 语句创建更复杂的关系模式

5. **对话记忆**：
   - 你可以记住之前的对话内容
   - 在回答问题时，可以参考之前的对话上下文
   - 用户可能会提到"刚才说的"、"之前的"等，请根据对话历史理解

6. **灵活应对**：
   - 如果现有工具无法满足需求，直接编写 Cypher 语句实现
   - 例如：统计某个标签下的笔记数量、查找两个实体的共同笔记、查找最热门的实体等

请用中文回答用户。操作成功后，简要反馈结果。如果查询不到信息，请如实告知。
"""
        
        # 4. 创建 Agent
        self.graph = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt
        )
        
        # 5. 获取会话历史管理器
        self.history = get_session_history(self.session_id)
        
    def chat(self, user_input: str) -> str:
        """
        与 Agent 对话（支持持续性对话）
        
        Args:
            user_input: 用户输入
            
        Returns:
            Agent 的回复
        """
        try:
            # 获取历史消息
            history_messages = self.history.get_recent_messages(limit=50)
            
            # 构建包含历史的输入
            all_messages = history_messages + [{"role": "user", "content": user_input}]
            inputs = {"messages": all_messages}
            
            # 运行 Agent
            final_state = self.graph.invoke(inputs)
            
            # 获取最后一条消息 (AIMessage)
            messages = final_state.get("messages", [])
            if messages:
                last_message = messages[-1]
                response_content = last_message.content
                
                # 保存对话历史到 Neo4j
                from langchain_core.messages import HumanMessage, AIMessage
                self.history.add_message(HumanMessage(content=user_input))
                self.history.add_message(AIMessage(content=response_content))
                
                return response_content
            return "Agent 没有回应。"
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"❌ Agent 运行出错: {e}\n详细信息:\n{error_details}"
    
    def get_session_id(self) -> str:
        """获取当前会话ID"""
        return self.session_id
    
    def clear_history(self):
        """清空当前会话的对话历史"""
        self.history.clear()
    
    def get_message_count(self) -> int:
        """获取当前会话的消息数量"""
        return self.history.get_message_count()


# 默认实例（无持久化会话）
note_agent_with_memory = NoteAgentWithMemory()


# 便捷函数
def create_session(session_id: Optional[str] = None) -> NoteAgentWithMemory:
    """
    创建一个新的带记忆的 Agent 会话
    
    Args:
        session_id: 可选的会话ID
        
    Returns:
        NoteAgentWithMemory 实例
    """
    return NoteAgentWithMemory(session_id)
