# -*- coding: utf-8 -*-
"""认证路由 - 提供用户登录接口"""

from fastapi import APIRouter, Depends, HTTPException, status

from auth import verify_password, create_access_token, get_current_user
from database import get_user_by_username
from models import LoginRequest, TokenResponse

router = APIRouter(tags=["认证"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = get_user_by_username(request.username)
    
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(user["id"], user["username"])
    
    return TokenResponse(access_token=access_token)


@router.get("/auth/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    return {
        "status": "success",
        "data": {
            "user_id": user["user_id"],
            "username": user["username"],
        }
    }