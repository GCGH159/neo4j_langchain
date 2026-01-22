"""
笔记管理工具集 - 提供给 Agent 使用的图数据库操作工具
"""
import uuid
from datetime import datetime
from typing import List, Optional
from langchain_core.tools import tool
from app.core.graph import execute_cypher

@tool
def save_note(content: str, entities: List[str] = [], tags: List[str] = []) -> str:
    """
    保存一条笔记，并自动关联提到的实体和标签。
    
    Args:
        content: 笔记的文本内容
        entities: 笔记中提到的关键实体名称列表 (例如: ["Python", "Neo4j"])
        tags: 笔记的分类标签 (例如: ["学习", "编程"])
        
    Returns:
        保存结果描述
    """
    note_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. 创建 Note 节点
    query = """
    CREATE (n:Note {id: $id, content: $content, created_at: $created_at})
    RETURN n
    """
    execute_cypher(query, {"id": note_id, "content": content, "created_at": created_at})
    
    # 2. 处理实体关联
    for entity in entities:
        # MERGE 保证实体存在，然后建立 MENTIONS 关系
        entity_query = """
        MATCH (n:Note {id: $note_id})
        MERGE (e:Entity {name: $name})
        MERGE (n)-[:MENTIONS]->(e)
        """
        execute_cypher(entity_query, {"note_id": note_id, "name": entity})
        
    # 3. 处理标签关联
    for tag in tags:
        # MERGE 标签，建立 HAS_TAG 关系
        tag_query = """
        MATCH (n:Note {id: $note_id})
        MERGE (t:Tag {name: $name})
        MERGE (n)-[:HAS_TAG]->(t)
        """
        execute_cypher(tag_query, {"note_id": note_id, "name": tag})
        
    return f"✅ 笔记已保存 (ID: {note_id[:8]}...)，关联了 {len(entities)} 个实体和 {len(tags)} 个标签。"

@tool
def query_notes(keyword: str) -> str:
    """
    根据关键词搜索笔记。
    
    Args:
        keyword: 搜索关键词 (可以是实体名、标签名或内容片段)
    
    Returns:
        匹配的笔记列表文本
    """
    # 模糊匹配内容，或匹配关联的实体/标签
    query = """
    MATCH (n:Note)
    OPTIONAL MATCH (n)-[:MENTIONS]->(e:Entity)
    OPTIONAL MATCH (n)-[:HAS_TAG]->(t:Tag)
    WHERE n.content CONTAINS $keyword 
       OR e.name CONTAINS $keyword 
       OR t.name CONTAINS $keyword
    RETURN n.content as content, n.created_at as time, 
           collect(distinct e.name) as entities, 
           collect(distinct t.name) as tags
    LIMIT 5
    """
    results = execute_cypher(query, {"keyword": keyword})
    
    if not results:
        return f"未找到关于 '{keyword}' 的笔记。"
    
    response = []
    for r in results:
        entities_str = ", ".join(r['entities']) if r['entities'] else "无"
        tags_str = ", ".join(r['tags']) if r['tags'] else "无"
        response.append(f"📝 [{r['time']}] {r['content']}\n   🔗 实体: {entities_str} | 🏷️ 标签: {tags_str}")
        
    return "\n\n".join(response)

@tool
def create_relation(entity1: str, entity2: str, relation: str) -> str:
    """
    在两个实体之间手动建立关系。
    
    Args:
        entity1: 第一个实体名称
        entity2: 第二个实体名称
        relation: 关系名称 (例如: "RELATED_TO", "PART_OF", "OWNS")
        
    Returns:
        操作结果
    """
    # 规范化关系名称：大写，下划线
    rel_type = relation.upper().replace(" ", "_")
    
    # 简单的 Cypher 注入防护：仅允许字母数字下划线
    if not rel_type.replace("_", "").isalnum():
        return "❌ 关系名称只能包含字母、数字和下划线。"
    
    query = f"""
    MERGE (e1:Entity {{name: $e1}})
    MERGE (e2:Entity {{name: $e2}})
    MERGE (e1)-[:{rel_type}]->(e2)
    """
    execute_cypher(query, {"e1": entity1, "e2": entity2})
    
    return f"✅ 已建立关系: ({entity1})-[:{rel_type}]->({entity2})"

@tool
def list_recent_notes(limit: int = 5) -> str:
    """
    列出最近的笔记。
    
    Args:
        limit: 返回数量，默认 5
    
    Returns:
        笔记列表
    """
    query = """
    MATCH (n:Note)
    RETURN n.content as content, n.created_at as time
    ORDER BY n.created_at DESC
    LIMIT $limit
    """
    results = execute_cypher(query, {"limit": limit})
    
    if not results:
        return "📭 还没有任何笔记。"
        
    response = ["最近的笔记："]
    for r in results:
        response.append(f"- [{r['time']}] {r['content']}")
        
    return "\n".join(response)

@tool
def get_entity_info(name: str) -> str:
    """
    获取某个实体的详细信息（关联的笔记、和其他实体的关系）。
    
    Args:
        name: 实体名称
        
    Returns:
        实体详情
    """
    # 1. 查找关联笔记
    notes_query = """
    MATCH (e:Entity {name: $name})<-[:MENTIONS]-(n:Note)
    RETURN n.content as content
    LIMIT 3
    """
    notes = execute_cypher(notes_query, {"name": name})
    
    # 2. 查找关联的其他实体
    rels_query = """
    MATCH (e:Entity {name: $name})-[r]->(other:Entity)
    RETURN type(r) as rel, other.name as other_name
    UNION
    MATCH (e:Entity {name: $name})<-[r]-(other:Entity)
    RETURN type(r) as rel, other.name as other_name
    """
    rels = execute_cypher(rels_query, {"name": name})
    
    if not notes and not rels:
        return f"未找到实体 '{name}' 的相关信息。"
        
    info = [f"🔍 关于 '{name}' 的信息："]
    
    if notes:
        info.append("\n相关笔记：")
        for n in notes:
            info.append(f"- {n['content']}")
            
    if rels:
        info.append("\n关联实体：")
        for r in rels:
            info.append(f"- {r['rel']} {r['other_name']}")
            
    return "\n".join(info)
