"""
用户相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.services.user_service import user_service
from app.config.logging_config import log

router = APIRouter()


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    created_at: str


@router.post("/register", response_model=dict)
async def register(request: UserRegisterRequest):
    """
    用户注册
    
    - **username**: 用户名
    - **email**: 邮箱
    - **password**: 密码
    """
    try:
        result = await user_service.register(
            username=request.username,
            email=request.email,
            password=request.password
        )
        return {
            "success": True,
            "message": "注册成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in register: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=dict)
async def login(request: UserLoginRequest):
    """
    用户登录
    
    - **email**: 邮箱
    - **password**: 密码
    """
    try:
        result = await user_service.login(
            email=request.email,
            password=request.password
        )
        return {
            "success": True,
            "message": "登录成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in login: {e}")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: int):
    """
    获取用户信息
    
    - **user_id**: 用户ID
    """
    try:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "success": True,
            "data": user
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in get_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/preferences", response_model=dict)
async def get_user_preferences(user_id: int):
    """
    获取用户偏好设置
    
    - **user_id**: 用户ID
    """
    try:
        preferences = await user_service.get_user_preferences(user_id)
        return {
            "success": True,
            "data": preferences
        }
    except Exception as e:
        log.error(f"Error in get_user_preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/preferences", response_model=dict)
async def update_user_preferences(user_id: int, preferences: dict):
    """
    更新用户偏好设置
    
    - **user_id**: 用户ID
    - **preferences**: 偏好设置
    """
    try:
        result = await user_service.update_user_preferences(user_id, preferences)
        return {
            "success": True,
            "message": "偏好设置更新成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in update_user_preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))
