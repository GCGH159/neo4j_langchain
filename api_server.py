"""
Neo4j + LangChain 前端 API 服务
基于 FastAPI，提供会话管理、流式聊天、数据库信息等接口
"""
import uuid
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import config
from app.core.graph import execute_cypher, get_schema, get_node_labels, get_relationship_types
from app.core.chat_history import Neo4jChatMessageHistory

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.tools.note_tools import (
    save_note, query_notes, create_relation,
    list_recent_notes, get_entity_info, execute_raw_cypher, get_graph_schema
)
from app.tools.analysis_tools import (
    analyze_text_entities, get_entity_position,
    suggest_relations, analyze_graph_position
)

# ==================== 应用初始化 ====================

app = FastAPI(title="Neo4j LangChain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 全局状态 ====================

# LLM 实例
llm = ChatOpenAI(
    model_name=config.LLM_MODEL,
    openai_api_key=config.LLM_API_KEY,
    openai_api_base=config.LLM_BASE_URL,
    temperature=0.7,
    streaming=True,
)

# 工具集
tools = [
    save_note, query_notes, create_relation,
    list_recent_notes, get_entity_info, execute_raw_cypher, get_graph_schema,
    analyze_text_entities, get_entity_position,
    suggest_relations, analyze_graph_position
]

# 系统提示词
system_instruction = SystemMessage(content="""你是一个智能笔记助手，基于 Neo4j 图数据库工作。

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

5. **分析能力**：
   - 可以使用 `analyze_text_entities` 分析文本实体
   - 使用 `get_entity_position` 查询实体在图中的位置
   - 使用 `analyze_graph_position` 分析实体的重要性

6. **对话记忆**：
   - 你可以记住之前的对话内容
   - 在回答问题时，可以参考之前的对话上下文
   - 用户可能会提到"刚才说的"、"之前的"等，请根据对话历史理解

请用中文回答用户。操作成功后，简要反馈结果。如果查询不到信息，请如实告知。
""")

# MemorySaver 用于 LangGraph 的对话记忆
memory = MemorySaver()

# 创建 Agent
agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
)

# 会话元数据存储（内存中维护会话列表，消息历史通过 MemorySaver 自动维护）
sessions_meta: Dict[str, Dict[str, Any]] = {}


# ==================== 数据模型 ====================

class CreateSessionRequest(BaseModel):
    name: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class RenameSessionRequest(BaseModel):
    name: str


# ==================== 会话管理接口 ====================

@app.post("/api/sessions")
async def create_session(req: CreateSessionRequest):
    """创建新会话"""
    session_id = str(uuid.uuid4())[:12]
    now = datetime.now().isoformat()
    sessions_meta[session_id] = {
        "id": session_id,
        "name": req.name or f"新会话",
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
    }
    return sessions_meta[session_id]


@app.get("/api/sessions")
async def list_sessions():
    """列出所有会话"""
    return sorted(sessions_meta.values(), key=lambda s: s["updated_at"], reverse=True)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    if session_id not in sessions_meta:
        raise HTTPException(status_code=404, detail="会话不存在")
    return sessions_meta[session_id]


@app.put("/api/sessions/{session_id}")
async def rename_session(session_id: str, req: RenameSessionRequest):
    """重命名会话"""
    if session_id not in sessions_meta:
        raise HTTPException(status_code=404, detail="会话不存在")
    sessions_meta[session_id]["name"] = req.name
    sessions_meta[session_id]["updated_at"] = datetime.now().isoformat()
    return sessions_meta[session_id]


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in sessions_meta:
        del sessions_meta[session_id]
    return {"status": "ok"}


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取会话的历史消息（从 MemorySaver 获取）"""
    try:
        config_obj = {"configurable": {"thread_id": session_id}}
        state = agent.get_state(config_obj)
        messages = state.values.get("messages", [])

        result = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({
                    "role": "user",
                    "content": msg.content,
                })
            elif isinstance(msg, AIMessage):
                # 跳过工具调用中间消息（无文本内容的）
                if msg.content:
                    result.append({
                        "role": "assistant",
                        "content": msg.content,
                    })
            # SystemMessage 等不返回给前端
        return result
    except Exception:
        return []


# ==================== 聊天接口（SSE 流式） ====================

@app.post("/api/chat")
async def chat_stream(req: ChatRequest):
    """流式聊天接口（SSE）"""
    session_id = req.session_id
    user_message = req.message

    # 自动创建会话元数据（如果不存在）
    if session_id not in sessions_meta:
        now = datetime.now().isoformat()
        sessions_meta[session_id] = {
            "id": session_id,
            "name": user_message[:20] + ("..." if len(user_message) > 20 else ""),
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }

    # 更新会话时间
    sessions_meta[session_id]["updated_at"] = datetime.now().isoformat()
    sessions_meta[session_id]["message_count"] += 1

    config_obj = {"configurable": {"thread_id": session_id}}

    async def event_generator():
        try:
            # 构建输入：只传入当前用户消息，MemorySaver 自动维护历史
            input_messages = [system_instruction, HumanMessage(content=user_message)]

            # 检查是否已有历史（如果有，system_instruction 已经在历史中了）
            try:
                state = agent.get_state(config_obj)
                existing = state.values.get("messages", [])
                if existing:
                    # 已有历史，只追加用户消息
                    input_messages = [HumanMessage(content=user_message)]
            except Exception:
                pass

            full_response = ""
            # 使用 stream 进行流式输出
            for chunk, metadata in agent.stream(
                {"messages": input_messages},
                config=config_obj,
                stream_mode="messages"
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    full_response += chunk.content
                    data = json.dumps({"type": "content", "content": chunk.content}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                    await asyncio.sleep(0)  # 让出事件循环

            # 发送完成信号
            done_data = json.dumps({"type": "done", "content": full_response}, ensure_ascii=False)
            yield f"data: {done_data}\n\n"

            # 如果是第一条消息，用其内容作为会话名称
            if sessions_meta.get(session_id, {}).get("message_count", 0) <= 1:
                sessions_meta[session_id]["name"] = user_message[:30] + ("..." if len(user_message) > 30 else "")

        except Exception as e:
            error_data = json.dumps({"type": "error", "content": f"错误: {str(e)}"}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ==================== 数据库信息接口 ====================

@app.get("/api/db/schema")
async def db_schema():
    """获取数据库 Schema"""
    try:
        schema = get_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/db/stats")
async def db_stats():
    """获取数据库统计信息"""
    try:
        labels = get_node_labels()
        rel_types = get_relationship_types()

        node_counts = {}
        for label in labels:
            result = execute_cypher(f"MATCH (n:`{label}`) RETURN count(n) as count")
            node_counts[label] = result[0]['count'] if result else 0

        rel_result = execute_cypher("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = rel_result[0]['count'] if rel_result else 0

        return {
            "labels": labels,
            "relationship_types": rel_types,
            "node_counts": node_counts,
            "total_relationships": rel_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """健康检查"""
    neo4j_ok = False
    try:
        execute_cypher("RETURN 1")
        neo4j_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if neo4j_ok else "degraded",
        "neo4j": neo4j_ok,
        "llm_model": config.LLM_MODEL,
    }


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
