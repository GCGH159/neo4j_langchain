"""
搜索相关API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.search_service import search_service
from app.config.logging_config import log

router = APIRouter()


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    search_type: Optional[str] = "auto"
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 10


@router.post("/", response_model=dict)
async def search(user_id: int, request: SearchRequest):
    """
    智能搜索
    
    - **user_id**: 用户ID
    - **query**: 搜索查询
    - **search_type**: 搜索类型（auto/fulltext/vector/graph/hybrid）
    - **filters**: 过滤条件（可选）
    - **limit**: 返回结果数量限制
    """
    try:
        result = await search_service.search(
            user_id=user_id,
            query=request.query,
            search_type=request.search_type,
            filters=request.filters,
            limit=request.limit
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        log.error(f"Error in search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions", response_model=dict)
async def get_search_suggestions(user_id: int, query: str, limit: int = 5):
    """
    获取搜索建议
    
    - **user_id**: 用户ID
    - **query**: 搜索查询
    - **limit**: 返回结果数量限制
    """
    try:
        suggestions = await search_service.get_search_suggestions(
            user_id=user_id,
            query=query,
            limit=limit
        )
        return {
            "success": True,
            "data": suggestions
        }
    except Exception as e:
        log.error(f"Error in get_search_suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/related", response_model=dict)
async def get_related_notes(note_id: int, limit: int = 5):
    """
    获取相关速记
    
    - **note_id**: 速记ID
    - **limit**: 返回结果数量限制
    """
    try:
        related = await search_service.get_related_notes(note_id, limit)
        return {
            "success": True,
            "data": related
        }
    except Exception as e:
        log.error(f"Error in get_related_notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
