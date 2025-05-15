from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api.middleware.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_active_user,
)

from .v1 import router as v1_router

router = APIRouter()


# 令牌获取接口
@router.post("/api/v1/token", tags=["登录认证"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "code": 200,
        "success": True,
        "msg": "获取token成功",
        "tokenType": "bearer",
        "accessToken": access_token,
        "availableTime": 7200,
    }


router.include_router(v1_router, prefix="/v1")
