"""
记忆裁剪 Agent - 负责整理和优化 Neo4j 图谱中的记忆
"""
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from app.core.graph import execute_cypher
from config import config
from pydantic import SecretStr


# ==================== 记忆裁剪工具集 ====================

@tool
def analyze_memory_graph() -> str:
    """
    分析当前记忆图谱的状态，包括节点数量、关系密度、冗余信息等。
    
    Returns:
        图谱分析报告
    """
    query = """
    // 统计各类节点数量
    MATCH (n)
    WITH labels(n) as label_list, count(n) as node_count
    UNWIND label_list as label
    WITH label, sum(node_count) as count
    WHERE count > 0
    RETURN label, count
    ORDER BY count DESC
    """
    node_stats = execute_cypher(query)
    
    # 统计关系
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as rel_type, count(r) as count
    ORDER BY count DESC
    """
    rel_stats = execute_cypher(rel_query)
    
    # 查找孤立节点
    orphan_query = """
    MATCH (n)
    WHERE NOT (n)-[]-()
    RETURN labels(n)[0] as label, count(n) as orphan_count
    """
    orphan_stats = execute_cypher(orphan_query)
    
    report = ["📊 记忆图谱分析报告\n"]
    report.append("节点统计:")
    for stat in node_stats:
        report.append(f"  • {stat['label']}: {stat['count']} 个")
    
    report.append("\n关系统计:")
    for stat in rel_stats:
        report.append(f"  • {stat['rel_type']}: {stat['count']} 条")
    
    if orphan_stats and any(s['orphan_count'] > 0 for s in orphan_stats):
        report.append("\n⚠️  发现孤立节点:")
        for stat in orphan_stats:
            if stat['orphan_count'] > 0:
                report.append(f"  • {stat['label']}: {stat['orphan_count']} 个")
    
    return "\n".join(report)


@tool
def find_redundant_entities() -> str:
    """
    查找冗余的实体节点（名称相似、关系相同的实体）。
    
    Returns:
        冗余实体列表
    """
    query = """
    // 查找名称非常相似的实体
    MATCH (e1:Entity), (e2:Entity)
    WHERE e1.name < e2.name
      AND (
        toLower(e1.name) = toLower(e2.name) OR
        e1.name CONTAINS e2.name OR
        e2.name CONTAINS e1.name
      )
    RETURN e1.name as name1, e2.name as name2
    LIMIT 20
    """
    results = execute_cypher(query)
    
    if not results:
        return "✅ 未发现明显的冗余实体"
    
    report = ["⚠️  发现可能冗余的实体:"]
    for r in results:
        report.append(f"  • '{r['name1']}' ↔️ '{r['name2']}'")
    
    return "\n".join(report)


@tool
def merge_similar_entities(entity1: str, entity2: str, keep_name: str) -> str:
    """
    合并两个相似的实体节点，保留指定名称的实体。
    
    Args:
        entity1: 第一个实体名称
        entity2: 第二个实体名称
        keep_name: 要保留的实体名称（必须是 entity1 或 entity2）
        
    Returns:
        合并结果
    """
    if keep_name not in [entity1, entity2]:
        return f"❌ keep_name 必须是 '{entity1}' 或 '{entity2}'"
    
    remove_name = entity2 if keep_name == entity1 else entity1
    
    # 简化的合并逻辑：转移所有关系后删除冗余节点
    query = """
    MATCH (keep:Entity {name: $keep_name})
    MATCH (remove:Entity {name: $remove_name})
    
    // 复制 MENTIONS 关系
    WITH keep, remove
    OPTIONAL MATCH (n:Note)-[r:MENTIONS]->(remove)
    MERGE (n)-[:MENTIONS]->(keep)
    DELETE r
    
    // 删除冗余节点
    WITH keep, remove
    DETACH DELETE remove
    RETURN keep.name as kept_entity
    """
    
    try:
        execute_cypher(query, {
            "keep_name": keep_name,
            "remove_name": remove_name
        })
        return f"✅ 已合并实体: '{remove_name}' → '{keep_name}'"
    except Exception as e:
        return f"❌ 合并失败: {e}"


@tool
def remove_orphan_nodes(label: str = "all") -> str:
    """
    删除孤立的节点（没有任何关系的节点）。
    
    Args:
        label: 节点标签，"all" 表示删除所有类型的孤立节点
        
    Returns:
        删除结果
    """
    if label == "all":
        query = """
        MATCH (n)
        WHERE NOT (n)-[]-()
        DELETE n
        RETURN count(n) as deleted_count
        """
    else:
        query = f"""
        MATCH (n:`{label}`)
        WHERE NOT (n)-[]-()
        DELETE n
        RETURN count(n) as deleted_count
        """
    
    try:
        result = execute_cypher(query, {})
        count = result[0]['deleted_count'] if result else 0
        return f"✅ 已删除 {count} 个孤立节点"
    except Exception as e:
        return f"❌ 删除失败: {e}"


@tool
def prune_old_messages(session_id: str, keep_recent: int = 20) -> str:
    """
    裁剪旧的对话消息，只保留最近的 N 条。
    
    Args:
        session_id: 会话ID
        keep_recent: 要保留的最近消息数量
        
    Returns:
        裁剪结果
    """
    query = """
    MATCH (s:Session {id: $session_id})-[:HAS_MESSAGE]->(m:Message)
    WITH m
    ORDER BY m.timestamp DESC
    SKIP $keep_recent
    DETACH DELETE m
    RETURN count(m) as deleted_count
    """
    
    try:
        result = execute_cypher(query, {
            "session_id": session_id,
            "keep_recent": keep_recent
        })
        count = result[0]['deleted_count'] if result else 0
        return f"✅ 已删除会话 '{session_id}' 的 {count} 条旧消息，保留最近 {keep_recent} 条"
    except Exception as e:
        return f"❌ 裁剪失败: {e}"


@tool
def consolidate_notes_by_topic(topic_keyword: str, new_summary: str) -> str:
    """
    将某个主题的多条笔记合并为一条摘要笔记。
    
    Args:
        topic_keyword: 主题关键词（用于搜索相关笔记）
        new_summary: 新的摘要内容
        
    Returns:
        合并结果
    """
    # 查找相关笔记
    search_query = """
    MATCH (n:Note)
    WHERE n.content CONTAINS $keyword
    RETURN n.id as note_id, n.content as content
    """
    notes = execute_cypher(search_query, {"keyword": topic_keyword})
    
    if not notes:
        return f"未找到包含关键词 '{topic_keyword}' 的笔记"
    
    # 创建新的摘要笔记
    from datetime import datetime
    import uuid
    
    create_query = """
    CREATE (summary:Note {
        id: $id,
        content: $content,
        created_at: $timestamp,
        type: 'summary'
    })
    RETURN summary.id as new_id
    """
    
    new_id = str(uuid.uuid4())
    execute_cypher(create_query, {
        "id": new_id,
        "content": new_summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # 将原笔记的关系转移到摘要笔记
    transfer_query = """
    MATCH (old:Note)
    WHERE old.id IN $old_ids
    MATCH (summary:Note {id: $new_id})
    
    OPTIONAL MATCH (old)-[:MENTIONS]->(e:Entity)
    MERGE (summary)-[:MENTIONS]->(e)
    
    OPTIONAL MATCH (old)-[:HAS_TAG]->(t:Tag)
    MERGE (summary)-[:HAS_TAG]->(t)
    
    WITH old, summary
    DETACH DELETE old
    """
    
    old_ids = [n['note_id'] for n in notes]
    execute_cypher(transfer_query, {"old_ids": old_ids, "new_id": new_id})
    
    return f"✅ 已将 {len(notes)} 条笔记合并为摘要笔记（ID: {new_id[:8]}...）"


# ==================== 记忆裁剪 Agent ====================

class MemoryPruningAgent:
    """
    记忆裁剪 Agent
    负责分析和优化 Neo4j 图谱中的记忆结构
    """
    
    def __init__(self):
        # 1. 初始化 LLM
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=SecretStr(config.LLM_API_KEY) if config.LLM_API_KEY else None,
            base_url=config.LLM_BASE_URL,
            temperature=0.3,  # 较低温度以保持一致性
        )
        
        # 2. 定义工具集
        self.tools = [
            analyze_memory_graph,
            find_redundant_entities,
            merge_similar_entities,
            remove_orphan_nodes,
            prune_old_messages,
            consolidate_notes_by_topic
        ]
        
        # 3. 创建系统提示词
        system_prompt = """你是一个记忆整理专家，负责优化和维护 Neo4j 知识图谱。

你的职责：
1. **分析图谱状态**：定期分析图谱的节点、关系、冗余信息
2. **识别优化机会**：
   - 查找相似或冗余的实体节点
   - 识别孤立的、无关联的节点
   - 发现可以合并的相关笔记
3. **执行优化操作**：
   - 合并相似实体
   - 删除无用的孤立节点
   - 裁剪过期的对话历史
   - 将多条相关笔记整合为摘要
4. **汇报结果**：清晰说明执行了什么操作，产生了什么效果

优化原则：
- 保守为主：不确定时不要删除数据
- 先分析后操作：了解情况后再决定如何优化
- 保留重要信息：删除冗余但保留核心内容
- 用户确认：重大操作前向用户确认

请用中文回答，操作完成后提供详细报告。
"""
        
        # 4. 创建 Agent
        self.graph = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt
        )
    
    def optimize(self, instruction: str = "请分析记忆图谱并提供优化建议") -> str:
        """
        执行记忆优化操作
        
        Args:
            instruction: 优化指令（例如："分析并删除孤立节点"）
            
        Returns:
            优化结果报告
        """
        try:
            inputs = {"messages": [{"role": "user", "content": instruction}]}
            final_state = self.graph.invoke(inputs)
            
            messages = final_state.get("messages", [])
            if messages:
                last_message = messages[-1]
                return last_message.content
            return "Agent 没有回应。"
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"❌ 优化操作出错: {e}\n详细信息:\n{error_details}"


# 单例实例
memory_pruning_agent = MemoryPruningAgent()
