"""
关联分析Agent
使用LLM分析文本内容，识别实体之间的关联关系
"""
from typing import List, Dict, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config.logging_config import log
from app.config.settings import settings


class EntityRelation(BaseModel):
    """实体关联模型"""
    source_entity: str = Field(description="源实体名称")
    target_entity: str = Field(description="目标实体名称")
    relation_type: str = Field(description="关联类型：related_to, part_of, caused_by, similar_to, contains")
    confidence: float = Field(description="置信度，0-1之间的浮点数")
    description: str = Field(description="关联描述")


class RelationAnalysisResult(BaseModel):
    """关联分析结果模型"""
    relations: List[EntityRelation] = Field(description="识别到的关联关系列表")
    summary: str = Field(description="关联分析摘要")


class RelationAnalysisAgent:
    """关联分析Agent类"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,
            api_key=settings.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=RelationAnalysisResult)
        
        # 关联类型定义
        self.relation_types = {
            "related_to": "相关",
            "part_of": "属于",
            "caused_by": "由...导致",
            "similar_to": "相似",
            "contains": "包含"
        }
        
        # 全局关联分析提示词
        self.global_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能关联分析助手，负责分析多个文本之间的关联关系。

关联类型说明：
- related_to: 两个实体之间存在一般性关联
- part_of: 一个实体是另一个实体的一部分
- caused_by: 一个实体由另一个实体导致
- similar_to: 两个实体在内容或主题上相似
- contains: 一个实体包含另一个实体

分析规则：
1. 识别文本中提到的关键实体（人名、地名、事件、概念等）
2. 分析实体之间的语义关联
3. 只保留置信度大于0.6的关联
4. 每个关联关系需要清晰的描述

请根据提供的多个文本，分析它们之间的关联关系。

{format_instructions}"""),
            ("user", "文本列表：\n{texts}")
        ])
        
        # 增量关联分析提示词
        self.incremental_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能增量关联分析助手，负责分析新文本与现有知识图谱之间的关联关系。

关联类型说明：
- related_to: 两个实体之间存在一般性关联
- part_of: 一个实体是另一个实体的一部分
- caused_by: 一个实体由另一个实体导致
- similar_to: 两个实体在内容或主题上相似
- contains: 一个实体包含另一个实体

分析规则：
1. 识别新文本中的关键实体
2. 将新实体与现有实体进行匹配和关联
3. 只保留置信度大于0.6的关联
4. 重点关注新实体与现有实体之间的关联

请根据新文本和现有实体列表，分析它们之间的关联关系。

{format_instructions}"""),
            ("user", "新文本：{new_text}\n\n现有实体列表：{existing_entities}")
        ])
    
    def global_analysis(
        self,
        texts: List[Dict[str, any]]
    ) -> RelationAnalysisResult:
        """
        全局关联分析
        
        Args:
            texts: 文本列表，每个元素包含id和content
        
        Returns:
            关联分析结果
        """
        try:
            # 格式化文本列表
            formatted_texts = "\n".join([
                f"[{t['id']}] {t['content'][:200]}..."
                for t in texts
            ])
            
            # 构建提示词
            prompt_value = self.global_prompt.format_prompt(
                texts=formatted_texts,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # 调用LLM
            response = self.llm.invoke(prompt_value.to_messages())
            
            # 解析结果
            result = self.parser.parse(response.content)
            
            log.info(f"Global analysis found {len(result.relations)} relations")
            return result
        
        except Exception as e:
            log.error(f"Error in global analysis: {e}")
            return RelationAnalysisResult(
                relations=[],
                summary="全局关联分析时出错"
            )
    
    def incremental_analysis(
        self,
        new_text: str,
        existing_entities: List[Dict[str, any]]
    ) -> RelationAnalysisResult:
        """
        增量关联分析
        
        Args:
            new_text: 新文本内容
            existing_entities: 现有实体列表，每个元素包含id和name
        
        Returns:
            关联分析结果
        """
        try:
            # 格式化现有实体列表
            formatted_entities = "\n".join([
                f"[{e['id']}] {e['name']}"
                for e in existing_entities
            ])
            
            # 限制新文本长度
            if len(new_text) > 500:
                new_text = new_text[:500] + "..."
            
            # 构建提示词
            prompt_value = self.incremental_prompt.format_prompt(
                new_text=new_text,
                existing_entities=formatted_entities,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # 调用LLM
            response = self.llm.invoke(prompt_value.to_messages())
            
            # 解析结果
            result = self.parser.parse(response.content)
            
            log.info(f"Incremental analysis found {len(result.relations)} relations")
            return result
        
        except Exception as e:
            log.error(f"Error in incremental analysis: {e}")
            return RelationAnalysisResult(
                relations=[],
                summary="增量关联分析时出错"
            )
    
    def analyze_entity_similarity(
        self,
        entity1: str,
        entity2: str
    ) -> float:
        """
        分析实体相似度
        
        Args:
            entity1: 实体1名称
            entity2: 实体2名称
        
        Returns:
            相似度分数，0-1之间的浮点数
        """
        try:
            # 简单的字符串相似度计算
            if entity1.lower() == entity2.lower():
                return 1.0
            elif entity1.lower() in entity2.lower() or entity2.lower() in entity1.lower():
                return 0.8
            else:
                # 使用LLM进行语义相似度分析
                prompt = f"请判断以下两个实体的语义相似度（0-1之间的浮点数）：\n实体1：{entity1}\n实体2：{entity2}\n\n只输出数字，不要其他内容。"
                response = self.llm.invoke(prompt)
                try:
                    similarity = float(response.content.strip())
                    return max(0.0, min(1.0, similarity))
                except:
                    return 0.0
        
        except Exception as e:
            log.error(f"Error analyzing entity similarity: {e}")
            return 0.0
    
    def extract_entities(self, text: str) -> List[str]:
        """
        从文本中提取实体
        
        Args:
            text: 文本内容
        
        Returns:
            实体列表
        """
        try:
            # 使用LLM提取实体
            prompt = f"""请从以下文本中提取关键实体（人名、地名、事件、概念等），每行一个实体：
{text}

只输出实体列表，不要其他内容。"""
            response = self.llm.invoke(prompt)
            
            entities = [
                line.strip()
                for line in response.content.strip().split('\n')
                if line.strip()
            ]
            
            return entities
        
        except Exception as e:
            log.error(f"Error extracting entities: {e}")
            return []
    
    def calculate_relation_weight(
        self,
        relation_type: str,
        confidence: float,
        text_similarity: float = 0.0
    ) -> float:
        """
        计算关系权重
        
        Args:
            relation_type: 关联类型
            confidence: 置信度
            text_similarity: 文本相似度
        
        Returns:
            关系权重
        """
        # 基础权重
        base_weight = confidence
        
        # 根据关联类型调整权重
        type_weight = {
            "related_to": 1.0,
            "part_of": 1.2,
            "caused_by": 1.3,
            "similar_to": 0.9,
            "contains": 1.1
        }.get(relation_type, 1.0)
        
        # 综合计算
        final_weight = base_weight * type_weight
        
        # 如果有文本相似度，综合考虑
        if text_similarity > 0:
            final_weight = (final_weight + text_similarity) / 2
        
        return round(final_weight, 2)


# 全局关联分析Agent实例
relation_agent = RelationAnalysisAgent()
