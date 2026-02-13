"""
事件中心展示服务
提供事件聚合、分类展示、关系可视化等功能
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.config.database import mysql_db, neo4j_db, redis_db
from app.config.logging_config import log


class EventCenterService:
    """事件中心展示服务类"""
    
    def __init__(self):
        pass
    
    async def get_event_center(
        self,
        user_id: int,
        category_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取事件中心数据
        
        Args:
            user_id: 用户ID
            category_id: 分类ID（可选）
            tag_id: 标签ID（可选）
            limit: 返回结果数量限制
        
        Returns:
            事件中心数据字典
        """
        try:
            # 获取事件列表
            events = await self._get_events(
                user_id, category_id, tag_id, limit
            )
            
            # 获取相关速记
            notes = await self._get_related_notes(
                user_id, category_id, tag_id, limit
            )
            
            # 获取相关录音
            audios = await self._get_related_audios(
                user_id, category_id, tag_id, limit
            )
            
            # 获取分类统计
            category_stats = await self._get_category_statistics(user_id)
            
            # 获取标签统计
            tag_stats = await self._get_tag_statistics(user_id)
            
            return {
                "events": events,
                "notes": notes,
                "audios": audios,
                "category_statistics": category_stats,
                "tag_statistics": tag_stats,
                "total": len(events) + len(notes) + len(audios)
            }
        
        except Exception as e:
            log.error(f"Error getting event center: {e}")
            return {
                "events": [],
                "notes": [],
                "audios": [],
                "category_statistics": [],
                "tag_statistics": [],
                "total": 0
            }
    
    async def _get_events(
        self,
        user_id: int,
        category_id: Optional[int],
        tag_id: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        获取事件列表
        
        Args:
            user_id: 用户ID
            category_id: 分类ID
            tag_id: 标签ID
            limit: 返回结果数量限制
        
        Returns:
            事件列表
        """
        try:
            query_sql = """
                SELECT e.id, e.title, e.description, e.event_date, e.created_at,
                       c.id as category_id, c.name as category_name
                FROM events e
                LEFT JOIN categories c ON e.category_id = c.id
                WHERE e.user_id = :user_id
                AND e.is_deleted = 0
            """
            params = {"user_id": user_id}
            
            if category_id:
                query_sql += " AND e.category_id = :category_id"
                params["category_id"] = category_id
            
            if tag_id:
                query_sql += """
                    AND e.id IN (
                        SELECT event_id FROM event_tags WHERE tag_id = :tag_id
                    )
                """
                params["tag_id"] = tag_id
            
            query_sql += " ORDER BY e.event_date DESC LIMIT :limit"
            params["limit"] = limit
            
            with mysql_db.session() as session:
                events = session.execute(query_sql, params).fetchall()
                
                return [
                    {
                        "id": event.id,
                        "type": "event",
                        "title": event.title,
                        "description": event.description,
                        "event_date": event.event_date.isoformat(),
                        "created_at": event.created_at.isoformat(),
                        "category_id": event.category_id,
                        "category_name": event.category_name
                    }
                    for event in events
                ]
        
        except Exception as e:
            log.error(f"Error getting events: {e}")
            return []
    
    async def _get_related_notes(
        self,
        user_id: int,
        category_id: Optional[int],
        tag_id: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        获取相关速记
        
        Args:
            user_id: 用户ID
            category_id: 分类ID
            tag_id: 标签ID
            limit: 返回结果数量限制
        
        Returns:
            速记列表
        """
        try:
            query_sql = """
                SELECT n.id, n.content, n.created_at,
                       c.id as category_id, c.name as category_name
                FROM notes n
                LEFT JOIN categories c ON n.category_id = c.id
                WHERE n.user_id = :user_id
                AND n.is_deleted = 0
            """
            params = {"user_id": user_id}
            
            if category_id:
                query_sql += " AND n.category_id = :category_id"
                params["category_id"] = category_id
            
            if tag_id:
                query_sql += """
                    AND n.id IN (
                        SELECT note_id FROM note_tags WHERE tag_id = :tag_id
                    )
                """
                params["tag_id"] = tag_id
            
            query_sql += " ORDER BY n.created_at DESC LIMIT :limit"
            params["limit"] = limit
            
            with mysql_db.session() as session:
                notes = session.execute(query_sql, params).fetchall()
                
                return [
                    {
                        "id": note.id,
                        "type": "note",
                        "content": note.content[:200],
                        "created_at": note.created_at.isoformat(),
                        "category_id": note.category_id,
                        "category_name": note.category_name
                    }
                    for note in notes
                ]
        
        except Exception as e:
            log.error(f"Error getting related notes: {e}")
            return []
    
    async def _get_related_audios(
        self,
        user_id: int,
        category_id: Optional[int],
        tag_id: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        获取相关录音
        
        Args:
            user_id: 用户ID
            category_id: 分类ID
            tag_id: 标签ID
            limit: 返回结果数量限制
        
        Returns:
            录音列表
        """
        try:
            query_sql = """
                SELECT a.id, a.note_id, a.audio_url, a.duration, a.created_at,
                       n.content as note_content
                FROM audio_recordings a
                LEFT JOIN notes n ON a.note_id = n.id
                WHERE a.user_id = :user_id
                AND a.is_deleted = 0
            """
            params = {"user_id": user_id}
            
            if category_id:
                query_sql += " AND n.category_id = :category_id"
                params["category_id"] = category_id
            
            if tag_id:
                query_sql += """
                    AND n.id IN (
                        SELECT note_id FROM note_tags WHERE tag_id = :tag_id
                    )
                """
                params["tag_id"] = tag_id
            
            query_sql += " ORDER BY a.created_at DESC LIMIT :limit"
            params["limit"] = limit
            
            with mysql_db.session() as session:
                audios = session.execute(query_sql, params).fetchall()
                
                return [
                    {
                        "id": audio.id,
                        "type": "audio",
                        "note_id": audio.note_id,
                        "audio_url": audio.audio_url,
                        "duration": audio.duration,
                        "created_at": audio.created_at.isoformat(),
                        "note_content": audio.note_content[:100] if audio.note_content else None
                    }
                    for audio in audios
                ]
        
        except Exception as e:
            log.error(f"Error getting related audios: {e}")
            return []
    
    async def _get_category_statistics(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取分类统计
        
        Args:
            user_id: 用户ID
        
        Returns:
            分类统计列表
        """
        try:
            # 统计每个分类下的速记数量
            query_sql = """
                SELECT c.id, c.name, COUNT(n.id) as note_count
                FROM categories c
                LEFT JOIN notes n ON c.id = n.category_id AND n.is_deleted = 0
                WHERE c.user_id = :user_id
                AND c.is_deleted = 0
                GROUP BY c.id, c.name
                ORDER BY note_count DESC
            """
            
            with mysql_db.session() as session:
                results = session.execute(query_sql, {"user_id": user_id}).fetchall()
                
                return [
                    {
                        "category_id": result.id,
                        "category_name": result.name,
                        "note_count": result.note_count
                    }
                    for result in results
                ]
        
        except Exception as e:
            log.error(f"Error getting category statistics: {e}")
            return []
    
    async def _get_tag_statistics(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取标签统计
        
        Args:
            user_id: 用户ID
        
        Returns:
            标签统计列表
        """
        try:
            # 统计每个标签的使用次数
            query_sql = """
                SELECT t.id, t.name, COUNT(nt.note_id) as note_count
                FROM tags t
                LEFT JOIN note_tags nt ON t.id = nt.tag_id
                LEFT JOIN notes n ON nt.note_id = n.id
                WHERE t.user_id = :user_id
                AND t.is_deleted = 0
                AND (n.is_deleted = 0 OR n.is_deleted IS NULL)
                GROUP BY t.id, t.name
                ORDER BY note_count DESC
                LIMIT 20
            """
            
            with mysql_db.session() as session:
                results = session.execute(query_sql, {"user_id": user_id}).fetchall()
                
                return [
                    {
                        "tag_id": result.id,
                        "tag_name": result.name,
                        "note_count": result.note_count
                    }
                    for result in results
                ]
        
        except Exception as e:
            log.error(f"Error getting tag statistics: {e}")
            return []
    
    async def get_event_relations(
        self,
        user_id: int,
        event_id: int
    ) -> Dict[str, Any]:
        """
        获取事件关联关系
        
        Args:
            user_id: 用户ID
            event_id: 事件ID
        
        Returns:
            关联关系字典
        """
        try:
            relations = []
            
            with neo4j_db.session() as session:
                # 查找与该事件相关的其他事件
                cypher = """
                    MATCH (u:User {id: $user_id})-[:HAS_EVENT]->(e:Event {id: $event_id})
                    MATCH (e)-[r:RELATED_TO|SIMILAR_TO|CAUSED_BY]-(other:Event)
                    WHERE other.id <> $event_id
                    RETURN other.id as id, other.title as title, r.weight as weight, type(r) as relation_type
                    ORDER BY r.weight DESC
                    LIMIT 10
                """
                
                result = session.run(
                    cypher,
                    user_id=user_id,
                    event_id=event_id
                )
                
                for record in result:
                    relations.append({
                        "id": record["id"],
                        "title": record["title"],
                        "weight": record["weight"],
                        "relation_type": record["relation_type"]
                    })
            
            return {
                "event_id": event_id,
                "relations": relations,
                "total": len(relations)
            }
        
        except Exception as e:
            log.error(f"Error getting event relations: {e}")
            return {
                "event_id": event_id,
                "relations": [],
                "total": 0
            }
    
    async def get_event_timeline(
        self,
        user_id: int,
        event_id: int
    ) -> Dict[str, Any]:
        """
        获取事件时间轴（相关速记和录音）
        
        Args:
            user_id: 用户ID
            event_id: 事件ID
        
        Returns:
            时间轴数据字典
        """
        try:
            # 获取事件详情
            query_sql = """
                SELECT id, title, description, event_date, created_at
                FROM events
                WHERE id = :event_id AND user_id = :user_id AND is_deleted = 0
            """
            
            with mysql_db.session() as session:
                event = session.execute(
                    query_sql,
                    {"event_id": event_id, "user_id": user_id}
                ).fetchone()
                
                if not event:
                    return {
                        "event_id": event_id,
                        "event": None,
                        "timeline": []
                    }
            
            # 获取相关速记
            notes_query = """
                SELECT id, content, created_at
                FROM notes
                WHERE user_id = :user_id
                AND category_id = (SELECT category_id FROM events WHERE id = :event_id)
                AND is_deleted = 0
                AND created_at >= :start_date
                AND created_at <= :end_date
                ORDER BY created_at ASC
            """
            
            start_date = event.event_date - timedelta(days=7)
            end_date = event.event_date + timedelta(days=7)
            
            with mysql_db.session() as session:
                notes = session.execute(
                    notes_query,
                    {
                        "user_id": user_id,
                        "event_id": event_id,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                ).fetchall()
                
                timeline = [
                    {
                        "id": note.id,
                        "type": "note",
                        "content": note.content[:200],
                        "created_at": note.created_at.isoformat()
                    }
                    for note in notes
                ]
            
            # 添加事件本身
            timeline.append({
                "id": event.id,
                "type": "event",
                "title": event.title,
                "description": event.description,
                "created_at": event.created_at.isoformat()
            })
            
            # 按时间排序
            timeline.sort(key=lambda x: x["created_at"])
            
            return {
                "event_id": event_id,
                "event": {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "event_date": event.event_date.isoformat()
                },
                "timeline": timeline,
                "total": len(timeline)
            }
        
        except Exception as e:
            log.error(f"Error getting event timeline: {e}")
            return {
                "event_id": event_id,
                "event": None,
                "timeline": [],
                "total": 0
            }


# 全局事件中心服务实例
event_center_service = EventCenterService()
