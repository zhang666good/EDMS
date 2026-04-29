"""
JWT认证服务模块
提供Token生成、验证和解码功能
"""
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps
from fastapi import HTTPException, Header


# JWT配置（从环境变量读取）
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


def generate_token(user_id: str, username: str, role: str = "admin") -> str:
    """
    生成JWT Token
    
    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        
    Returns:
        JWT Token字符串
    """
    now = datetime.utcnow()
    expire = now + timedelta(hours=JWT_EXPIRE_HOURS)
    
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
        "iat": now,
        "type": "access"
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[Dict]:
    """
    验证JWT Token
    
    Args:
        token: JWT Token字符串
        
    Returns:
        解码后的payload，如果验证失败返回None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("[JWT] Token已过期")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[JWT] Token无效: {e}")
        return None


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict:
    """
    从请求头获取当前用户信息（FastAPI依赖注入）
    
    Args:
        authorization: Authorization头（Bearer token）
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 如果Token无效或缺失
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "AUTHORIZATION_REQUIRED",
                "message": "缺少认证Token"
            }
        )
    
    # 提取Token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_TOKEN_FORMAT",
                "message": "Token格式错误，应为: Bearer <token>"
            }
        )
    
    token = authorization[7:]
    
    # 验证Token
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Token无效或已过期"
            }
        )
    
    return payload


def require_auth(func):
    """
    认证装饰器（用于普通函数）
    
    Usage:
        @require_auth
        def my_function(current_user: Dict):
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 这里需要从请求中获取Token，通常在FastAPI中使用Depends
        # 这个装饰器主要用于非FastAPI场景
        raise NotImplementedError("请在FastAPI中使用 get_current_user 依赖注入")
    return wrapper
