"""
Neo4j 图数据库连接与操作封装
"""
from langchain_neo4j import Neo4jGraph
from config import config


class Neo4jConnection:
    """Neo4j 连接管理器"""
    
    _instance: Neo4jGraph | None = None
    
    @classmethod
    def get_graph(cls) -> Neo4jGraph:
        """获取 Neo4j 图实例（单例模式）"""
        if cls._instance is None:
            cls._instance = Neo4jGraph(
                url=config.NEO4J_URI,
                username=config.NEO4J_USERNAME,
                password=config.NEO4J_PASSWORD,
                enhanced_schema=True  # 增强 Schema 信息 (依赖 APOC)
            )
        return cls._instance
    
    @classmethod
    def close(cls):
        """关闭连接"""
        if cls._instance:
            cls._instance._driver.close()
            cls._instance = None
    
    @classmethod
    def refresh_schema(cls):
        """刷新数据库 Schema"""
        graph = cls.get_graph()
        graph.refresh_schema()
        return graph.schema


def get_schema() -> str:
    """获取数据库 Schema 信息"""
    graph = Neo4jConnection.get_graph()
    return graph.schema


def execute_cypher(query: str, params: dict = None) -> list:
    """执行 Cypher 查询"""
    graph = Neo4jConnection.get_graph()
    return graph.query(query, params or {})


def get_node_labels() -> list[str]:
    """获取所有节点标签"""
    result = execute_cypher("CALL db.labels()")
    return [r['label'] for r in result]


def get_relationship_types() -> list[str]:
    """获取所有关系类型"""
    result = execute_cypher("CALL db.relationshipTypes()")
    return [r['relationshipType'] for r in result]


def get_node_count(label: str = None) -> int:
    """获取节点数量"""
    if label:
        query = f"MATCH (n:`{label}`) RETURN count(n) as count"
    else:
        query = "MATCH (n) RETURN count(n) as count"
    result = execute_cypher(query)
    return result[0]['count'] if result else 0
