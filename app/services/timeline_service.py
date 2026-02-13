"""
时间轴展示服务
提供按时间维度展示速记、事件、录音等功能
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.config.database import mysql_db, neo4j_db, redis_db
from app.config.logging_config import log


class TimelineService:
    """时间轴展示服务类"""
    
    def __init__(self):
        pass
    
    async def get_timeline(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取时间轴数据
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回结果数量限制
        
        Returns:
            时间轴数据字典
        """
        try:
            # 设置默认时间范围（最近30天）
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # 获取速记
            notes = await self._get_notes_by_date_range(
                user_id, start_date, end_date, limit
            )
            
            # 获取事件
            events = await self._get_events_by_date_range(
                user_id, start_date, end_date, limit
            )
            
            # 获取录音
            audios = await self._get_audios_by_date_range(
                user_id, start_date, end_date, limit
            )
            
            # 按日期分组
            timeline = self._group_by_date(notes, events, audios)
            
            # 按日期排序
            sorted_timeline = sorted(
                timeline.items(),
                key=lambda x: x[0],
                reverse=True
            )
            
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timeline": [
                    {
                        "date": date_str,
                        "items": items
                    }
                    for date_str, items in sorted_timeline
                ],
                "total": sum(len(items) for _, items in sorted_timeline)
            }
        
        except Exception as e:
            log.error(f"Error getting timeline: {e}")
            return {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "timeline": [],
                "total": 0
            }
    
    async def _get_notes_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        获取指定日期范围内的速记
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回结果数量限制
        
        Returns:
            速记列表
        """
        try:
            query_sql = """
                SELECT id, content, category_id, created_at, updated_at
                FROM notes
                WHERE user_id = :user_id
                AND created_at >= :start_date
                AND created_at <= :end_date
                AND is_deleted = 0
                ORDER BY created_at DESC
                LIMIT :limit
            """
            
            with mysql_db.session() as session:
                notes = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit
                    }
                ).fetchall()
                
                return [
                    {
                        "id": note.id,
                        "type": "note",
                        "content": note.content,
                        "category_id": note.category_id,
                        "created_at": note.created_at.isoformat(),
                        "updated_at": note.updated_at.isoformat()
                    }
                    for note in notes
                ]
        
        except Exception as e:
            log.error(f"Error getting notes by date range: {e}")
            return []
    
    async def _get_events_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        获取指定日期范围内的事件
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回结果数量限制
        
        Returns:
            事件列表
        """
        try:
            query_sql = """
                SELECT id, title, description, event_date, created_at
                FROM events
                WHERE user_id = :user_id
                AND event_date >= :start_date
                AND event_date <= :end_date
                AND is_deleted = 0
                ORDER BY event_date DESC
                LIMIT :limit
            """
            
            with mysql_db.session() as session:
                events = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit
                    }
                ).fetchall()
                
                return [
                    {
                        "id": event.id,
                        "type": "event",
                        "title": event.title,
                        "description": event.description,
                        "event_date": event.event_date.isoformat(),
                        "created_at": event.created_at.isoformat()
                    }
                    for event in events
                ]
        
        except Exception as e:
            log.error(f"Error getting events by date range: {e}")
            return []
    
    async def _get_audios_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        获取指定日期范围内的录音
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回结果数量限制
        
        Returns:
            录音列表
        """
        try:
            query_sql = """
                SELECT id, note_id, audio_url, duration, created_at
                FROM audio_recordings
                WHERE user_id = :user_id
                AND created_at >= :start_date
                AND created_at <= :end_date
                AND is_deleted = 0
                ORDER BY created_at DESC
                LIMIT :limit
            """
            
            with mysql_db.session() as session:
                audios = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit
                    }
                ).fetchall()
                
                return [
                    {
                        "id": audio.id,
                        "type": "audio",
                        "note_id": audio.note_id,
                        "audio_url": audio.audio_url,
                        "duration": audio.duration,
                        "created_at": audio.created_at.isoformat()
                    }
                    for audio in audios
                ]
        
        except Exception as e:
            log.error(f"Error getting audios by date range: {e}")
            return []
    
    def _group_by_date(
        self,
        notes: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        audios: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按日期分组
        
        Args:
            notes: 速记列表
            events: 事件列表
            audios: 录音列表
        
        Returns:
            按日期分组的数据字典
        """
        grouped = defaultdict(list)
        
        # 添加速记
        for note in notes:
            date_str = note["created_at"][:10]  # YYYY-MM-DD
            grouped[date_str].append(note)
        
        # 添加事件
        for event in events:
            date_str = event["event_date"][:10]
            grouped[date_str].append(event)
        
        # 添加录音
        for audio in audios:
            date_str = audio["created_at"][:10]
            grouped[date_str].append(audio)
        
        # 对每天的项目按时间排序
        for date_str in grouped:
            grouped[date_str].sort(
                key=lambda x: x.get("created_at") or x.get("event_date"),
                reverse=True
            )
        
        return grouped
    
    async def get_timeline_by_category(
        self,
        user_id: int,
        category_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        按分类获取时间轴数据
        
        Args:
            user_id: 用户ID
            category_id: 分类ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回结果数量限制
        
        Returns:
            时间轴数据字典
        """
        try:
            # 设置默认时间范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # 获取该分类下的速记
            query_sql = """
                SELECT id, content, category_id, created_at, updated_at
                FROM notes
                WHERE user_id = :user_id
                AND category_id = :category_id
                AND created_at >= :start_date
                AND created_at <= :end_date
                AND is_deleted = 0
                ORDER BY created_at DESC
                LIMIT :limit
            """
            
            with mysql_db.session() as session:
                notes = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "category_id": category_id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "limit": limit
                    }
                ).fetchall()
                
                notes_list = [
                    {
                        "id": note.id,
                        "type": "note",
                        "content": note.content,
                        "category_id": note.category_id,
                        "created_at": note.created_at.isoformat(),
                        "updated_at": note.updated_at.isoformat()
                    }
                    for note in notes
                ]
            
            # 按日期分组
            timeline = self._group_by_date(notes_list, [], [])
            
            # 按日期排序
            sorted_timeline = sorted(
                timeline.items(),
                key=lambda x: x[0],
                reverse=True
            )
            
            return {
                "category_id": category_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timeline": [
                    {
                        "date": date_str,
                        "items": items
                    }
                    for date_str, items in sorted_timeline
                ],
                "total": len(notes_list)
            }
        
        except Exception as e:
            log.error(f"Error getting timeline by category: {e}")
            return {
                "category_id": category_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "timeline": [],
                "total": 0
            }
    
    async def get_timeline_statistics(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取时间轴统计数据
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计数据字典
        """
        try:
            # 设置默认时间范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # 统计速记数量
            notes_count = await self._count_notes(user_id, start_date, end_date)
            
            # 统计事件数量
            events_count = await self._count_events(user_id, start_date, end_date)
            
            # 统计录音数量
            audios_count = await self._count_audios(user_id, start_date, end_date)
            
            # 统计每日活动
            daily_stats = await self._get_daily_statistics(
                user_id, start_date, end_date
            )
            
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "notes_count": notes_count,
                "events_count": events_count,
                "audios_count": audios_count,
                "total_count": notes_count + events_count + audios_count,
                "daily_statistics": daily_stats
            }
        
        except Exception as e:
            log.error(f"Error getting timeline statistics: {e}")
            return {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "notes_count": 0,
                "events_count": 0,
                "audios_count": 0,
                "total_count": 0,
                "daily_statistics": []
            }
    
    async def _count_notes(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """统计速记数量"""
        try:
            query_sql = """
                SELECT COUNT(*) as count
                FROM notes
                WHERE user_id = :user_id
                AND created_at >= :start_date
                AND created_at <= :end_date
                AND is_deleted = 0
            """
            
            with mysql_db.session() as session:
                result = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                ).fetchone()
                return result.count if result else 0
        
        except Exception as e:
            log.error(f"Error counting notes: {e}")
            return 0
    
    async def _count_events(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """统计事件数量"""
        try:
            query_sql = """
                SELECT COUNT(*) as count
                FROM events
                WHERE user_id = :user_id
                AND event_date >= :start_date
                AND event_date <= :end_date
                AND is_deleted = 0
            """
            
            with mysql_db.session() as session:
                result = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                ).fetchone()
                return result.count if result else 0
        
        except Exception as e:
            log.error(f"Error counting events: {e}")
            return 0
    
    async def _count_audios(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """统计录音数量"""
        try:
            query_sql = """
                SELECT COUNT(*) as count
                FROM audio_recordings
                WHERE user_id = :user_id
                AND created_at >= :start_date
                AND created_at <= :end_date
                AND is_deleted = 0
            """
            
            with mysql_db.session() as session:
                result = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                ).fetchone()
                return result.count if result else 0
        
        except Exception as e:
            log.error(f"Error counting audios: {e}")
            return 0
    
    async def _get_daily_statistics(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """获取每日统计数据"""
        try:
            # 获取每日速记数量
            query_sql = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM notes
                WHERE user_id = :user_id
                AND created_at >= :start_date
                AND created_at <= :end_date
                AND is_deleted = 0
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """
            
            with mysql_db.session() as session:
                results = session.execute(
                    query_sql,
                    {
                        "user_id": user_id,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                ).fetchall()
                
                return [
                    {
                        "date": result.date.isoformat(),
                        "notes_count": result.count
                    }
                    for result in results
                ]
        
        except Exception as e:
            log.error(f"Error getting daily statistics: {e}")
            return []


# 全局时间轴服务实例
timeline_service = TimelineService()
