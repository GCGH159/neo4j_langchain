"""
笔记管理 Agent 逻辑封装
"""
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from app.tools.note_tools import save_note, query_notes, create_relation, list_recent_notes, get_entity_info
from config import config

class NoteAgent:
    """笔记智能体，具备读写图谱的能力"""
    
    def __init__(self):
        # 1. 初始化 LLM
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            temperature=0.7,
        )
        
        # 2. 定义工具集
        self.tools = [save_note, query_notes, create_relation, list_recent_notes, get_entity_info]
        
        # 3. 创建系统提示词
        system_prompt = """你是一个智能笔记助手，基于 Neo4j 图数据库工作。
            
            你的核心能力：
            1. **自动记录**：当用户输入笔记时，调用 `save_note`。你需要智能提取文本中的“重要实体”(entities)和“标签”(tags)。
               - 实体：人名、技术名词、项目名、地点等（如 "Python", "LangChain", "张三"）。
               - 标签：主题分类（如 "学习", "会议", "灵感"）。
            
            2. **信息检索**：
               - 当用户问“与其相关的笔记”或搜索内容时，调用 `query_notes` 或 `get_entity_info`。
               - 当用户想看最近的记录时，调用 `list_recent_notes`。

            3. **关系管理**：
               - 当用户明确指出两个事物的关系时（如“A 是 B 的子集”），调用 `create_relation`。
            
            请用中文回答用户。操作成功后，简要反馈结果。如果查询不到信息，请如实告知。
            """
        
        # 4. 创建 Agent (Graph)
        self.graph = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt
        )
        
    def chat(self, user_input: str) -> str:
        """
        与 Agent 对话
        """
        try:
            # 使用 invoke 调用图
            inputs = {"messages": [{"role": "user", "content": user_input}]}
            
            # 运行图
            # result 是最终状态，包含 messages 列表
            final_state = self.graph.invoke(inputs)
            
            # 获取最后一条消息 (AIMessage)
            messages = final_state.get("messages", [])
            if messages:
                last_message = messages[-1]
                return last_message.content
            return "Agent 没有回应。"
            
        except Exception as e:
            return f"❌ Agent 运行出错: {e}"

# 单例实例
note_agent = NoteAgent()
