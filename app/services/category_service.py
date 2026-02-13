"""
分类管理服务
"""
from typing import Optional, List, Dict
import json

from app.config.database import neo4j_db, redis_db
from app.config.logging_config import log
from app.agents.relation_agent import RelationAgent


class CategoryService:
    """分类服务类"""
    
    def __init__(self):
        self.relation_agent = RelationAgent()
    
    def get_category_tree(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        获取分类树
        
        Args:
            user_id: 用户ID（可选，用于获取用户偏好分类）
        
        Returns:
            分类树列表
        """
        try:
            # 先从缓存获取
            cache_key = f"category:tree"
            if user_id:
                cache_key = f"user:{user_id}:categories"
            
            cached = redis_db.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 从Neo4j查询
            if user_id:
                # 查询用户偏好的分类
                query = """
                MATCH (u:User {id: $userId})-[:PREFERS]->(c:Category)
                OPTIONAL MATCH (c)<-[:BELONGS_TO]-(sub:Category)
                RETURN DISTINCT c, collect(DISTINCT sub) as sub_categories
                ORDER BY c.level, c.name
                """
                results = neo4j_db.run(query, {"userId": user_id})
            else:
                # 查询所有分类
                query = """
                MATCH (c:Category {level: 1})
                OPTIONAL MATCH (c)<-[:BELONGS_TO]-(sub:Category)
                RETURN DISTINCT c, collect(DISTINCT sub) as sub_categories
                ORDER BY c.name
                """
                results = neo4j_db.run(query)
            
            # 构建分类树
            category_tree = []
            for result in results:
                category = result["c"]
                sub_categories = result["sub_categories"]
                
                category_tree.append({
                    "id": category.get("id"),
                    "name": category.get("name"),
                    "level": category.get("level"),
                    "sub_categories": [
                        {
                            "id": sub.get("id"),
                            "name": sub.get("name"),
                            "level": sub.get("level")
                        }
                        for sub in sub_categories
                    ]
                })
            
            # 缓存结果
            redis_db.set(cache_key, json.dumps(category_tree), ttl=3600)
            
            return category_tree
        
        except Exception as e:
            log.error(f"Error getting category tree: {e}")
            return []
    
    def create_category(
        self,
        name: str,
        level: int,
        parent_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        创建分类
        
        Args:
            name: 分类名称
            level: 分类级别（1或2）
            parent_id: 父分类ID（二级分类需要）
            user_id: 用户ID（可选）
        
        Returns:
            分类信息字典
        """
        try:
            # 创建分类节点
            if level == 1:
                query = """
                CREATE (c:Category {
                    name: $name,
                    level: $level,
                    created_at: datetime()
                })
                RETURN c, id(c) as id
                """
                result = neo4j_db.run_single(query, {"name": name, "level": level})
            else:
                # 二级分类需要关联到一级分类
                if not parent_id:
                    raise ValueError("二级分类需要指定父分类ID")
                
                query = """
                MATCH (parent:Category {id: $parentId})
                CREATE (c:Category {
                    name: $name,
                    level: $level,
                    parent_id: $parentId,
                    created_at: datetime()
                })
                CREATE (c)-[:BELONGS_TO]->(parent)
                RETURN c, id(c) as id
                """
                result = neo4j_db.run_single(query, {
                    "name": name,
                    "level": level,
                    "parentId": parent_id
                })
            
            category = result["c"]
            category_id = result["id"]
            
            # 如果指定了用户，创建用户-分类偏好关系
            if user_id:
                query = """
                MATCH (u:User {id: $userId})
                MATCH (c:Category {id: $categoryId})
                MERGE (u)-[:PREFERS {weight: 0.8}]->(c)
                """
                neo4j_db.run(query, {"userId": user_id, "categoryId": category_id})
            
            # 清除缓存
            self._clear_category_cache(user_id)
            
            # 触发关联分析
            self._trigger_relation_analysis(category_id, user_id)
            
            return {
                "id": category_id,
                "name": category.get("name"),
                "level": category.get("level"),
                "parent_id": category.get("parent_id")
            }
        
        except Exception as e:
            log.error(f"Error creating category: {e}")
            raise
    
    def _trigger_relation_analysis(self, category_id: int, user_id: Optional[int]):
        """触发关联分析"""
        try:
            # 查找相似分类和事件
            query = """
            MATCH (c:Category {id: $categoryId})
            MATCH (other:Category)
            WHERE other.id <> $categoryId
              AND other.name CONTAINS c.name OR c.name CONTAINS other.name
            RETURN other
            LIMIT 10
            """
            similar_categories = neo4j_db.run(query, {"categoryId": category_id})
            
            # 使用Agent分析关联
            if similar_categories:
                self.relation_agent.analyze_category_relations(
                    category_id,
                    [cat["other"] for cat in similar_categories],
                    user_id
                )
            
            log.info(f"Relation analysis triggered for category: {category_id}")
        
        except Exception as e:
            log.error(f"Error triggering relation analysis: {e}")
    
    def _clear_category_cache(self, user_id: Optional[int]):
        """清除分类缓存"""
        try:
            redis_db.delete("category:tree")
            if user_id:
                redis_db.delete(f"user:{user_id}:categories")
        except Exception as e:
            log.error(f"Error clearing category cache: {e}")
    
    def get_category_notes(self, category_id: int, user_id: int) -> List[Dict]:
        """
        获取分类下的速记
        
        Args:
            category_id: 分类ID
            user_id: 用户ID
        
        Returns:
            速记列表
        """
        try:
            query = """
            MATCH (u:User {id: $userId})-[:CREATED]->(n:Note)
            MATCH (n)-[:BELONGS_TO]->(c:Category {id: $categoryId})
            RETURN n
            ORDER BY n.created_at DESC
            LIMIT 50
            """
            results = neo4j_db.run(query, {
                "userId": user_id,
                "categoryId": category_id
            })
            
            notes = []
            for result in results:
                note = result["n"]
                notes.append({
                    "id": note.get("id"),
                    "title": note.get("title"),
                    "content": note.get("content"),
                    "source": note.get("source"),
                    "created_at": note.get("created_at")
                })
            
            return notes
        
        except Exception as e:
            log.error(f"Error getting category notes: {e}")
            return []
    
    def get_category_events(self, category_id: int, user_id: int) -> List[Dict]:
        """
        获取分类下的事件
        
        Args:
            category_id: 分类ID
            user_id: 用户ID
        
        Returns:
            事件列表
        """
        try:
            query = """
            MATCH (u:User {id: $userId})-[:CREATED]->(e:Event)
            MATCH (e)-[:BELONGS_TO]->(c:Category {id: $categoryId})
            RETURN e
            ORDER BY e.created_at DESC
            LIMIT 50
            """
            results = neo4j_db.run(query, {
                "userId": user_id,
                "categoryId": category_id
            })
            
            events = []
            for result in results:
                event = result["e"]
                events.append({
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "description": event.get("description"),
                    "event_type": event.get("event_type"),
                    "status": event.get("status"),
                    "priority": event.get("priority"),
                    "created_at": event.get("created_at")
                })
            
            return events
        
        except Exception as e:
            log.error(f"Error getting category events: {e}")
            return []


# 全局分类服务实例
category_service = CategoryService()
