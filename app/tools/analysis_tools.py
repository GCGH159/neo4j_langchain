"""
分析工具集 - 为 Plan-and-Execute 工作流提供分析能力
"""
from typing import List, Dict, Optional
from langchain_core.tools import tool
from app.core.graph import execute_cypher


@tool
def analyze_text_entities(content: str) -> str:
    """
    分析文本内容，提取关键实体和标签。
    
    Args:
        content: 要分析的文本内容
        
    Returns:
        提取的实体和标签列表，以及它们的类型说明
    """
    # 使用简单的规则提取（后续可以换成 LLM 调用）
    import re
    
    # 常见技术词汇和实体模式
    tech_keywords = [
        'Python', 'JavaScript', 'Java', 'Go', 'Rust', 'C++', 'TypeScript',
        'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring',
        'LangChain', 'OpenAI', 'Neo4j', 'PostgreSQL', 'MongoDB', 'Redis',
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
        'AI', 'LLM', '机器学习', '深度学习', 'NLP',
        'API', 'REST', 'GraphQL', '微服务', '数据库'
    ]
    
    entities = []
    tags = []
    
    # 提取技术关键词
    for keyword in tech_keywords:
        if keyword.lower() in content.lower():
            if keyword not in entities:
                entities.append(keyword)
    
    # 提取人名（简单规则：2-4个汉字）
    chinese_names = re.findall(r'[\u4e00-\u9fa5]{2,4}', content)
    for name in chinese_names:
        # 排除常见非人名词汇
        if name not in ['一个', '这个', '那个', '什么', '如何', '可以', '应该', '然后', '因为', '所以']:
            if name not in entities:
                entities.append(name)
    
    # 提取标签（基于关键词推断）
    tag_keywords = {
        '编程': ['代码', '开发', '程序', '函数', '变量', 'API'],
        '数据库': ['存储', '查询', 'SQL', '数据', '表', '关系'],
        'AI': ['模型', '训练', '预测', '智能', 'LLM', '大模型'],
        '运维': ['部署', '服务器', 'Docker', 'K8s', '运维'],
        '架构': ['设计', '模式', '微服务', '系统', '模块'],
        '学习': ['教程', '入门', '基础', '概念', '理解']
    }
    
    for tag, keywords in tag_keywords.items():
        for keyword in keywords:
            if keyword in content:
                if tag not in tags:
                    tags.append(tag)
                break
    
    # 如果没有提取到标签，默认给一个
    if not tags:
        tags = ['通用']
    
    return f"""
📋 **文本分析结果**

**提取的实体 ({len(entities)} 个):**
{', '.join([f'• {e}' for e in entities]) if entities else '无明显实体'}

**建议的标签 ({len(tags)} 个):**
{', '.join([f'• {t}' for t in tags]) if tags else '无'}

**分析建议:**
- 如果实体在图中已存在，系统会查询其现有位置
- 如果是新增实体，系统会建议合适的关系类型
"""


@tool
def get_entity_position(entity_name: str) -> str:
    """
    查询实体在图中的现有位置和关联关系。
    
    Args:
        entity_name: 实体名称
        
    Returns:
        实体的现有位置、关联的笔记、关联的其他实体
    """
    # 1. 查找关联笔记
    notes_query = """
    MATCH (e:Entity {name: $name})<-[:MENTIONS]-(n:Note)
    RETURN n.content as content, n.created_at as time
    ORDER BY n.created_at DESC
    LIMIT 5
    """
    notes = execute_cypher(notes_query, {"name": entity_name})
    
    # 2. 查找关联的其他实体（双向）
    rels_query = """
    MATCH (e:Entity {name: $name})-[r]->(other:Entity)
    RETURN type(r) as rel, other.name as other_name
    UNION
    MATCH (e:Entity {name: $name})<-[r]-(other:Entity)
    RETURN type(r) as rel, other.name as other_name
    """
    rels = execute_cypher(rels_query, {"name": entity_name})
    
    # 3. 查找关联的标签
    tags_query = """
    MATCH (e:Entity {name: $name})<-[:MENTIONS]-(n:Note)-[:HAS_TAG]->(t:Tag)
    RETURN collect(distinct t.name) as tags
    """
    tags_result = execute_cypher(tags_query, {"name": entity_name})
    tags = tags_result[0]['tags'] if tags_result and tags_result[0]['tags'] else []
    
    # 构建响应
    response = [f"🔍 实体 '{entity_name}' 的现有位置:"]
    
    if notes:
        response.append(f"\n📝 相关笔记 ({len(notes)} 条):")
        for n in notes:
            content = n['content'][:50] + '...' if len(n['content']) > 50 else n['content']
            response.append(f"  • [{n['time']}] {content}")
    else:
        response.append("\n📝 暂无关联笔记")
    
    if rels:
        response.append(f"\n🔗 关联实体 ({len(rels)} 个):")
        for r in rels:
            response.append(f"  • {entity_name} -[:{r['rel']}]-> {r['other_name']}")
    else:
        response.append("\n🔗 暂无关联实体")
    
    if tags:
        response.append(f"\n🏷️ 关联标签: {', '.join(tags)}")
    
    if not notes and not rels:
        response.append("\n💡 这是新实体，建议建立新的关联关系")
    
    return "\n".join(response)


@tool
def suggest_relations(new_entity: str, context_entities: List[str], content: str) -> str:
    """
    基于上下文，建议新实体应该和哪些实体建立关系。
    
    Args:
        new_entity: 新实体的名称
        context_entities: 上下文中提到的其他实体
        content: 原始文本内容
        
    Returns:
        建议的关系类型和理由
    """
    if not context_entities:
        return f"""
💡 **'{new_entity}' 关系建议**

这是新实体，暂无现有关联。

建议操作：
- 先创建笔记，建立基本记录
- 后续可以手动或根据新笔记补充关联关系
"""
    
    # 查询上下文实体之间的关系
    existing_rels = []
    for ctx_entity in context_entities[:3]:  # 最多查询3个
        rels_query = """
        MATCH (e1:Entity {name: $e1})-[r]->(e2:Entity)
        WHERE e2.name IN $context
        RETURN e1.name as from, type(r) as rel, e2.name as to
        """
        result = execute_cypher(rels_query, {"e1": ctx_entity, "context": context_entities})
        existing_rels.extend(result)
    
    # 基于现有关系和新实体的语义，建议新关系
    suggestions = []
    
    # 技术栈类关系
    tech_stack_rels = ['DEPENDS_ON', 'BUILT_WITH', 'USES', 'INTEGRATED_WITH']
    
    # 学习类关系  
    learning_rels = ['LEARNS', 'RELATED_TO', 'PART_OF']
    
    # 项目类关系
    project_rels = ['OWNS', 'MAINTAINS', 'CONTRIBUTES_TO']
    
    # 基于名称推断关系类型
    new_lower = new_entity.lower()
    
    if any(kw in new_lower for kw in ['langchain', 'openai', 'pytorch', 'tensorflow']):
        for rel in tech_stack_rels:
            suggestions.append({
                'relation': rel,
                'target': context_entities[0] if context_entities else None,
                'reason': f"'{new_entity}' 是一个技术框架/库，可能依赖或配合 {context_entities[0] if context_entities else '其他工具'} 使用"
            })
    
    elif any(kw in new_lower for kw in ['python', 'javascript', 'java', 'rust']):
        for rel in learning_rels:
            suggestions.append({
                'relation': rel,
                'target': context_entities[0] if context_entities else None,
                'reason': f"'{new_entity}' 是一种编程语言，通常用于 {context_entities[0] if context_entities else '相关领域'}"
            })
    
    else:
        # 通用关系建议
        suggestions.append({
            'relation': 'RELATED_TO',
            'target': context_entities[0] if context_entities else None,
            'reason': f"'{new_entity}' 与 {context_entities[0] if context_entities else '其他实体'} 存在关联"
        })
    
    # 构建响应
    response = [f"🔮 **'{new_entity}' 关系建议**"]
    response.append(f"\n上下文实体: {', '.join(context_entities)}")
    response.append(f"\n现有关联: {len(existing_rels)} 个已知关系")
    
    response.append("\n\n📋 **建议建立的关系:**")
    
    for i, sug in enumerate(suggestions, 1):
        target = sug['target'] or '后续补充'
        response.append(f"\n{i}. 与 **{target}** 建立 [:{sug['relation']}] 关系")
        response.append(f"   理由: {sug['reason']}")
    
    if not suggestions:
        response.append("\n暂无法推断具体关系，建议：")
        response.append("  • 使用 RELATED_TO 建立通用关联")
        response.append("  • 手动补充更精确的关系类型")
    
    return "\n".join(response)


@tool
def analyze_graph_position(entity_name: str) -> str:
    """
    分析实体在图中的中心度和重要程度。
    
    Args:
        entity_name: 实体名称
        
    Returns:
        实体的重要性评估和位置建议
    """
    # 1. 计算度数中心性
    degree_query = """
    MATCH (e:Entity {name: $name})
    OPTIONAL MATCH (e)-[r1]->()
    OPTIONAL MATCH ()-[r2]->(e)
    RETURN 
        count(r1) as out_degree,
        count(r2) as in_degree,
        count(r1) + count(r2) as total_degree
    """
    degree = execute_cypher(degree_query, {"name": entity_name})
    
    if degree and degree[0]['total_degree'] > 0:
        d = degree[0]
        importance = "高" if d['total_degree'] > 5 else "中" if d['total_degree'] > 2 else "低"
        
        return f"""
📊 **'{entity_name}' 图位置分析**

**中心度指标:**
  • 出度 (指向他人): {d['out_degree']}
  • 入度 (被指向): {d['in_degree']}
  • 总度数: {d['total_degree']}

**重要性评估:** {importance}

**位置特征:**
  - {'核心节点（与多个实体相连）' if importance == '高' else '一般节点（连接较少）' if importance == '中' else '边缘节点（新实体或孤立实体）'}

**建议:**
  - {'这是重要实体，可以作为新实体的参考点' if importance == '高' else '可以尝试建立更多关联'}
  - {'建议新实体与其建立关系以融入网络' if importance != '高' else '可以考虑让新实体与其产生关联'}
"""
    else:
        return f"""
📊 **'{entity_name}' 图位置分析**

⚠️ 这是图中的**新实体**或**孤立节点**

**建议:**
  1. 先创建笔记建立存在
  2. 后续补充关联关系
  3. 可以作为其他实体的补充说明
"""
