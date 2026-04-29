"""
严格模式测试脚本 - 验证必须提供有效角色API Key
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_no_authorization():
    """测试1: 无Authorization头 - 应该拒绝（401）"""
    print_section("测试1: 无Authorization头（应该拒绝）")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": "edms-deep-insight",
            "messages": [{"role": "user", "content": "你好"}],
            "stream": False,
            "user": "test_user"
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 401:
        error_data = response.json()
        print("✅ 通过 - 正确拒绝无认证请求")
        print(f"   错误码: {error_data.get('code')}")
        print(f"   错误信息: {error_data.get('message')}")
        return True
    else:
        print(f"❌ 失败 - 应该返回401，实际返回 {response.status_code}")
        print(f"   响应: {response.json()}")
        return False


def test_invalid_authorization():
    """测试2: 无效的Authorization头 - 应该拒绝（401）"""
    print_section("测试2: 无效Authorization头（应该拒绝）")
    
    test_cases = [
        ("Bearer abc123random", "随机字符串"),
        ("Bearer invalid-key-format", "无效格式"),
        ("Bearer edms-unknown-role-xxx", "未知角色"),
        ("abc123", "缺少Bearer前缀的无效key"),
    ]
    
    all_passed = True
    
    for auth_header, description in test_cases:
        print(f"\n测试用例: {description}")
        print(f"Authorization: {auth_header}")
        
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_header
            },
            json={
                "model": "edms-deep-insight",
                "messages": [{"role": "user", "content": "你好"}],
                "stream": False,
                "user": "test_user"
            }
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            error_data = response.json()
            print(f"✅ 通过 - 正确拒绝无效认证")
            print(f"   错误码: {error_data.get('code')}")
            print(f"   错误信息: {error_data.get('message')}")
        else:
            print(f"❌ 失败 - 应该返回401，实际返回 {response.status_code}")
            print(f"   响应: {response.json()}")
            all_passed = False
    
    return all_passed


def test_valid_but_unauthorized():
    """测试3: 有效但无权访问 - 应该拒绝（403）"""
    print_section("测试3: 有效API Key但无权访问（应该403）")
    
    # 电力专家尝试访问企业分析师的Agent
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer edms-power-expert-test1234"
        },
        json={
            "model": "edms-deep-insight",  # 企业分析师的Agent
            "messages": [{"role": "user", "content": "你好"}],
            "stream": False,
            "user": "user_001"
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 403:
        error_data = response.json()
        print("✅ 通过 - 正确拒绝越权访问")
        print(f"   错误码: {error_data.get('code')}")
        print(f"   错误信息: {error_data.get('message')}")
        return True
    else:
        print(f"❌ 失败 - 应该返回403，实际返回 {response.status_code}")
        print(f"   响应: {response.json()}")
        return False


def test_models_endpoint_no_auth():
    """测试4: /models接口无认证 - 应该拒绝"""
    print_section("测试4: /models接口无认证（应该拒绝）")
    
    response = requests.get(
        f"{BASE_URL}/v1/models",
        headers={}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 401:
        error_data = response.json()
        print("✅ 通过 - 正确拒绝无认证请求")
        print(f"   错误码: {error_data.get('code')}")
        print(f"   错误信息: {error_data.get('message')}")
        return True
    else:
        print(f"❌ 失败 - 应该返回401，实际返回 {response.status_code}")
        return False


def test_models_endpoint_with_role():
    """测试5: /models接口带角色认证 - 应该返回过滤后的模型列表"""
    print_section("测试5: /models接口带角色认证")
    
    # 测试电力行业专家
    print("\n5a. 电力行业专家")
    response = requests.get(
        f"{BASE_URL}/v1/models",
        headers={"Authorization": "Bearer edms-power-expert-test1234"}
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        models = response.json()["data"]
        model_ids = [m["id"] for m in models]
        print(f"   ✅ 返回授权的模型: {model_ids}")
        if "edms-power-standard" in model_ids and len(model_ids) == 1:
            print(f"   ✅ 权限过滤正确（只返回电力标准模型）")
        else:
            print(f"   ❌ 权限过滤错误")
    else:
        print(f"   ❌ 失败: {response.json()}")
    
    # 测试综合决策者
    print("\n5b. 综合决策者")
    response = requests.get(
        f"{BASE_URL}/v1/models",
        headers={"Authorization": "Bearer edms-decision-maker-test9012"}
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        models = response.json()["data"]
        model_ids = [m["id"] for m in models]
        print(f"   ✅ 返回授权的模型: {model_ids}")
        if len(model_ids) == 4:
            print(f"   ✅ 权限过滤正确（返回所有4个模型）")
        else:
            print(f"   ❌ 应该返回4个模型，实际返回 {len(model_ids)} 个")
    else:
        print(f"   ❌ 失败: {response.json()}")


if __name__ == "__main__":
    print("\n🚀 开始运行严格模式安全验证测试\n")
    print("⚠️  注意: 请确保后端服务已启动 (uvicorn main:app --reload)")
    
    try:
        results = []
        
        results.append(("无认证请求拒绝", test_no_authorization()))
        results.append(("无效认证拒绝", test_invalid_authorization()))
        results.append(("越权访问拒绝", test_valid_but_unauthorized()))
        results.append(("/models无认证拒绝", test_models_endpoint_no_auth()))
        
        print_section("测试5: /models接口角色过滤")
        test_models_endpoint_with_role()
        
        # 汇总结果
        print_section("测试结果汇总")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status} - {test_name}")
        
        print(f"\n总计: {passed}/{total} 测试通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！严格模式已正确实现。")
            print("\n✅ 安全特性:")
            print("   • 无Authorization头 → 401拒绝")
            print("   • 无效API Key → 401拒绝")
            print("   • 越权访问 → 403拒绝")
            print("   • 有效认证+有权 → 200成功")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败，请检查问题。")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("请先启动后端服务: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
