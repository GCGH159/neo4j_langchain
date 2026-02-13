"""
时间轴相关API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.services.timeline_service import timeline_service
from app.config.logging_config import log

router = APIRouter()


@router.get("/", response_model=dict)
async def get_timeline(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
):
    """
    获取时间轴数据
    
    - **user_id**: 用户ID
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    - **limit**: 返回结果数量限制
    """
    try:
        result = await timeline_service.get_timeline(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        log.error(f"Error in get_timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category_id}", response_model=dict)
async def get_timeline_by_category(
    user_id: int,
    category_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
):
    """
    按分类获取时间轴数据
    
    - **user_id**: 用户ID
    - **category_id**: 分类ID
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    - **limit**: 返回结果数量限制
    """
    try:
        result = await timeline_service.get_timeline_by_category(
            user_id=user_id,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        log.error(f"Error in get_timeline_by_category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{user_id}", response_model=dict)
async def get_timeline_statistics(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    获取时间轴统计数据
    
    - **user_id**: 用户ID
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    """
    try:
        result = await timeline_service.get_timeline_statistics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        log.error(f"Error in get_timeline_statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
