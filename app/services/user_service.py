"""
用户注册服务
"""
from typing import Optional, List, Dict
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import json

from app.config.database import mysql_db, neo4j_db, redis_db
from app.config.logging_config import log
from app.agents.category_agent import CategoryAgent


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.category_agent = CategoryAgent()
    
    def hash_password(self, password: str) -> str:
        """密码加密"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        category_level_1: Optional[str] = None,
        category_level_2: Optional[List[str]] = None
    ) -> Dict:
        """
        创建用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            category_level_1: 一级分类
            category_level_2: 二级分类列表
        
        Returns:
            用户信息字典
        """
        try:
            # 1. 保存用户信息到MySQL
            with mysql_db.get_session() as session:
                # 检查用户名和邮箱是否已存在
                from app.models.user import User
                existing_user = session.query(User).filter(
                    (User.username == username) | (User.email == email)
                ).first()
                
                if existing_user:
                    raise ValueError("用户名或邮箱已存在")
                
                # 创建用户
                user = User(
                    username=username,
                    email=email,
                    password_hash=self.hash_password(password)
                )
                session.add(user)
                session.flush()
                
                user_id = user.id
                log.info(f"User created in MySQL: {user_id}")
                
                # 2. 保存用户偏好到MySQL
                if category_level_1:
                    from app.models.user import UserPreference
                    preference = UserPreference(
                        user_id=user_id,
                        category_level_1=category_level_1,
                        category_level_2=json.dumps(category_level_2) if category_level_2 else None
                    )
                    session.add(preference)
                    session.flush()
                    log.info(f"User preference saved: {user_id}")
            
            # 3. 在Neo4j中创建用户节点
            self._create_neo4j_user(user_id, username)
            
            # 4. 创建分类节点和关系
            if category_level_1:
                self._create_category_relations(user_id, category_level_1, category_level_2)
            
            # 5. 初始化Redis用户缓存
            self._init_user_cache(user_id, username, email)
            
            return {
                "user_id": user_id,
                "username": username,
                "email": email,
                "category_level_1": category_level_1,
                "category_level_2": category_level_2
            }
        
        except Exception as e:
            log.error(f"Error creating user: {e}")
            raise
    
    def _create_neo4j_user(self, user_id: int, username: str):
        """在Neo4j中创建用户节点"""
        query = """
        MERGE (u:User {id: $userId})
        SET u.username = $username,
            u.created_at = datetime()
        """
        neo4j_db.run(query, {"userId": user_id, "username": username})
        log.info(f"Neo4j user node created: {user_id}")
    
    def _create_category_relations(
        self,
        user_id: int,
        category_level_1: str,
        category_level_2: Optional[List[str]]
    ):
        """创建分类节点和用户-分类关系"""
        # 创建一级分类节点
        query = """
        MERGE (c1:Category {name: $categoryName, level: 1})
        ON CREATE SET c1.id = id(c1), c1.created_at = datetime()
        """
        neo4j_db.run(query, {"categoryName": category_level_1})
        
        # 创建用户-一级分类关系
        query = """
        MATCH (u:User {id: $userId})
        MATCH (c1:Category {name: $categoryName, level: 1})
        MERGE (u)-[:PREFERS {weight: 1.0}]->(c1)
        """
        neo4j_db.run(query, {"userId": user_id, "categoryName": category_level_1})
        
        # 创建二级分类节点和关系
        if category_level_2:
            for sub_category in category_level_2:
                # 创建二级分类节点
                query = """
                MERGE (c2:Category {name: $subCategoryName, level: 2})
                ON CREATE SET c2.id = id(c2), c2.created_at = datetime()
                """
                neo4j_db.run(query, {"subCategoryName": sub_category})
                
                # 创建二级分类-一级分类关系
                query = """
                MATCH (c1:Category {name: $categoryName, level: 1})
                MATCH (c2:Category {name: $subCategoryName, level: 2})
                MERGE (c2)-[:BELONGS_TO]->(c1)
                """
                neo4j_db.run(query, {
                    "categoryName": category_level_1,
                    "subCategoryName": sub_category
                })
                
                # 创建用户-二级分类关系
                query = """
                MATCH (u:User {id: $userId})
                MATCH (c2:Category {name: $subCategoryName, level: 2})
                MERGE (u)-[:PREFERS {weight: 0.8}]->(c2)
                """
                neo4j_db.run(query, {"userId": user_id, "subCategoryName": sub_category})
        
        log.info(f"Category relations created for user: {user_id}")
    
    def _init_user_cache(self, user_id: int, username: str, email: str):
        """初始化Redis用户缓存"""
        user_info = {
            "user_id": user_id,
            "username": username,
            "email": email
        }
        redis_db.set(
            f"user:{user_id}:info",
            json.dumps(user_info),
            ttl=86400  # 24小时
        )
        log.info(f"User cache initialized: {user_id}")
    
    def generate_categories(self, category_level_1: str) -> List[str]:
        """
        生成二级分类
        
        Args:
            category_level_1: 一级分类
        
        Returns:
            二级分类列表
        """
        try:
            categories = self.category_agent.generate_sub_categories(category_level_1)
            log.info(f"Generated sub-categories for {category_level_1}: {categories}")
            return categories
        except Exception as e:
            log.error(f"Error generating categories: {e}")
            # 返回默认分类
            return [f"{category_level_1}-默认1", f"{category_level_1}-默认2"]
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户信息"""
        try:
            # 先从缓存获取
            cached = redis_db.get(f"user:{user_id}:info")
            if cached:
                return json.loads(cached)
            
            # 从MySQL获取
            with mysql_db.get_session() as session:
                from app.models.user import User
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    return {
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at.isoformat()
                    }
                return None
        except Exception as e:
            log.error(f"Error getting user: {e}")
            return None
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict]:
        """获取用户偏好"""
        try:
            with mysql_db.get_session() as session:
                from app.models.user import UserPreference
                preference = session.query(UserPreference).filter(
                    UserPreference.user_id == user_id
                ).first()
                if preference:
                    return {
                        "user_id": preference.user_id,
                        "category_level_1": preference.category_level_1,
                        "category_level_2": json.loads(preference.category_level_2) if preference.category_level_2 else []
                    }
                return None
        except Exception as e:
            log.error(f"Error getting user preferences: {e}")
            return None


# 全局用户服务实例
user_service = UserService()
