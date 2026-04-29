"""
JWT认证功能测试脚本
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_admin_login():
    """测试1: 管理员登录"""
    print_section("测试1: 管理员登录")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "zhang666",
            "password": "Python666good@"
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('code') == 200:
        token = result['data']['access_token']
        print(f"\n✅ 登录成功！")
        print(f"Token: {token[:50]}...")
        print(f"用户: {result['data']['user_info']['name']}")
        print(f"角色: {result['data']['user_info']['role']}")
        return token
    else:
        print(f"\n❌ 登录失败: {result.get('message')}")
        return None

def test_invalid_login():
    """测试2: 无效凭证登录"""
    print_section("测试2: 无效凭证登录")
    
    test_cases = [
        ("wrong_user", "Python666good@", "错误用户名"),
        ("zhang666", "wrong_password", "错误密码"),
        ("", "", "空凭证"),
    ]
    
    for username, password, description in test_cases:
        print(f"\n测试: {description}")
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ 正确拒绝无效凭证")
        else:
            print(f"❌ 应该返回401，实际返回 {response.status_code}")

def test_verify_token(token):
    """测试3: 验证Token"""
    print_section("测试3: 验证Token有效性")
    
    response = requests.post(
        f"{BASE_URL}/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('code') == 200:
        print("\n✅ Token验证成功")
        return True
    else:
        print(f"\n❌ Token验证失败: {result.get('message')}")
        return False

def test_get_current_user(token):
    """测试4: 获取当前用户信息"""
    print_section("测试4: 获取当前用户信息")
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('code') == 200:
        print("\n✅ 获取用户信息成功")
        return True
    else:
        print(f"\n❌ 获取失败: {result.get('message')}")
        return False

def test_invalid_token():
    """测试5: 无效Token"""
    print_section("测试5: 使用无效Token")
    
    response = requests.post(
        f"{BASE_URL}/auth/verify",
        headers={"Authorization": "Bearer invalid-token-12345"}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ 正确拒绝无效Token")
        return True
    else:
        print(f"❌ 应该返回401，实际返回 {response.status_code}")
        return False

def test_no_token():
    """测试6: 无Token访问"""
    print_section("测试6: 无Token访问受保护接口")
    
    response = requests.post(f"{BASE_URL}/auth/verify")
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ 正确拒绝无Token请求")
        return True
    else:
        print(f"❌ 应该返回401，实际返回 {response.status_code}")
        return False

if __name__ == "__main__":
    print("\n🚀 开始运行JWT认证测试\n")
    
    try:
        # 测试1: 登录
        token = test_admin_login()
        
        if not token:
            print("\n⚠️  登录失败，跳过后续测试")
            exit(1)
        
        # 测试2: 无效凭证
        test_invalid_login()
        
        # 测试3: 验证Token
        test_verify_token(token)
        
        # 测试4: 获取用户信息
        test_get_current_user(token)
        
        # 测试5: 无效Token
        test_invalid_token()
        
        # 测试6: 无Token
        test_no_token()
        
        print_section("测试完成")
        print("\n✅ 所有测试已完成！")
        print("\n📝 下一步:")
        print("   1. 前端已更新为API登录方式")
        print("   2. 不再硬编码管理员密码")
        print("   3. Token有效期24小时")
        print("   4. 访问 http://127.0.0.1:8000/admin 测试登录")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请先启动后端服务: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
