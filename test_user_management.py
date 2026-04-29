"""
用户管理系统测试脚本
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_user_registration():
    """测试1: 用户注册"""
    print_section("测试1: 用户注册")
    
    users = [
        {"name": "张三", "phone": "13800138001"},
        {"name": "李四", "phone": "13800138002"},
        {"name": "王五", "phone": "13800138003"}
    ]
    
    registered_users = []
    
    for user in users:
        print(f"\n注册用户: {user['name']} ({user['phone']})")
        
        response = requests.post(
            f"{BASE_URL}/users/register",
            json=user
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 200:
            registered_users.append(result['data'])
            print(f"✅ 注册成功，UID: {result['data']['uid']}")
        else:
            print(f"❌ 注册失败: {result.get('message')}")
    
    return registered_users

def test_list_users():
    """测试2: 获取用户列表"""
    print_section("测试2: 获取用户列表")
    
    response = requests.get(f"{BASE_URL}/users/list")
    print(f"状态码: {response.status_code}")
    
    users = response.json()
    print(f"用户数量: {len(users)}")
    
    for user in users:
        print(f"  - {user['name']} ({user['phone']}) - UID: {user['uid']} - 角色: {user['role'] or '未设置'}")
    
    return users

def test_set_role(uid, role):
    """测试3: 设置用户角色"""
    print_section(f"测试3: 设置用户角色 - {uid}")
    
    response = requests.post(
        f"{BASE_URL}/users/set-role",
        json={"uid": uid, "role": role}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('code') == 200:
        print(f"✅ 角色设置成功")
    else:
        print(f"❌ 角色设置失败: {result.get('message')}")
    
    return result

def test_generate_api_key(uid):
    """测试4: 生成API Key"""
    print_section(f"测试4: 生成API Key - {uid}")
    
    response = requests.post(
        f"{BASE_URL}/users/generate-api-key",
        json={"uid": uid}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get('code') == 200:
        api_key = result['data']['api_key']
        print(f"✅ API Key生成成功: {api_key}")
        return api_key
    else:
        print(f"❌ 生成失败: {result.get('message')}")
        return None

def test_search_users(keyword):
    """测试5: 搜索用户"""
    print_section(f"测试5: 搜索用户 - '{keyword}'")
    
    response = requests.post(
        f"{BASE_URL}/users/search",
        json={"keyword": keyword}
    )
    
    print(f"状态码: {response.status_code}")
    users = response.json()
    print(f"找到 {len(users)} 个用户")
    
    for user in users:
        print(f"  - {user['name']} ({user['phone']})")

def test_authentication_with_api_key(api_key, model="edms-deep-insight"):
    """测试6: 使用API Key进行认证"""
    print_section(f"测试6: API Key认证测试")
    
    print(f"使用API Key: {api_key}")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": "你好"}],
            "stream": False,
            "user": "test_user"
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 认证成功，请求处理成功")
        result = response.json()
        print(f"回答: {result['choices'][0]['message']['content'][:100]}...")
    else:
        error = response.json()
        print(f"❌ 认证失败: {error.get('message')}")

if __name__ == "__main__":
    print("\n🚀 开始运行用户管理系统测试\n")
    
    try:
        # 测试1: 注册用户
        registered = test_user_registration()
        
        if not registered:
            print("\n⚠️  没有成功注册的用户，跳过后续测试")
            exit(1)
        
        # 测试2: 获取用户列表
        all_users = test_list_users()
        
        if all_users:
            # 取第一个用户进行测试
            test_uid = all_users[0]['uid']
            
            # 测试3: 设置角色
            test_set_role(test_uid, "企业分析师")
            
            # 测试4: 生成API Key
            api_key = test_generate_api_key(test_uid)
            
            if api_key:
                # 测试6: 使用API Key认证
                test_authentication_with_api_key(api_key)
            
            # 测试5: 搜索用户
            test_search_users(all_users[0]['name'])
        
        print_section("测试完成")
        print("\n✅ 所有测试已完成！")
        print("\n📝 下一步:")
        print("   1. 打开浏览器访问: http://127.0.0.1:8000/admin")
        print("   2. 登录管理员账户")
        print("   3. 点击'用户管理'查看和管理用户")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请先启动后端服务: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
