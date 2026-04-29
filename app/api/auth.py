"""
认证API接口
提供管理员登录、Token验证等功能
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.services.user_service import verify_admin_credentials
from app.services.auth_service import generate_token, get_current_user

router = APIRouter(prefix="/auth", tags=["认证管理"])


# 请求模型
class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenRefreshRequest(BaseModel):
    """Token刷新请求（可选）"""
    token: str = Field(..., description="当前Token")


# 响应模型
class LoginResponse(BaseModel):
    """登录响应"""
    code: int
    message: str
    data: Optional[dict] = None


class TokenInfo(BaseModel):
    """Token信息"""
    access_token: str
    token_type: str
    expires_in: int
    user_info: dict


# API接口
@router.post("/login", response_model=LoginResponse)
def admin_login(request: LoginRequest = Body(...)):
    """
    管理员登录接口
    
    - 验证用户名和密码
    - 生成JWT Token
    - 返回Token和用户信息
    """
    # 验证凭证
    admin = verify_admin_credentials(request.username, request.password)
    
    if not admin:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "用户名或密码错误"
            }
        )
    
    # 生成Token
    token = generate_token(
        user_id=admin['uid'],
        username=admin['name'],
        role=admin.get('role', 'admin')
    )
    
    return LoginResponse(
        code=200,
        message="登录成功",
        data={
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 86400,  # 24小时（秒）
            "user_info": {
                "uid": admin['uid'],
                "name": admin['name'],
                "role": admin.get('role', 'admin')
            }
        }
    )


@router.post("/verify", response_model=LoginResponse)
def verify_token_api(current_user: dict = Depends(get_current_user)):
    """
    验证Token有效性
    
    - 需要携带有效的Bearer Token
    - 返回当前用户信息
    """
    return LoginResponse(
        code=200,
        message="Token有效",
        data={
            "user_info": {
                "user_id": current_user.get('user_id'),
                "username": current_user.get('username'),
                "role": current_user.get('role')
            }
        }
    )


@router.get("/me", response_model=LoginResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前登录用户信息
    
    - 需要携带有效的Bearer Token
    """
    return LoginResponse(
        code=200,
        message="获取成功",
        data={
            "user_info": {
                "user_id": current_user.get('user_id'),
                "username": current_user.get('username'),
                "role": current_user.get('role'),
                "exp": current_user.get('exp')
            }
        }
    )
