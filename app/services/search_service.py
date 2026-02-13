"""
智能搜索服务
整合全文搜索、向量搜索和图搜索
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from app.config.database import mysql_db, neo4j_db, redis_db
from app.agents.search_agent import search_agent, SearchResult, SearchQuery
from app.config.logging_config import log


class SearchService:
    """智能搜索服务类"""
    
    def __init__(self):
        self.agent = search_agent
    
    async def search(
        self,
        user_id: int,
        query: str,
        search_type: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        执行智能搜索
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            search_type: 搜索类型 (fulltext, vector, graph, hybrid)
            filters: 过滤条件
            limit: 返回结果数量限制
        
        Returns:
            搜索结果字典
        """
        try:
            # 1. 分析查询
            analysis = self.agent.analyze_query(query)
            
            # 2. 根据分析结果选择搜索策略
            if search_type == "auto":
                search_type = analysis.search_strategy
            
            # 3. 合并过滤条件
            if filters is None:
                filters = {}
            filters.update(analysis.filters)
            
            # 4. 执行搜索
            results = []
            if search_type in ["fulltext", "hybrid"]:
                fulltext_results = await self._fulltext_search(
                    user_id, query, filters, limit
                )
                results.extend(fulltext_results)
            
            if search_type in ["vector", "hybrid"]:
                vector_results = await self._vector_search(
                    user_id, query, filters, limit
                )
                results.extend(vector_results)
            
            if search_type in ["graph", "hybrid"]:
                graph_results = await self._graph_search(
                    user_id, query, filters, limit
                )
                results.extend(graph_results)
            
            # 5. 去重和排序
            results = self._deduplicate_and_sort(results, limit)
            
            # 6. 生成摘要
            summary = self.agent.generate_search_summary(query, results)
            
            return {
                "query": query,
                "refined_query": analysis.refined_query,
                "search_type": search_type,
                "results": results,
                "total": len(results),
                "summary": summary
            }
        
        except Exception as e:
            log.error(f"Error in search: {e}")
            return {
                "query": query,
                "search_type": search_type,
                "results": [],
                "total": 0,
                "summary": "搜索时出错"
            }
    
    async def _fulltext_search(
        self,
        user_id: int,
        query: str,
        filters: Dict[str, Any],
        limit: int
    ) -> List[SearchResult]:
        """
        全文搜索
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            filters: 过滤条件
            limit: 返回结果数量限制
        
        Returns:
            搜索结果列表
        """
        try:
            results = []
            
            # 搜索速记
            query_sql = """
                SELECT id, content, created_at, 'note' as source_type
                FROM notes
                WHERE user_id = :user_id
                AND content LIKE :query
                AND is_deleted = 0
            """
            params = {
                "user_id": user_id,
                "query": f"%{query}%"
            }
            
            # 添加时间过滤
            if "start_date" in filters:
                query_sql += " AND created_at >= :start_date"
                params["start_date"] = filters["start_date"]
            if "end_date" in filters:
                query_sql += " AND created_at <= :end_date"
                params["end_date"] = filters["end_date"]
            
            # 添加分类过滤
            if "category_id" in filters:
                query_sql += " AND category_id = :category_id"
                params["category_id"] = filters["category_id"]
            
            query_sql += f" LIMIT {limit}"
            
            with mysql_db.session() as session:
                notes = session.execute(query_sql, params).fetchall()
                
                for note in notes:
                    results.append(SearchResult(
                        id=str(note.id),
                        content=note.content[:200],
                        score=0.8,  # 全文搜索基础分数
                        source_type=note.source_type,
                        metadata={
                            "created_at": note.created_at.isoformat(),
                            "type": "note"
                        }
                    ))
            
            # 搜索事件
            query_sql = """
                SELECT id, title, description, created_at, 'event' as source_type
                FROM events
                WHERE user_id = :user_id
                AND (title LIKE :query OR description LIKE :query)
                AND is_deleted = 0
            """
            params = {
                "user_id": user_id,
                "query": f"%{query}%"
            }
            
            query_sql += f" LIMIT {limit}"
            
            with mysql_db.session() as session:
                events = session.execute(query_sql, params).fetchall()
                
                for event in events:
                    content = f"{event.title}: {event.description}" if event.description else event.title
                    results.append(SearchResult(
                        id=str(event.id),
                        content=content[:200],
                        score=0.8,
                        source_type=event.source_type,
                        metadata={
                            "created_at": event.created_at.isoformat(),
                            "type": "event"
                        }
                    ))
            
            log.info(f"Fulltext search found {len(results)} results")
            return results
        
        except Exception as e:
            log.error(f"Error in fulltext search: {e}")
            return []
    
    async def _vector_search(
        self,
        user_id: int,
        query: str,
        filters: Dict[str, Any],
        limit: int
    ) -> List[SearchResult]:
        """
        向量搜索
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            filters: 过滤条件
            limit: 返回结果数量限制
        
        Returns:
            搜索结果列表
        """
        try:
            results = []
            
            # 生成查询向量
            query_embedding = self.agent.generate_embedding(query)
            if not query_embedding:
                return results
            
            # 从Redis获取缓存的向量
            cache_key = f"embeddings:user:{user_id}"
            cached_embeddings = redis_db.get(cache_key)
            
            if cached_embeddings:
                # 计算相似度
                import json
                embeddings = json.loads(cached_embeddings)
                
                for item in embeddings:
                    doc_embedding = item.get("embedding", [])
                    similarity = self.agent.calculate_similarity(
                        query_embedding,
                        doc_embedding
                    )
                    
                    if similarity > 0.6:  # 相似度阈值
                        results.append(SearchResult(
                            id=item["id"],
                            content=item["content"][:200],
                            score=similarity,
                            source_type=item["source_type"],
                            metadata=item.get("metadata", {})
                        ))
            
            # 按相似度排序
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:limit]
            
            log.info(f"Vector search found {len(results)} results")
            return results
        
        except Exception as e:
            log.error(f"Error in vector search: {e}")
            return []
    
    async def _graph_search(
        self,
        user_id: int,
        query: str,
        filters: Dict[str, Any],
        limit: int
    ) -> List[SearchResult]:
        """
        图搜索
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            filters: 过滤条件
            limit: 返回结果数量限制
        
        Returns:
            搜索结果列表
        """
        try:
            results = []
            
            # 提取查询中的实体
            entities = self.agent.extract_entities_from_query(query)
            
            if not entities:
                return results
            
            # 在Neo4j中搜索相关节点
            with neo4j_db.session() as session:
                for entity in entities:
                    # 搜索Note节点
                    cypher = """
                        MATCH (u:User {id: $user_id})-[:HAS_NOTE]->(n:Note)
                        WHERE n.content CONTAINS $entity
                        RETURN n.id as id, n.content as content, 'note' as source_type
                        LIMIT $limit
                    """
                    result = session.run(
                        cypher,
                        user_id=user_id,
                        entity=entity,
                        limit=limit
                    )
                    
                    for record in result:
                        results.append(SearchResult(
                            id=record["id"],
                            content=record["content"][:200],
                            score=0.7,
                            source_type=record["source_type"],
                            metadata={"type": "note"}
                        ))
                    
                    # 搜索Event节点
                    cypher = """
                        MATCH (u:User {id: $user_id})-[:HAS_EVENT]->(e:Event)
                        WHERE e.title CONTAINS $entity OR e.description CONTAINS $entity
                        RETURN e.id as id, e.title as title, e.description as description, 'event' as source_type
                        LIMIT $limit
                    """
                    result = session.run(
                        cypher,
                        user_id=user_id,
                        entity=entity,
                        limit=limit
                    )
                    
                    for record in result:
                        content = f"{record['title']}: {record['description']}" if record['description'] else record['title']
                        results.append(SearchResult(
                            id=record["id"],
                            content=content[:200],
                            score=0.7,
                            source_type=record["source_type"],
                            metadata={"type": "event"}
                        ))
            
            log.info(f"Graph search found {len(results)} results")
            return results
        
        except Exception as e:
            log.error(f"Error in graph search: {e}")
            return []
    
    def _deduplicate_and_sort(
        self,
        results: List[SearchResult],
        limit: int
    ) -> List[SearchResult]:
        """
        去重和排序
        
        Args:
            results: 搜索结果列表
            limit: 返回结果数量限制
        
        Returns:
            去重排序后的结果列表
        """
        # 去重（相同ID保留分数高的）
        result_dict = {}
        for result in results:
            if result.id not in result_dict:
                result_dict[result.id] = result
            else:
                if result.score > result_dict[result.id].score:
                    result_dict[result.id] = result
        
        # 按分数排序
        sorted_results = sorted(
            result_dict.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        return sorted_results[:limit]
    
    async def get_related_notes(
        self,
        user_id: int,
        note_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取相关速记（基于图关系）
        
        Args:
            user_id: 用户ID
            note_id: 速记ID
            limit: 返回结果数量限制
        
        Returns:
            相关速记列表
        """
        try:
            related_notes = []
            
            with neo4j_db.session() as session:
                # 查找与该速记相关的其他速记
                cypher = """
                    MATCH (u:User {id: $user_id})-[:HAS_NOTE]->(n:Note {id: $note_id})
                    MATCH (n)-[r:RELATED_TO|SIMILAR_TO|CAUSED_BY]-(other:Note)
                    WHERE other.id <> $note_id
                    RETURN other.id as id, other.content as content, r.weight as weight
                    ORDER BY r.weight DESC
                    LIMIT $limit
                """
                
                result = session.run(
                    cypher,
                    user_id=user_id,
                    note_id=note_id,
                    limit=limit
                )
                
                for record in result:
                    related_notes.append({
                        "id": record["id"],
                        "content": record["content"][:200],
                        "weight": record["weight"]
                    })
            
            return related_notes
        
        except Exception as e:
            log.error(f"Error getting related notes: {e}")
            return []
    
    async def get_search_suggestions(
        self,
        user_id: int,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """
        获取搜索建议
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            limit: 返回结果数量限制
        
        Returns:
            搜索建议列表
        """
        try:
            # 扩展查询
            expanded_queries = self.agent.expand_query(query)
            
            # 从历史搜索中获取建议
            cache_key = f"search_history:user:{user_id}"
            history = redis_db.lrange(cache_key, 0, -1)
            
            suggestions = []
            
            # 添加扩展查询
            suggestions.extend(expanded_queries)
            
            # 添加历史搜索中匹配的查询
            for h in history:
                if query.lower() in h.lower() and h not in suggestions:
                    suggestions.append(h)
            
            return suggestions[:limit]
        
        except Exception as e:
            log.error(f"Error getting search suggestions: {e}")
            return []
    
    async def save_search_history(
        self,
        user_id: int,
        query: str
    ) -> None:
        """
        保存搜索历史
        
        Args:
            user_id: 用户ID
            query: 搜索查询
        """
        try:
            cache_key = f"search_history:user:{user_id}"
            redis_db.lpush(cache_key, query)
            redis_db.ltrim(cache_key, 0, 99)  # 保留最近100条
            redis_db.expire(cache_key, 86400 * 30)  # 30天过期
        
        except Exception as e:
            log.error(f"Error saving search history: {e}")


# 全局搜索服务实例
search_service = SearchService()
