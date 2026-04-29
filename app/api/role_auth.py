"""
角色认证与API Key管理模块
基于数据库的用户认证机制
"""
from __future__ import annotations

import os
from typing import Dict, Optional, Set

# 导入用户服务
try:
    from app.services.user_service import get_user_by_api_key
except ImportError:
    # 如果user_service还未创建，使用fallback
    def get_user_by_api_key(api_key: str):
        return None


# 角色到Agent的映射配置
ROLE_TO_AGENTS: Dict[str, Dict] = {
    "power_expert": {
        "display_name": "电力行业专家",
        "api_key_prefix": "edms-power-expert-",
        "allowed_agents": {"power_standard_query"},
        "description": "专注电力行业标准、技术规范查询"
    },
    "business_analyst": {
        "display_name": "企业分析师",
        "api_key_prefix": "edms-business-analyst-",
        "allowed_agents": {"annual_report_analyst", "deep_insight_analyst"},
        "description": "企业年报分析与经营洞察"
    },
    "decision_maker": {
        "display_name": "综合决策者",
        "api_key_prefix": "edms-decision-maker-",
        "allowed_agents": {"power_standard_query", "annual_report_analyst", "deep_insight_analyst", "auto_report_expert"},
        "description": "跨领域综合决策支持"
    }
}


def get_role_from_api_key(api_key: str) -> Optional[str]:
    """
    根据API Key识别角色（从数据库查询）
    
    Args:
        api_key: 前端传入的API Key
        
    Returns:
        角色标识字符串，如果无法识别则返回None
    """
    if not api_key:
        return None
    
    # 从数据库查询用户
    user = get_user_by_api_key(api_key)
    
    if user:
        # 返回用户的角色
        role = user.get('role', '')
        
        # 映射角色字符串到系统角色标识
        role_mapping = {
            '综合决策者': 'decision_maker',
            '企业分析师': 'business_analyst',
            '电力行业专家': 'power_expert',
            'admin': 'admin',
            # 兼容旧的直接存储英文角色
            'decision_maker': 'decision_maker',
            'business_analyst': 'business_analyst',
            'power_expert': 'power_expert'
        }
        
        return role_mapping.get(role, None)
    
    return None


def validate_role_access(role: str, agent_alias: str) -> bool:
    """
    验证角色是否有权限访问指定Agent
    
    Args:
        role: 角色标识
        agent_alias: Agent别名
        
    Returns:
        True表示有权限，False表示无权限
    """
    if role not in ROLE_TO_AGENTS:
        return False
    
    allowed_agents = ROLE_TO_AGENTS[role]["allowed_agents"]
    return agent_alias in allowed_agents


def get_allowed_agents_for_role(role: str) -> Set[str]:
    """
    获取角色允许访问的Agent列表
    
    Args:
        role: 角色标识
        
    Returns:
        Agent别名集合
    """
    if role not in ROLE_TO_AGENTS:
        return set()
    
    return ROLE_TO_AGENTS[role]["allowed_agents"].copy()


def generate_role_api_key(role: str, secret_suffix: str = "") -> str:
    """
    为角色生成API Key（用于后端配置）
    
    Args:
        role: 角色标识
        secret_suffix: 密钥后缀（建议至少8位随机字符）
        
    Returns:
        完整的API Key字符串
        
    Example:
        >>> generate_role_api_key("power_expert", "a1b2c3d4")
        'edms-power-expert-a1b2c3d4'
    """
    if role not in ROLE_TO_AGENTS:
        raise ValueError(f"Unknown role: {role}")
    
    prefix = ROLE_TO_AGENTS[role]["api_key_prefix"]
    return f"{prefix}{secret_suffix}"


def list_available_roles() -> Dict[str, Dict]:
    """
    列出所有可用角色及其配置（不包含敏感信息）
    
    Returns:
        角色配置字典
    """
    result = {}
    for role_name, config in ROLE_TO_AGENTS.items():
        result[role_name] = {
            "display_name": config["display_name"],
            "description": config["description"],
            "api_key_prefix": config["api_key_prefix"]
        }
    return result
