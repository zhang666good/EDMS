"""
用户管理API接口
提供用户注册、查询、权限管理等功能
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import secrets

from app.services.user_service import (
    create_user,
    get_user_by_uid,
    get_user_by_phone,
    update_user_role,
    update_user_api_key,
    get_all_users,
    search_users,
    deactivate_user
)

router = APIRouter(prefix="/users", tags=["用户管理"])


# 请求模型
class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    name: str = Field(..., description="姓名", min_length=1, max_length=50)
    phone: str = Field(..., description="手机号", pattern=r"^1[3-9]\d{9}$")


class UserRoleUpdateRequest(BaseModel):
    """更新用户角色请求"""
    uid: str = Field(..., description="用户UID")
    role: str = Field(..., description="角色", enum=["综合决策者", "企业分析师", "电力行业专家", ""])


class UserApiKeyGenerateRequest(BaseModel):
    """生成API Key请求"""
    uid: str = Field(..., description="用户UID")


class UserSearchRequest(BaseModel):
    """搜索用户请求"""
    keyword: str = Field(..., description="搜索关键词（姓名/手机号/UID）")


# 响应模型
class UserResponse(BaseModel):
    """用户信息响应"""
    uid: str
    name: str
    phone: str
    role: str
    api_key: Optional[str] = None
    created_at: str


class ApiResponse(BaseModel):
    """通用API响应"""
    code: int
    message: str
    data: Optional[dict] = None


# API接口
@router.post("/register", response_model=ApiResponse)
def register_user(request: UserRegisterRequest = Body(...)):
    """
    用户注册接口
    
    - 自动生成唯一UID
    - 检查手机号是否已注册
    - 初始角色为空，需管理员设置
    """
    # 检查手机号是否已注册
    existing_user = get_user_by_phone(request.phone)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "PHONE_ALREADY_REGISTERED",
                "message": "该手机号已注册"
            }
        )
    
    # 生成唯一UID
    uid = f"user_{uuid.uuid4().hex[:12]}"
    
    # 创建用户
    success = create_user(
        uid=uid,
        name=request.name,
        phone=request.phone,
        role="",  # 初始无角色
        api_key=None  # 初始无API Key
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "REGISTER_FAILED",
                "message": "用户注册失败，请稍后重试"
            }
        )
    
    return ApiResponse(
        code=200,
        message="注册成功",
        data={
            "uid": uid,
            "name": request.name,
            "phone": request.phone,
            "note": "请联系管理员设置角色和生成API Key"
        }
    )


@router.get("/list", response_model=List[UserResponse])
def list_users():
    """
    获取所有用户列表（管理员专用）
    
    - 返回所有活跃用户
    - 按注册时间倒序排列
    """
    users = get_all_users()
    
    # 转换为响应格式
    result = []
    for user in users:
        result.append(UserResponse(
            uid=user['uid'],
            name=user['name'],
            phone=user['phone'],
            role=user['role'] or "",
            api_key=user['api_key'],
            created_at=str(user['created_at'])
        ))
    
    return result


@router.post("/search", response_model=List[UserResponse])
def search_user_api(request: UserSearchRequest = Body(...)):
    """
    搜索用户（管理员专用）
    
    - 支持按姓名、手机号、UID搜索
    """
    users = search_users(request.keyword)
    
    result = []
    for user in users:
        result.append(UserResponse(
            uid=user['uid'],
            name=user['name'],
            phone=user['phone'],
            role=user['role'] or "",
            api_key=user['api_key'],
            created_at=str(user['created_at'])
        ))
    
    return result


@router.post("/set-role", response_model=ApiResponse)
def set_user_role(request: UserRoleUpdateRequest = Body(...)):
    """
    设置用户角色（管理员专用）
    
    - 可选角色：综合决策者、企业分析师、电力行业专家
    """
    # 验证用户是否存在
    user = get_user_by_uid(request.uid)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "用户不存在"
            }
        )
    
    # 更新角色
    success = update_user_role(request.uid, request.role)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "UPDATE_FAILED",
                "message": "更新角色失败"
            }
        )
    
    return ApiResponse(
        code=200,
        message=f"用户 {user['name']} 的角色已设置为: {request.role or '未设置'}",
        data={
            "uid": request.uid,
            "role": request.role
        }
    )


@router.post("/generate-api-key", response_model=ApiResponse)
def generate_api_key(request: UserApiKeyGenerateRequest = Body(...)):
    """
    为用户生成API Key（管理员专用）
    
    - 生成格式: edms-{role}-{random}
    - 如果用户已有API Key，会覆盖
    """
    # 验证用户是否存在
    user = get_user_by_uid(request.uid)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "用户不存在"
            }
        )
    
    # 检查用户是否有角色
    if not user.get('role'):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ROLE_NOT_SET",
                "message": "请先为用户设置角色"
            }
        )
    
    # 映射角色到英文标识
    role_mapping = {
        '综合决策者': 'decision-maker',
        '企业分析师': 'business-analyst',
        '电力行业专家': 'power-expert'
    }
    
    role_en = role_mapping.get(user['role'], 'user')
    
    # 生成随机后缀（16位）
    random_suffix = secrets.token_hex(8)
    
    # 生成API Key
    api_key = f"edms-{role_en}-{random_suffix}"
    
    # 保存到数据库
    success = update_user_api_key(request.uid, api_key)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "GENERATE_FAILED",
                "message": "生成API Key失败"
            }
        )
    
    return ApiResponse(
        code=200,
        message="API Key生成成功",
        data={
            "uid": request.uid,
            "api_key": api_key,
            "note": "请将此API Key提供给用户，妥善保管"
        }
    )


@router.post("/deactivate", response_model=ApiResponse)
def deactivate_user_api(uid: str = Body(..., embed=True)):
    """
    禁用用户（管理员专用）
    
    - 软删除，不真正删除数据
    - 禁用后无法登录
    """
    user = get_user_by_uid(uid)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "用户不存在"
            }
        )
    
    success = deactivate_user(uid)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DEACTIVATE_FAILED",
                "message": "禁用用户失败"
            }
        )
    
    return ApiResponse(
        code=200,
        message=f"用户 {user['name']} 已禁用",
        data={"uid": uid}
    )


@router.get("/{uid}", response_model=UserResponse)
def get_user_info(uid: str):
    """
    获取单个用户信息
    
    - 通过UID查询
    """
    user = get_user_by_uid(uid)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "用户不存在"
            }
        )
    
    return UserResponse(
        uid=user['uid'],
        name=user['name'],
        phone=user['phone'],
        role=user['role'] or "",
        api_key=user['api_key'],
        created_at=str(user['created_at'])
    )
