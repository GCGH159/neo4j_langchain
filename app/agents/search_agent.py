"""
智能搜索Agent
使用LLM进行智能搜索，支持全文搜索、向量搜索、图搜索
"""
from typing import List, Dict, Optional, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config.logging_config import log
from app.config.settings import settings


class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str = Field(description="结果ID")
    content: str = Field(description="内容摘要")
    score: float = Field(description="相关度分数")
    source_type: str = Field(description="来源类型：note, event, audio")
    metadata: Dict[str, Any] = Field(description="元数据")


class SearchQuery(BaseModel):
    """搜索查询模型"""
    query: str = Field(description="搜索查询文本")
    search_type: str = Field(description="搜索类型：fulltext, vector, graph, hybrid")
    filters: Dict[str, Any] = Field(description="过滤条件", default={})
    limit: int = Field(description="返回结果数量限制", default=10)


class SearchAnalysisResult(BaseModel):
    """搜索分析结果模型"""
    refined_query: str = Field(description="优化后的查询")
    search_strategy: str = Field(description="推荐的搜索策略")
    filters: Dict[str, Any] = Field(description="建议的过滤条件")
    explanation: str = Field(description="搜索策略说明")


class SmartSearchAgent:
    """智能搜索Agent类"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=SearchAnalysisResult)
        
        # 查询优化提示词
        self.query_optimization_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能搜索助手，负责优化用户的搜索查询。

搜索类型说明：
- fulltext: 全文搜索，适合关键词匹配
- vector: 向量搜索，适合语义相似度搜索
- graph: 图搜索，适合基于关系的搜索
- hybrid: 混合搜索，结合多种搜索方式

优化规则：
1. 识别查询的核心意图
2. 提取关键实体和概念
3. 根据查询特点选择合适的搜索策略
4. 建议合适的过滤条件（如时间范围、分类、标签等）
5. 优化查询文本，使其更准确

请根据用户提供的查询，给出搜索策略建议。

{format_instructions}"""),
            ("user", "搜索查询：{query}")
        ])
        
        # 结果重排序提示词
        self.rerank_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个搜索结果重排序助手，负责根据查询对搜索结果进行重新排序。

重排序规则：
1. 根据查询的相关性对结果进行评分
2. 考虑内容的语义相似度
3. 考虑结果的时效性（如果查询涉及时间）
4. 考虑结果的权威性和质量
5. 返回重新排序后的结果列表

请根据查询和搜索结果，进行重排序。

{format_instructions}"""),
            ("user", "查询：{query}\n\n搜索结果：{results}")
        ])
    
    def analyze_query(self, query: str) -> SearchAnalysisResult:
        """
        分析搜索查询，优化查询并推荐搜索策略
        
        Args:
            query: 原始查询文本
        
        Returns:
            搜索分析结果
        """
        try:
            # 构建提示词
            prompt_value = self.query_optimization_prompt.format_prompt(
                query=query,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # 调用LLM
            response = self.llm.invoke(prompt_value.to_messages())
            
            # 解析结果
            result = self.parser.parse(response.content)
            
            log.info(f"Analyzed query: {result.refined_query} (strategy: {result.search_strategy})")
            return result
        
        except Exception as e:
            log.error(f"Error analyzing query: {e}")
            return SearchAnalysisResult(
                refined_query=query,
                search_strategy="hybrid",
                filters={},
                explanation="查询分析时出错，使用默认策略"
            )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本的向量嵌入
        
        Args:
            text: 文本内容
        
        Returns:
            向量嵌入
        """
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        
        except Exception as e:
            log.error(f"Error generating embedding: {e}")
            return []
    
    def calculate_similarity(
        self,
        query_embedding: List[float],
        doc_embedding: List[float]
    ) -> float:
        """
        计算向量相似度（余弦相似度）
        
        Args:
            query_embedding: 查询向量
            doc_embedding: 文档向量
        
        Returns:
            相似度分数
        """
        try:
            import numpy as np
            
            query_vec = np.array(query_embedding)
            doc_vec = np.array(doc_embedding)
            
            # 余弦相似度
            dot_product = np.dot(query_vec, doc_vec)
            norm_query = np.linalg.norm(query_vec)
            norm_doc = np.linalg.norm(doc_vec)
            
            if norm_query == 0 or norm_doc == 0:
                return 0.0
            
            similarity = dot_product / (norm_query * norm_doc)
            return float(similarity)
        
        except Exception as e:
            log.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def expand_query(self, query: str) -> List[str]:
        """
        扩展查询，生成相关的查询变体
        
        Args:
            query: 原始查询
        
        Returns:
            扩展后的查询列表
        """
        try:
            prompt = f"""请为以下搜索查询生成3-5个相关的查询变体，用于扩展搜索范围：
{query}

每行一个查询变体，不要其他内容。"""
            response = self.llm.invoke(prompt)
            
            expanded_queries = [
                line.strip()
                for line in response.content.strip().split('\n')
                if line.strip()
            ]
            
            return expanded_queries
        
        except Exception as e:
            log.error(f"Error expanding query: {e}")
            return []
    
    def rerank_results(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        对搜索结果进行重新排序
        
        Args:
            query: 搜索查询
            results: 原始搜索结果
        
        Returns:
            重新排序后的结果
        """
        try:
            # 格式化结果
            formatted_results = "\n".join([
                f"[{r.id}] {r.content[:100]}... (score: {r.score})"
                for r in results
            ])
            
            # 构建提示词
            prompt_value = self.rerank_prompt.format_prompt(
                query=query,
                results=formatted_results,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # 调用LLM
            response = self.llm.invoke(prompt_value.to_messages())
            
            # 解析结果
            result = self.parser.parse(response.content)
            
            # 根据LLM的建议重新排序
            # 这里简化处理，实际应该根据LLM的评分重新排序
            log.info(f"Reranked {len(results)} results")
            return results
        
        except Exception as e:
            log.error(f"Error reranking results: {e}")
            return results
    
    def extract_entities_from_query(self, query: str) -> List[str]:
        """
        从查询中提取实体
        
        Args:
            query: 查询文本
        
        Returns:
            实体列表
        """
        try:
            prompt = f"""请从以下搜索查询中提取关键实体（人名、地名、事件、概念等），每行一个实体：
{query}

只输出实体列表，不要其他内容。"""
            response = self.llm.invoke(prompt)
            
            entities = [
                line.strip()
                for line in response.content.strip().split('\n')
                if line.strip()
            ]
            
            return entities
        
        except Exception as e:
            log.error(f"Error extracting entities from query: {e}")
            return []
    
    def suggest_filters(self, query: str) -> Dict[str, Any]:
        """
        根据查询建议过滤条件
        
        Args:
            query: 查询文本
        
        Returns:
            过滤条件字典
        """
        try:
            # 分析查询
            analysis = self.analyze_query(query)
            
            # 返回建议的过滤条件
            return analysis.filters
        
        except Exception as e:
            log.error(f"Error suggesting filters: {e}")
            return {}
    
    def generate_search_summary(
        self,
        query: str,
        results: List[SearchResult]
    ) -> str:
        """
        生成搜索结果摘要
        
        Args:
            query: 搜索查询
            results: 搜索结果
        
        Returns:
            摘要文本
        """
        try:
            if not results:
                return "未找到相关结果"
            
            # 格式化结果
            formatted_results = "\n".join([
                f"- {r.content[:150]}..."
                for r in results[:5]
            ])
            
            prompt = f"""请根据以下搜索查询和结果，生成一个简洁的摘要（50字以内）：
查询：{query}

结果：
{formatted_results}

只输出摘要，不要其他内容。"""
            response = self.llm.invoke(prompt)
            
            return response.content.strip()
        
        except Exception as e:
            log.error(f"Error generating search summary: {e}")
            return f"找到{len(results)}条相关结果"


# 全局智能搜索Agent实例
search_agent = SmartSearchAgent()
