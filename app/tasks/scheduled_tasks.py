"""
定时任务模块
包含关系权重更新、数据同步、统计分析、数据清理等定时任务
"""
from typing import Optional
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.config.database import mysql_db, neo4j_db, redis_db
from app.agents.relation_agent import relation_agent
from app.config.logging_config import log
from app.config.settings import settings


class ScheduledTasks:
    """定时任务管理类"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    
    def start(self):
        """启动定时任务调度器"""
        try:
            # 添加定时任务
            self._add_relation_weight_update_task()
            self._add_data_sync_task()
            self._add_statistics_task()
            self._add_data_cleanup_task()
            
            # 启动调度器
            self.scheduler.start()
            log.info("Scheduled tasks started successfully")
        
        except Exception as e:
            log.error(f"Error starting scheduled tasks: {e}")
    
    def stop(self):
        """停止定时任务调度器"""
        try:
            self.scheduler.shutdown()
            log.info("Scheduled tasks stopped successfully")
        
        except Exception as e:
            log.error(f"Error stopping scheduled tasks: {e}")
    
    def _add_relation_weight_update_task(self):
        """添加关系权重更新任务"""
        try:
            # 每小时执行一次
            self.scheduler.add_job(
                self.update_relation_weights,
                trigger=IntervalTrigger(hours=1),
                id="relation_weight_update",
                name="关系权重更新任务",
                replace_existing=True
            )
            log.info("Relation weight update task added")
        
        except Exception as e:
            log.error(f"Error adding relation weight update task: {e}")
    
    def _add_data_sync_task(self):
        """添加数据同步任务"""
        try:
            # 每30分钟执行一次
            self.scheduler.add_job(
                self.sync_data,
                trigger=IntervalTrigger(minutes=30),
                id="data_sync",
                name="数据同步任务",
                replace_existing=True
            )
            log.info("Data sync task added")
        
        except Exception as e:
            log.error(f"Error adding data sync task: {e}")
    
    def _add_statistics_task(self):
        """添加统计分析任务"""
        try:
            # 每天凌晨2点执行
            self.scheduler.add_job(
                self.generate_statistics,
                trigger=CronTrigger(hour=2, minute=0),
                id="statistics",
                name="统计分析任务",
                replace_existing=True
            )
            log.info("Statistics task added")
        
        except Exception as e:
            log.error(f"Error adding statistics task: {e}")
    
    def _add_data_cleanup_task(self):
        """添加数据清理任务"""
        try:
            # 每天凌晨3点执行
            self.scheduler.add_job(
                self.cleanup_data,
                trigger=CronTrigger(hour=3, minute=0),
                id="data_cleanup",
                name="数据清理任务",
                replace_existing=True
            )
            log.info("Data cleanup task added")
        
        except Exception as e:
            log.error(f"Error adding data cleanup task: {e}")
    
    async def update_relation_weights(self):
        """
        更新关系权重
        根据时间衰减和交互频率更新Neo4j中的关系权重
        """
        try:
            log.info("Starting relation weight update task")
            
            with neo4j_db.session() as session:
                # 更新所有关系的权重（基于时间衰减）
                cypher = """
                    MATCH ()-[r]->()
                    WHERE r.weight IS NOT NULL
                    SET r.weight = r.weight * 0.99
                    RETURN count(r) as updated_count
                """
                result = session.run(cypher)
                record = result.single()
                updated_count = record["updated_count"] if record else 0
                
                log.info(f"Updated {updated_count} relation weights")
            
            # 增强最近活跃的关系权重
            with neo4j_db.session() as session:
                cypher = """
                    MATCH (u:User)-[:HAS_NOTE]->(n:Note)
                    WHERE n.created_at > datetime() - duration('P7D')
                    MATCH (n)-[r:RELATED_TO]-(other:Note)
                    SET r.weight = r.weight + 0.1
                    RETURN count(r) as boosted_count
                """
                result = session.run(cypher)
                record = result.single()
                boosted_count = record["boosted_count"] if record else 0
                
                log.info(f"Boosted {boosted_count} recent relation weights")
            
            log.info("Relation weight update task completed")
        
        except Exception as e:
            log.error(f"Error in relation weight update task: {e}")
    
    async def sync_data(self):
        """
        数据同步任务
        同步MySQL和Neo4j之间的数据
        """
        try:
            log.info("Starting data sync task")
            
            # 同步用户数据
            await self._sync_users()
            
            # 同步分类数据
            await self._sync_categories()
            
            # 同步速记数据
            await self._sync_notes()
            
            # 同步事件数据
            await self._sync_events()
            
            log.info("Data sync task completed")
        
        except Exception as e:
            log.error(f"Error in data sync task: {e}")
    
    async def _sync_users(self):
        """同步用户数据"""
        try:
            # 从MySQL获取用户列表
            query_sql = """
                SELECT id, username, email, created_at
                FROM users
                WHERE is_deleted = 0
            """
            
            with mysql_db.session() as session:
                users = session.execute(query_sql).fetchall()
            
            # 同步到Neo4j
            with neo4j_db.session() as session:
                for user in users:
                    cypher = """
                        MERGE (u:User {id: $id})
                        SET u.username = $username,
                            u.email = $email,
                            u.created_at = datetime($created_at)
                    """
                    session.run(
                        cypher,
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        created_at=user.created_at.isoformat()
                    )
            
            log.info(f"Synced {len(users)} users")
        
        except Exception as e:
            log.error(f"Error syncing users: {e}")
    
    async def _sync_categories(self):
        """同步分类数据"""
        try:
            # 从MySQL获取分类列表
            query_sql = """
                SELECT id, user_id, name, parent_id, created_at
                FROM categories
                WHERE is_deleted = 0
            """
            
            with mysql_db.session() as session:
                categories = session.execute(query_sql).fetchall()
            
            # 同步到Neo4j
            with neo4j_db.session() as session:
                for category in categories:
                    cypher = """
                        MATCH (u:User {id: $user_id})
                        MERGE (c:Category {id: $id})
                        SET c.name = $name,
                            c.created_at = datetime($created_at)
                        MERGE (u)-[:HAS_CATEGORY]->(c)
                    """
                    session.run(
                        cypher,
                        id=category.id,
                        user_id=category.user_id,
                        name=category.name,
                        created_at=category.created_at.isoformat()
                    )
                    
                    # 如果有父分类，建立关系
                    if category.parent_id:
                        cypher = """
                            MATCH (c:Category {id: $id})
                            MATCH (p:Category {id: $parent_id})
                            MERGE (p)-[:HAS_SUBCATEGORY]->(c)
                        """
                        session.run(
                            cypher,
                            id=category.id,
                            parent_id=category.parent_id
                        )
            
            log.info(f"Synced {len(categories)} categories")
        
        except Exception as e:
            log.error(f"Error syncing categories: {e}")
    
    async def _sync_notes(self):
        """同步速记数据"""
        try:
            # 从MySQL获取速记列表
            query_sql = """
                SELECT id, user_id, category_id, content, created_at
                FROM notes
                WHERE is_deleted = 0
                LIMIT 1000
            """
            
            with mysql_db.session() as session:
                notes = session.execute(query_sql).fetchall()
            
            # 同步到Neo4j
            with neo4j_db.session() as session:
                for note in notes:
                    cypher = """
                        MATCH (u:User {id: $user_id})
                        MERGE (n:Note {id: $id})
                        SET n.content = $content,
                            n.created_at = datetime($created_at)
                        MERGE (u)-[:HAS_NOTE]->(n)
                    """
                    session.run(
                        cypher,
                        id=note.id,
                        user_id=note.user_id,
                        content=note.content[:500],  # 限制内容长度
                        created_at=note.created_at.isoformat()
                    )
                    
                    # 如果有分类，建立关系
                    if note.category_id:
                        cypher = """
                            MATCH (n:Note {id: $id})
                            MATCH (c:Category {id: $category_id})
                            MERGE (c)-[:HAS_NOTE]->(n)
                        """
                        session.run(
                            cypher,
                            id=note.id,
                            category_id=note.category_id
                        )
            
            log.info(f"Synced {len(notes)} notes")
        
        except Exception as e:
            log.error(f"Error syncing notes: {e}")
    
    async def _sync_events(self):
        """同步事件数据"""
        try:
            # 从MySQL获取事件列表
            query_sql = """
                SELECT id, user_id, category_id, title, description, event_date, created_at
                FROM events
                WHERE is_deleted = 0
                LIMIT 1000
            """
            
            with mysql_db.session() as session:
                events = session.execute(query_sql).fetchall()
            
            # 同步到Neo4j
            with neo4j_db.session() as session:
                for event in events:
                    cypher = """
                        MATCH (u:User {id: $user_id})
                        MERGE (e:Event {id: $id})
                        SET e.title = $title,
                            e.description = $description,
                            e.event_date = datetime($event_date),
                            e.created_at = datetime($created_at)
                        MERGE (u)-[:HAS_EVENT]->(e)
                    """
                    session.run(
                        cypher,
                        id=event.id,
                        user_id=event.user_id,
                        title=event.title,
                        description=event.description or "",
                        event_date=event.event_date.isoformat(),
                        created_at=event.created_at.isoformat()
                    )
                    
                    # 如果有分类，建立关系
                    if event.category_id:
                        cypher = """
                            MATCH (e:Event {id: $id})
                            MATCH (c:Category {id: $category_id})
                            MERGE (c)-[:HAS_EVENT]->(e)
                        """
                        session.run(
                            cypher,
                            id=event.id,
                            category_id=event.category_id
                        )
            
            log.info(f"Synced {len(events)} events")
        
        except Exception as e:
            log.error(f"Error syncing events: {e}")
    
    async def generate_statistics(self):
        """
        生成统计数据
        生成用户活动统计、分类统计等
        """
        try:
            log.info("Starting statistics generation task")
            
            # 生成用户活动统计
            await self._generate_user_statistics()
            
            # 生成分类统计
            await self._generate_category_statistics()
            
            # 生成标签统计
            await self._generate_tag_statistics()
            
            log.info("Statistics generation task completed")
        
        except Exception as e:
            log.error(f"Error in statistics generation task: {e}")
    
    async def _generate_user_statistics(self):
        """生成用户活动统计"""
        try:
            # 获取所有用户
            query_sql = """
                SELECT id FROM users WHERE is_deleted = 0
            """
            
            with mysql_db.session() as session:
                users = session.execute(query_sql).fetchall()
            
            for user in users:
                # 统计速记数量
                notes_count = session.execute(
                    "SELECT COUNT(*) as count FROM notes WHERE user_id = :user_id AND is_deleted = 0",
                    {"user_id": user.id}
                ).fetchone().count
                
                # 统计事件数量
                events_count = session.execute(
                    "SELECT COUNT(*) as count FROM events WHERE user_id = :user_id AND is_deleted = 0",
                    {"user_id": user.id}
                ).fetchone().count
                
                # 统计录音数量
                audios_count = session.execute(
                    "SELECT COUNT(*) as count FROM audio_recordings WHERE user_id = :user_id AND is_deleted = 0",
                    {"user_id": user.id}
                ).fetchone().count
                
                # 缓存统计数据
                cache_key = f"stats:user:{user.id}"
                stats = {
                    "notes_count": notes_count,
                    "events_count": events_count,
                    "audios_count": audios_count,
                    "updated_at": datetime.now().isoformat()
                }
                redis_db.set(cache_key, str(stats), ex=86400)  # 24小时过期
            
            log.info(f"Generated statistics for {len(users)} users")
        
        except Exception as e:
            log.error(f"Error generating user statistics: {e}")
    
    async def _generate_category_statistics(self):
        """生成分类统计"""
        try:
            # 获取所有分类
            query_sql = """
                SELECT id FROM categories WHERE is_deleted = 0
            """
            
            with mysql_db.session() as session:
                categories = session.execute(query_sql).fetchall()
            
            for category in categories:
                # 统计速记数量
                notes_count = session.execute(
                    "SELECT COUNT(*) as count FROM notes WHERE category_id = :category_id AND is_deleted = 0",
                    {"category_id": category.id}
                ).fetchone().count
                
                # 统计事件数量
                events_count = session.execute(
                    "SELECT COUNT(*) as count FROM events WHERE category_id = :category_id AND is_deleted = 0",
                    {"category_id": category.id}
                ).fetchone().count
                
                # 缓存统计数据
                cache_key = f"stats:category:{category.id}"
                stats = {
                    "notes_count": notes_count,
                    "events_count": events_count,
                    "updated_at": datetime.now().isoformat()
                }
                redis_db.set(cache_key, str(stats), ex=86400)
            
            log.info(f"Generated statistics for {len(categories)} categories")
        
        except Exception as e:
            log.error(f"Error generating category statistics: {e}")
    
    async def _generate_tag_statistics(self):
        """生成标签统计"""
        try:
            # 获取所有标签
            query_sql = """
                SELECT id FROM tags WHERE is_deleted = 0
            """
            
            with mysql_db.session() as session:
                tags = session.execute(query_sql).fetchall()
            
            for tag in tags:
                # 统计使用次数
                usage_count = session.execute(
                    "SELECT COUNT(*) as count FROM note_tags WHERE tag_id = :tag_id",
                    {"tag_id": tag.id}
                ).fetchone().count
                
                # 缓存统计数据
                cache_key = f"stats:tag:{tag.id}"
                stats = {
                    "usage_count": usage_count,
                    "updated_at": datetime.now().isoformat()
                }
                redis_db.set(cache_key, str(stats), ex=86400)
            
            log.info(f"Generated statistics for {len(tags)} tags")
        
        except Exception as e:
            log.error(f"Error generating tag statistics: {e}")
    
    async def cleanup_data(self):
        """
        数据清理任务
        清理过期数据、软删除数据等
        """
        try:
            log.info("Starting data cleanup task")
            
            # 清理软删除超过30天的数据
            await self._cleanup_deleted_data()
            
            # 清理过期的缓存
            await self._cleanup_expired_cache()
            
            # 清理低权重关系
            await self._cleanup_low_weight_relations()
            
            log.info("Data cleanup task completed")
        
        except Exception as e:
            log.error(f"Error in data cleanup task: {e}")
    
    async def _cleanup_deleted_data(self):
        """清理软删除超过30天的数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # 物理删除软删除的速记
            query_sql = """
                DELETE FROM notes
                WHERE is_deleted = 1 AND deleted_at < :cutoff_date
            """
            
            with mysql_db.session() as session:
                result = session.execute(query_sql, {"cutoff_date": cutoff_date})
                notes_deleted = result.rowcount
            
            # 物理删除软删除的事件
            query_sql = """
                DELETE FROM events
                WHERE is_deleted = 1 AND deleted_at < :cutoff_date
            """
            
            with mysql_db.session() as session:
                result = session.execute(query_sql, {"cutoff_date": cutoff_date})
                events_deleted = result.rowcount
            
            log.info(f"Cleaned up {notes_deleted} notes and {events_deleted} events")
        
        except Exception as e:
            log.error(f"Error cleaning up deleted data: {e}")
    
    async def _cleanup_expired_cache(self):
        """清理过期的缓存"""
        try:
            # Redis会自动清理过期键，这里不需要额外操作
            # 可以添加一些自定义的缓存清理逻辑
            log.info("Cache cleanup completed (Redis handles expiration automatically)")
        
        except Exception as e:
            log.error(f"Error cleaning up expired cache: {e}")
    
    async def _cleanup_low_weight_relations(self):
        """清理低权重关系"""
        try:
            with neo4j_db.session() as session:
                # 删除权重低于0.1的关系
                cypher = """
                    MATCH ()-[r]->()
                    WHERE r.weight < 0.1
                    DELETE r
                    RETURN count(r) as deleted_count
                """
                result = session.run(cypher)
                record = result.single()
                deleted_count = record["deleted_count"] if record else 0
                
                log.info(f"Cleaned up {deleted_count} low weight relations")
        
        except Exception as e:
            log.error(f"Error cleaning up low weight relations: {e}")


# 全局定时任务实例
scheduled_tasks = ScheduledTasks()
