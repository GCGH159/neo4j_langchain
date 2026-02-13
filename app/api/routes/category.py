"""
分类相关API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.category_service import category_service
from app.config.logging_config import log

router = APIRouter()


class CategoryCreateRequest(BaseModel):
    """创建分类请求"""
    name: str
    parent_id: Optional[int] = None


class CategoryUpdateRequest(BaseModel):
    """更新分类请求"""
    name: Optional[str] = None
    parent_id: Optional[int] = None


@router.post("/", response_model=dict)
async def create_category(user_id: int, request: CategoryCreateRequest):
    """
    创建分类
    
    - **user_id**: 用户ID
    - **name**: 分类名称
    - **parent_id**: 父分类ID（可选）
    """
    try:
        result = await category_service.create_category(
            user_id=user_id,
            name=request.name,
            parent_id=request.parent_id
        )
        return {
            "success": True,
            "message": "分类创建成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in create_category: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tree/{user_id}", response_model=dict)
async def get_category_tree(user_id: int):
    """
    获取分类树
    
    - **user_id**: 用户ID
    """
    try:
        tree = await category_service.get_category_tree(user_id)
        return {
            "success": True,
            "data": tree
        }
    except Exception as e:
        log.error(f"Error in get_category_tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category_id}", response_model=dict)
async def get_category(category_id: int):
    """
    获取分类详情
    
    - **category_id**: 分类ID
    """
    try:
        category = await category_service.get_category(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        return {
            "success": True,
            "data": category
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in get_category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{category_id}", response_model=dict)
async def update_category(category_id: int, request: CategoryUpdateRequest):
    """
    更新分类
    
    - **category_id**: 分类ID
    - **name**: 分类名称（可选）
    - **parent_id**: 父分类ID（可选）
    """
    try:
        result = await category_service.update_category(
            category_id=category_id,
            name=request.name,
            parent_id=request.parent_id
        )
        return {
            "success": True,
            "message": "分类更新成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in update_category: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}", response_model=dict)
async def delete_category(category_id: int):
    """
    删除分类
    
    - **category_id**: 分类ID
    """
    try:
        await category_service.delete_category(category_id)
        return {
            "success": True,
            "message": "分类删除成功"
        }
    except Exception as e:
        log.error(f"Error in delete_category: {e}")
        raise HTTPException(status_code=400, detail=str(e))
