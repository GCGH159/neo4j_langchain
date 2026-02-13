"""
速记相关API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.note_service import note_service
from app.config.logging_config import log

router = APIRouter()


class NoteCreateRequest(BaseModel):
    """创建速记请求"""
    content: str
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None


class NoteUpdateRequest(BaseModel):
    """更新速记请求"""
    content: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None


@router.post("/", response_model=dict)
async def create_note(user_id: int, request: NoteCreateRequest):
    """
    创建速记
    
    - **user_id**: 用户ID
    - **content**: 速记内容
    - **category_id**: 分类ID（可选）
    - **tags**: 标签列表（可选）
    """
    try:
        result = await note_service.create_note(
            user_id=user_id,
            content=request.content,
            category_id=request.category_id,
            tags=request.tags
        )
        return {
            "success": True,
            "message": "速记创建成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in create_note: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{note_id}", response_model=dict)
async def get_note(note_id: int):
    """
    获取速记详情
    
    - **note_id**: 速记ID
    """
    try:
        note = await note_service.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="速记不存在")
        
        return {
            "success": True,
            "data": note
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in get_note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=dict)
async def get_user_notes(
    user_id: int,
    category_id: Optional[int] = None,
    limit: int = 50
):
    """
    获取用户速记列表
    
    - **user_id**: 用户ID
    - **category_id**: 分类ID（可选）
    - **limit**: 返回数量限制
    """
    try:
        notes = await note_service.get_user_notes(
            user_id=user_id,
            category_id=category_id,
            limit=limit
        )
        return {
            "success": True,
            "data": notes
        }
    except Exception as e:
        log.error(f"Error in get_user_notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{note_id}", response_model=dict)
async def update_note(note_id: int, request: NoteUpdateRequest):
    """
    更新速记
    
    - **note_id**: 速记ID
    - **content**: 速记内容（可选）
    - **category_id**: 分类ID（可选）
    - **tags**: 标签列表（可选）
    """
    try:
        result = await note_service.update_note(
            note_id=note_id,
            content=request.content,
            category_id=request.category_id,
            tags=request.tags
        )
        return {
            "success": True,
            "message": "速记更新成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in update_note: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{note_id}", response_model=dict)
async def delete_note(note_id: int):
    """
    删除速记
    
    - **note_id**: 速记ID
    """
    try:
        await note_service.delete_note(note_id)
        return {
            "success": True,
            "message": "速记删除成功"
        }
    except Exception as e:
        log.error(f"Error in delete_note: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{note_id}/related", response_model=dict)
async def get_related_notes(note_id: int, limit: int = 5):
    """
    获取相关速记
    
    - **note_id**: 速记ID
    - **limit**: 返回数量限制
    """
    try:
        related = await note_service.get_related_notes(note_id, limit)
        return {
            "success": True,
            "data": related
        }
    except Exception as e:
        log.error(f"Error in get_related_notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
