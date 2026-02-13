"""
数据库连接配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from neo4j import GraphDatabase
import redis
from typing import Optional
from contextlib import contextmanager

from app.config.settings import settings
from app.config.logging_config import log


# ============================================
# MySQL 连接配置
# ============================================

class MySQLConnection:
    """MySQL数据库连接管理"""
    
    def __init__(self):
        self.engine = create_engine(
            settings.mysql_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.app_debug
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log.error(f"MySQL session error: {e}")
            raise
        finally:
            session.close()
    
    def get_db(self):
        """FastAPI依赖注入使用"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# ============================================
# Neo4j 连接配置
# ============================================

class Neo4jConnection:
    """Neo4j图数据库连接管理"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self.database = settings.neo4j_database
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    @contextmanager
    def session(self):
        """获取Neo4j会话"""
        session = self.driver.session(database=self.database)
        try:
            yield session
        except Exception as e:
            log.error(f"Neo4j session error: {e}")
            raise
        finally:
            session.close()
    
    def run(self, query: str, parameters: Optional[dict] = None):
        """执行Cypher查询"""
        with self.session() as session:
            result = session.run(query, parameters or {})
            return result.data()
    
    def run_single(self, query: str, parameters: Optional[dict] = None):
        """执行Cypher查询并返回单条结果"""
        with self.session() as session:
            result = session.run(query, parameters or {})
            return result.single()


# ============================================
# Redis 连接配置
# ============================================

class RedisConnection:
    """Redis缓存连接管理"""
    
    def __init__(self):
        self.client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5
        )
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        try:
            return self.client.get(key)
        except Exception as e:
            log.error(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None):
        """设置缓存"""
        try:
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
        except Exception as e:
            log.error(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            self.client.delete(key)
        except Exception as e:
            log.error(f"Redis delete error: {e}")
    
    def delete_pattern(self, pattern: str):
        """删除匹配模式的缓存"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            log.error(f"Redis delete_pattern error: {e}")
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            log.error(f"Redis exists error: {e}")
            return False


# ============================================
# 全局数据库连接实例
# ============================================

mysql_db = MySQLConnection()
neo4j_db = Neo4jConnection()
redis_db = RedisConnection()


# ============================================
# 数据库初始化函数
# ============================================

def init_databases():
    """初始化数据库连接"""
    try:
        # 测试MySQL连接
        with mysql_db.get_session() as session:
            session.execute("SELECT 1")
        log.info("MySQL connection initialized successfully")
        
        # 测试Neo4j连接
        neo4j_db.run("RETURN 1")
        log.info("Neo4j connection initialized successfully")
        
        # 测试Redis连接
        redis_db.client.ping()
        log.info("Redis connection initialized successfully")
        
        return True
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        return False


def close_databases():
    """关闭所有数据库连接"""
    try:
        neo4j_db.close()
        redis_db.client.close()
        mysql_db.engine.dispose()
        log.info("All database connections closed")
    except Exception as e:
        log.error(f"Error closing databases: {e}")
