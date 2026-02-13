"""
事件中心相关API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.event_center_service import event_center_service
from app.config.logging_config import log

router = APIRouter()


@router.get("/", response_model=dict)
async def get_event_center(
    user_id: int,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    limit: int = 50
):
    """
    获取事件中心数据
    
    - **user_id**: 用户ID
    - **category_id**: 分类ID（可选）
    - **tag_id**: 标签ID（可选）
    - **limit**: 返回结果数量限制
    """
    try:
        result = await event_center_service.get_event_center(
            user_id=user_id,
            category_id=category_id,
            tag_id=tag_id,
            limit=limit
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        log.error(f"Error in get_event_center: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}/relations", response_model=dict)
async def get_event_relations(user_id: int, event_id: int):
    """
    获取事件关联关系
    
    - **user_id**: 用户ID
    - **event_id**: 事件ID
    """
    try:
        result = await event_center_service.get_event_relations(
            user_id=user_id,
            event_id=event_id
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        log.error(f"Error in get_event_relations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}/timeline", response_model=dict)
async def get_event_timeline(user_id: int, event_id: int):
    """
    获取事件时间轴
    
    - **user_id**: 用户ID
    - **event_id**: 事件ID
    """
    try:
        result = await event_center_service.get_event_timeline(
            user_id=user_id,
            event_id=event_id
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        log.error(f"Error in get_event_timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
