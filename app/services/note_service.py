"""
速记服务（事件/速记创建）
"""
from typing import Optional, List, Dict
from datetime import datetime
import json

from app.config.database import mysql_db, neo4j_db, redis_db
from app.config.logging_config import log
from app.agents.relation_agent import RelationAgent
from app.agents.tag_agent import TagAgent


class NoteService:
    """速记服务类"""
    
    def __init__(self):
        self.relation_agent = RelationAgent()
        self.tag_agent = TagAgent()
    
    def create_event(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        event_type: str = "project",
        status: str = "pending",
        priority: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        创建事件
        
        Args:
            user_id: 用户ID
            title: 事件标题
            description: 事件描述
            event_type: 事件类型（project, long_term_task, important_event, personality）
            status: 事件状态
            priority: 优先级
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            事件信息字典
        """
        try:
            # 1. 保存事件到MySQL
            with mysql_db.get_session() as session:
                from app.models.note import Event
                event = Event(
                    user_id=user_id,
                    title=title,
                    description=description,
                    event_type=event_type,
                    status=status,
                    priority=priority,
                    start_date=start_date,
                    end_date=end_date
                )
                session.add(event)
                session.flush()
                
                event_id = event.id
                log.info(f"Event created in MySQL: {event_id}")
            
            # 2. 在Neo4j中创建Event节点
            self._create_neo4j_event(event_id, user_id, title, description, event_type, priority)
            
            # 3. 调用LangChain Agent进行全局关联分析
            self._global_relation_analysis(event_id, user_id, title, description, event_type)
            
            return {
                "event_id": event_id,
                "user_id": user_id,
                "title": title,
                "description": description,
                "event_type": event_type,
                "status": status,
                "priority": priority,
                "start_date": start_date,
                "end_date": end_date
            }
        
        except Exception as e:
            log.error(f"Error creating event: {e}")
            raise
    
    def _create_neo4j_event(
        self,
        event_id: int,
        user_id: int,
        title: str,
        description: Optional[str],
        event_type: str,
        priority: int
    ):
        """在Neo4j中创建事件节点"""
        query = """
        MATCH (u:User {id: $userId})
        CREATE (e:Event {
            id: $eventId,
            user_id: $userId,
            title: $title,
            description: $description,
            event_type: $eventType,
            priority: $priority,
            created_at: datetime()
        })
        CREATE (u)-[:CREATED]->(e)
        """
        neo4j_db.run(query, {
            "eventId": event_id,
            "userId": user_id,
            "title": title,
            "description": description,
            "eventType": event_type,
            "priority": priority
        })
        log.info(f"Neo4j event node created: {event_id}")
    
    def _global_relation_analysis(
        self,
        event_id: int,
        user_id: int,
        title: str,
        description: Optional[str],
        event_type: str
    ):
        """全局关联分析"""
        try:
            # 查询所有相关内容
            categories = neo4j_db.run("""
                MATCH (c:Category) RETURN c LIMIT 100
            """)
            
            tags = neo4j_db.run("""
                MATCH (t:Tag) RETURN t LIMIT 100
            """)
            
            events = neo4j_db.run("""
                MATCH (e:Event) WHERE e.id <> $eventId RETURN e LIMIT 100
            """, {"eventId": event_id})
            
            notes = neo4j_db.run("""
                MATCH (n:Note) RETURN n LIMIT 100
            """)
            
            # 调用Agent分析关联
            relations = self.relation_agent.analyze_event_relations(
                event_id,
                title,
                description,
                event_type,
                {
                    "categories": [cat["c"] for cat in categories],
                    "tags": [tag["t"] for tag in tags],
                    "events": [evt["e"] for evt in events],
                    "notes": [note["n"] for note in notes]
                }
            )
            
            # 创建关系边
            self._create_event_relations(event_id, relations)
            
            log.info(f"Global relation analysis completed for event: {event_id}")
        
        except Exception as e:
            log.error(f"Error in global relation analysis: {e}")
    
    def _create_event_relations(self, event_id: int, relations: List[Dict]):
        """创建事件关系边"""
        for relation in relations:
            rel_type = relation.get("type")
            target_id = relation.get("target_id")
            target_type = relation.get("target_type")
            weight = relation.get("weight", 0.5)
            reason = relation.get("reason", "")
            
            if rel_type == "category":
                query = """
                MATCH (e:Event {id: $eventId})
                MATCH (c:Category {id: $targetId})
                MERGE (e)-[:BELONGS_TO {weight: $weight}]->(c)
                """
            elif rel_type == "tag":
                query = """
                MATCH (e:Event {id: $eventId})
                MATCH (t:Tag {id: $targetId})
                MERGE (e)-[:TAGGED_WITH {confidence: $weight, auto_generated: true}]->(t)
                """
            elif rel_type == "event":
                query = """
                MATCH (e1:Event {id: $eventId})
                MATCH (e2:Event {id: $targetId})
                MERGE (e1)-[:RELATED_TO {weight: $weight, reason: $reason}]->(e2)
                """
            elif rel_type == "note":
                query = """
                MATCH (e:Event {id: $eventId})
                MATCH (n:Note {id: $targetId})
                MERGE (e)-[:RELATED_TO {weight: $weight, reason: $reason}]->(n)
                """
            else:
                continue
            
            neo4j_db.run(query, {
                "eventId": event_id,
                "targetId": target_id,
                "weight": weight,
                "reason": reason
            })
    
    def create_note(
        self,
        user_id: int,
        content: str,
        title: Optional[str] = None,
        source: str = "text",
        audio_url: Optional[str] = None
    ) -> Dict:
        """
        创建速记
        
        Args:
            user_id: 用户ID
            content: 速记内容
            title: 速记标题
            source: 来源类型（text, audio, image）
            audio_url: 音频URL
        
        Returns:
            速记信息字典
        """
        try:
            # 1. 保存速记到MySQL
            with mysql_db.get_session() as session:
                from app.models.note import Note
                note = Note(
                    user_id=user_id,
                    title=title,
                    content=content,
                    source=source,
                    audio_url=audio_url
                )
                session.add(note)
                session.flush()
                
                note_id = note.id
                log.info(f"Note created in MySQL: {note_id}")
            
            # 2. 在Neo4j中创建Note节点
            self._create_neo4j_note(note_id, user_id, title, content, source)
            
            # 3. 调用LangChain Agent进行增量关联分析
            self._incremental_relation_analysis(note_id, user_id, content)
            
            return {
                "note_id": note_id,
                "user_id": user_id,
                "title": title,
                "content": content,
                "source": source,
                "audio_url": audio_url
            }
        
        except Exception as e:
            log.error(f"Error creating note: {e}")
            raise
    
    def _create_neo4j_note(
        self,
        note_id: int,
        user_id: int,
        title: Optional[str],
        content: str,
        source: str
    ):
        """在Neo4j中创建速记节点"""
        query = """
        MATCH (u:User {id: $userId})
        CREATE (n:Note {
            id: $noteId,
            user_id: $userId,
            title: $title,
            content: $content,
            source: $source,
            created_at: datetime()
        })
        CREATE (u)-[:CREATED]->(n)
        """
        neo4j_db.run(query, {
            "noteId": note_id,
            "userId": user_id,
            "title": title,
            "content": content,
            "source": source
        })
        log.info(f"Neo4j note node created: {note_id}")
    
    def _incremental_relation_analysis(self, note_id: int, user_id: int, content: str):
        """增量关联分析"""
        try:
            # 从缓存读取用户关系图谱
            cache_key = f"user:{user_id}:relationships"
            cached_graph = redis_db.get(cache_key)
            
            if cached_graph:
                user_graph = json.loads(cached_graph)
            else:
                # 从Neo4j查询用户关系图谱
                user_graph = self._get_user_graph(user_id)
                redis_db.set(cache_key, json.dumps(user_graph), ttl=3600)
            
            # 调用Agent分析关联
            relations = self.relation_agent.analyze_note_relations(
                note_id,
                content,
                user_graph
            )
            
            # 生成智能标签
            tags = self.tag_agent.generate_tags(content, user_graph.get("tags", []))
            
            # 创建关系和标签
            self._create_note_relations(note_id, relations)
            self._create_note_tags(note_id, tags)
            
            # 清除缓存
            redis_db.delete(cache_key)
            
            log.info(f"Incremental relation analysis completed for note: {note_id}")
        
        except Exception as e:
            log.error(f"Error in incremental relation analysis: {e}")
    
    def _get_user_graph(self, user_id: int) -> Dict:
        """获取用户关系图谱"""
        query = """
        MATCH (u:User {id: $userId})-[r*1..2]-(n)
        WHERE n:Category OR n:Tag OR n:Event OR n:Note
        RETURN DISTINCT labels(n)[0] as type, n, type(r), properties(r)
        LIMIT 100
        """
        results = neo4j_db.run(query, {"userId": user_id})
        
        graph = {
            "categories": [],
            "tags": [],
            "events": [],
            "notes": []
        }
        
        for result in results:
            node_type = result["type"]
            node = result["n"]
            
            if node_type == "Category":
                graph["categories"].append(node)
            elif node_type == "Tag":
                graph["tags"].append(node)
            elif node_type == "Event":
                graph["events"].append(node)
            elif node_type == "Note":
                graph["notes"].append(node)
        
        return graph
    
    def _create_note_relations(self, note_id: int, relations: List[Dict]):
        """创建速记关系边"""
        for relation in relations:
            rel_type = relation.get("type")
            target_id = relation.get("target_id")
            target_type = relation.get("target_type")
            weight = relation.get("weight", 0.5)
            reason = relation.get("reason", "")
            
            if rel_type == "category":
                query = """
                MATCH (n:Note {id: $noteId})
                MATCH (c:Category {id: $targetId})
                MERGE (n)-[:BELONGS_TO {weight: $weight}]->(c)
                """
            elif rel_type == "event":
                query = """
                MATCH (n:Note {id: $noteId})
                MATCH (e:Event {id: $targetId})
                MERGE (n)-[:RELATED_TO {weight: $weight, reason: $reason}]->(e)
                """
            elif rel_type == "note":
                query = """
                MATCH (n1:Note {id: $noteId})
                MATCH (n2:Note {id: $targetId})
                MERGE (n1)-[:RELATED_TO {weight: $weight, reason: $reason}]->(n2)
                """
            else:
                continue
            
            neo4j_db.run(query, {
                "noteId": note_id,
                "targetId": target_id,
                "weight": weight,
                "reason": reason
            })
    
    def _create_note_tags(self, note_id: int, tags: List[str]):
        """创建速记标签"""
        for tag_name in tags:
            # 检查标签是否存在
            query = """
            MERGE (t:Tag {name: $tagName})
            ON CREATE SET t.id = id(t), t.created_at = datetime()
            RETURN t
            """
            result = neo4j_db.run_single(query, {"tagName": tag_name})
            tag = result["t"]
            
            # 创建关系
            query = """
            MATCH (n:Note {id: $noteId})
            MATCH (t:Tag {name: $tagName})
            MERGE (n)-[:TAGGED_WITH {confidence: 0.95, auto_generated: true}]->(t)
            """
            neo4j_db.run(query, {"noteId": note_id, "tagName": tag_name})
    
    def get_note_by_id(self, note_id: int, user_id: int) -> Optional[Dict]:
        """根据ID获取速记详情"""
        try:
            # 从MySQL获取基础信息
            with mysql_db.get_session() as session:
                from app.models.note import Note
                note = session.query(Note).filter(
                    Note.id == note_id,
                    Note.user_id == user_id
                ).first()
                if not note:
                    return None
                
                # 从Neo4j获取关联信息
                query = """
                MATCH (n:Note {id: $noteId})
                OPTIONAL MATCH (n)-[r:RELATED_TO|:TAGGED_WITH|:BELONGS_TO]-(related)
                RETURN n, collect(DISTINCT {
                    id: related.id,
                    type: labels(related)[0],
                    name: related.name,
                    title: related.title,
                    relation_type: type(r),
                    weight: r.weight
                }) as relations
                """
                result = neo4j_db.run_single(query, {"noteId": note_id})
                
                return {
                    "id": note.id,
                    "user_id": note.user_id,
                    "title": note.title,
                    "content": note.content,
                    "source": note.source,
                    "audio_url": note.audio_url,
                    "created_at": note.created_at.isoformat(),
                    "relations": result["relations"] if result else []
                }
        
        except Exception as e:
            log.error(f"Error getting note: {e}")
            return None


# 全局速记服务实例
note_service = NoteService()
