"""
用户管理数据库模块 - 基于SQLite
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import hashlib


# 数据库文件路径
DB_DIR = Path(__file__).resolve().parent.parent / "db"
DB_PATH = DB_DIR / "users.db"


def get_db_connection():
    """获取数据库连接"""
    # 确保目录存在
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn


def init_database():
    """初始化数据库表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            role TEXT DEFAULT '',
            api_key TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_uid ON users(uid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_key ON users(api_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phone ON users(phone)")
    
    conn.commit()
    conn.close()
    
    print(f"[DB] 数据库初始化完成: {DB_PATH}")


# 用户CRUD操作
def create_user(uid: str, name: str, phone: str, role: str = "", api_key: str = None) -> bool:
    """
    创建新用户
    
    Args:
        uid: 用户唯一标识
        name: 姓名
        phone: 手机号
        role: 角色（可选）
        api_key: API Key（可选，管理员生成）
        
    Returns:
        True表示成功，False表示失败
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (uid, name, phone, role, api_key) VALUES (?, ?, ?, ?, ?)",
            (uid, name, phone, role, api_key)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"[DB] 创建用户失败: {e}")
        return False
    finally:
        conn.close()


def get_user_by_uid(uid: str) -> Optional[Dict]:
    """根据UID查询用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE uid = ? AND is_active = 1", (uid,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_user_by_api_key(api_key: str) -> Optional[Dict]:
    """根据API Key查询用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE api_key = ? AND is_active = 1", (api_key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_user_by_phone(phone: str) -> Optional[Dict]:
    """根据手机号查询用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE phone = ? AND is_active = 1", (phone,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_user_role(uid: str, role: str) -> bool:
    """更新用户角色"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE uid = ?",
            (role, uid)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_user_api_key(uid: str, api_key: str) -> bool:
    """更新用户API Key"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET api_key = ?, updated_at = CURRENT_TIMESTAMP WHERE uid = ?",
            (api_key, uid)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError as e:
        print(f"[DB] 更新API Key失败: {e}")
        return False
    finally:
        conn.close()


def deactivate_user(uid: str) -> bool:
    """禁用用户（软删除）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE uid = ?",
            (uid,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_all_users() -> List[Dict]:
    """获取所有活跃用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def search_users(keyword: str) -> List[Dict]:
    """搜索用户（按姓名、手机号或UID）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search_pattern = f"%{keyword}%"
    cursor.execute(
        """SELECT * FROM users 
           WHERE is_active = 1 
           AND (name LIKE ? OR phone LIKE ? OR uid LIKE ?)
           ORDER BY created_at DESC""",
        (search_pattern, search_pattern, search_pattern)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# 初始化管理员账户
def create_admin_if_not_exists():
    """如果不存在则创建默认管理员账户"""
    admin_uid = "admin_001"
    admin = get_user_by_uid(admin_uid)
    
    if not admin:
        # 创建管理员（特殊角色）
        create_user(
            uid=admin_uid,
            name="系统管理员",
            phone="00000000000",
            role="admin",
            api_key="edms-admin-master-key-001"
        )
        print("[DB] 默认管理员账户已创建")


def verify_admin_credentials(username: str, password: str) -> Optional[Dict]:
    """
    验证管理员凭证
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        如果验证成功返回管理员信息，否则返回None
    """
    # 从环境变量读取管理员凭证
    env_username = os.getenv("admin", "zhang666")
    env_password = os.getenv("password", "Python666good@")
    
    # 验证凭证
    if username == env_username and password == env_password:
        # 获取管理员用户信息
        admin = get_user_by_uid("admin_001")
        if admin:
            return admin
        else:
            # 如果数据库中不存在，返回默认信息
            return {
                "uid": "admin_001",
                "name": "系统管理员",
                "role": "admin"
            }
    
    return None


# 初始化数据库
init_database()
create_admin_if_not_exists()
