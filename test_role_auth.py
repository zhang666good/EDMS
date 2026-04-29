"""
角色权限系统快速测试脚本
用于验证角色API Key生成和权限验证功能
"""

from app.api.role_auth import (
    get_role_from_api_key,
    validate_role_access,
    get_allowed_agents_for_role,
    generate_role_api_key,
    list_available_roles
)


def test_role_identification():
    """测试1: API Key角色识别"""
    print("=" * 60)
    print("测试1: API Key角色识别")
    print("=" * 60)
    
    # 生成测试API Keys
    power_key = generate_role_api_key("power_expert", "test1234")
    business_key = generate_role_api_key("business_analyst", "test5678")
    decision_key = generate_role_api_key("decision_maker", "test9012")
    
    print(f"\n生成的API Keys:")
    print(f"  电力行业专家: {power_key}")
    print(f"  企业分析师:   {business_key}")
    print(f"  综合决策者:   {decision_key}")
    
    # 测试识别
    assert get_role_from_api_key(power_key) == "power_expert", "电力专家识别失败"
    assert get_role_from_api_key(business_key) == "business_analyst", "企业分析师识别失败"
    assert get_role_from_api_key(decision_key) == "decision_maker", "综合决策者识别失败"
    assert get_role_from_api_key("invalid-key") is None, "无效Key应返回None"
    assert get_role_from_api_key("") is None, "空Key应返回None"
    
    print("\n✅ 角色识别测试通过\n")


def test_permission_validation():
    """测试2: 权限验证"""
    print("=" * 60)
    print("测试2: 权限验证")
    print("=" * 60)
    
    # 电力行业专家权限测试
    print("\n电力行业专家 (power_expert):")
    assert validate_role_access("power_expert", "power_standard_query") == True
    print("  ✅ 可访问: power_standard_query")
    
    assert validate_role_access("power_expert", "annual_report_analyst") == False
    print("  ❌ 不可访问: annual_report_analyst")
    
    assert validate_role_access("power_expert", "deep_insight_analyst") == False
    print("  ❌ 不可访问: deep_insight_analyst")
    
    # 企业分析师权限测试
    print("\n企业分析师 (business_analyst):")
    assert validate_role_access("business_analyst", "annual_report_analyst") == True
    print("  ✅ 可访问: annual_report_analyst")
    
    assert validate_role_access("business_analyst", "deep_insight_analyst") == True
    print("  ✅ 可访问: deep_insight_analyst")
    
    assert validate_role_access("business_analyst", "power_standard_query") == False
    print("  ❌ 不可访问: power_standard_query")
    
    # 综合决策者权限测试
    print("\n综合决策者 (decision_maker):")
    for agent in ["power_standard_query", "annual_report_analyst", 
                  "deep_insight_analyst", "auto_report_expert"]:
        assert validate_role_access("decision_maker", agent) == True
        print(f"  ✅ 可访问: {agent}")
    
    print("\n✅ 权限验证测试通过\n")


def test_allowed_agents_list():
    """测试3: 获取允许访问的Agent列表"""
    print("=" * 60)
    print("测试3: 获取允许访问的Agent列表")
    print("=" * 60)
    
    power_agents = get_allowed_agents_for_role("power_expert")
    print(f"\n电力行业专家可访问的Agent: {power_agents}")
    assert power_agents == {"power_standard_query"}
    
    business_agents = get_allowed_agents_for_role("business_analyst")
    print(f"企业分析师可访问的Agent: {business_agents}")
    assert business_agents == {"annual_report_analyst", "deep_insight_analyst"}
    
    decision_agents = get_allowed_agents_for_role("decision_maker")
    print(f"综合决策者可访问的Agent: {decision_agents}")
    assert decision_agents == {"power_standard_query", "annual_report_analyst", 
                               "deep_insight_analyst", "auto_report_expert"}
    
    print("\n✅ Agent列表测试通过\n")


def test_list_roles():
    """测试4: 列出所有可用角色"""
    print("=" * 60)
    print("测试4: 列出所有可用角色")
    print("=" * 60)
    
    roles = list_available_roles()
    print(f"\n可用角色数量: {len(roles)}")
    
    for role_name, config in roles.items():
        print(f"\n角色: {role_name}")
        print(f"  显示名称: {config['display_name']}")
        print(f"  描述: {config['description']}")
        print(f"  API Key前缀: {config['api_key_prefix']}")
    
    assert len(roles) == 3, "应该有3个角色"
    assert "power_expert" in roles
    assert "business_analyst" in roles
    assert "decision_maker" in roles
    
    print("\n✅ 角色列表测试通过\n")


def test_bearer_token_format():
    """测试5: Bearer Token格式支持"""
    print("=" * 60)
    print("测试5: Bearer Token格式支持")
    print("=" * 60)
    
    # 模拟从Authorization头提取token
    auth_header = "Bearer edms-power-expert-test1234"
    token = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header
    
    role = get_role_from_api_key(token)
    print(f"\nAuthorization头: {auth_header}")
    print(f"提取的Token: {token}")
    print(f"识别的角色: {role}")
    
    assert role == "power_expert", "Bearer Token格式解析失败"
    
    print("\n✅ Bearer Token格式测试通过\n")


if __name__ == "__main__":
    print("\n🚀 开始运行角色权限系统测试\n")
    
    try:
        test_role_identification()
        test_permission_validation()
        test_allowed_agents_list()
        test_list_roles()
        test_bearer_token_format()
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print("\n系统已就绪，可以开始使用角色权限功能。")
        print("详细使用说明请参考: ROLE_AUTH_GUIDE.md\n")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        raise
    except Exception as e:
        print(f"\n💥 发生错误: {e}\n")
        raise
