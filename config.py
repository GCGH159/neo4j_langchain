"""
配置模块 - 从环境变量加载配置
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """应用配置"""
    
    # Neo4j 配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # LLM 配置 (SiliconFlow)
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1/")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3.1-Terminus")
    
    @classmethod
    def validate(cls) -> list[str]:
        """验证配置，返回缺失的配置项列表"""
        missing = []
        if not cls.LLM_API_KEY:
            missing.append("LLM_API_KEY")
        if not cls.NEO4J_PASSWORD or cls.NEO4J_PASSWORD == "your-password":
            missing.append("NEO4J_PASSWORD")
        return missing


config = Config()
