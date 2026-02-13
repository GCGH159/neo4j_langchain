"""
事件相关API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.services.note_service import note_service
from app.config.logging_config import log

router = APIRouter()


class EventCreateRequest(BaseModel):
    """创建事件请求"""
    title: str
    description: Optional[str] = None
    event_date: datetime
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None


class EventUpdateRequest(BaseModel):
    """更新事件请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None


@router.post("/", response_model=dict)
async def create_event(user_id: int, request: EventCreateRequest):
    """
    创建事件
    
    - **user_id**: 用户ID
    - **title**: 事件标题
    - **description**: 事件描述（可选）
    - **event_date**: 事件日期
    - **category_id**: 分类ID（可选）
    - **tags**: 标签列表（可选）
    """
    try:
        result = await note_service.create_event(
            user_id=user_id,
            title=request.title,
            description=request.description,
            event_date=request.event_date,
            category_id=request.category_id,
            tags=request.tags
        )
        return {
            "success": True,
            "message": "事件创建成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in create_event: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{event_id}", response_model=dict)
async def get_event(event_id: int):
    """
    获取事件详情
    
    - **event_id**: 事件ID
    """
    try:
        event = await note_service.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="事件不存在")
        
        return {
            "success": True,
            "data": event
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in get_event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=dict)
async def get_user_events(
    user_id: int,
    category_id: Optional[int] = None,
    limit: int = 50
):
    """
    获取用户事件列表
    
    - **user_id**: 用户ID
    - **category_id**: 分类ID（可选）
    - **limit**: 返回数量限制
    """
    try:
        events = await note_service.get_user_events(
            user_id=user_id,
            category_id=category_id,
            limit=limit
        )
        return {
            "success": True,
            "data": events
        }
    except Exception as e:
        log.error(f"Error in get_user_events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{event_id}", response_model=dict)
async def update_event(event_id: int, request: EventUpdateRequest):
    """
    更新事件
    
    - **event_id**: 事件ID
    - **title**: 事件标题（可选）
    - **description**: 事件描述（可选）
    - **event_date**: 事件日期（可选）
    - **category_id**: 分类ID（可选）
    - **tags**: 标签列表（可选）
    """
    try:
        result = await note_service.update_event(
            event_id=event_id,
            title=request.title,
            description=request.description,
            event_date=request.event_date,
            category_id=request.category_id,
            tags=request.tags
        )
        return {
            "success": True,
            "message": "事件更新成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in update_event: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{event_id}", response_model=dict)
async def delete_event(event_id: int):
    """
    删除事件
    
    - **event_id**: 事件ID
    """
    try:
        await note_service.delete_event(event_id)
        return {
            "success": True,
            "message": "事件删除成功"
        }
    except Exception as e:
        log.error(f"Error in delete_event: {e}")
        raise HTTPException(status_code=400, detail=str(e))
