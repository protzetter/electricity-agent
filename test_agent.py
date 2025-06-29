#!/usr/bin/env python3
"""
Test script for the European Electricity Market Analysis Agent
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_entsoe_tools():
    """Test the ENTSOE tools directly."""
    print("🧪 Testing ENTSOE Tools")
    print("-" * 30)
    
    try:
        from tools.entsoe_tool import (
            get_electricity_load, 
            get_supported_countries, 
            get_entsoe_api_info,
            debug_entsoe_request
        )
        
        # Test 1: Get supported countries
        print("1. Testing get_supported_countries...")
        countries = get_supported_countries()
        if countries.get('status') == 'success':
            print(f"   ✅ Found {countries.get('total_countries')} supported countries")
        else:
            print(f"   ❌ Failed: {countries.get('error')}")
        
        # Test 2: Get API info
        print("\n2. Testing get_entsoe_api_info...")
        api_info = get_entsoe_api_info()
        if api_info.get('status') == 'success':
            print(f"   ✅ API info retrieved: {api_info.get('api_name')}")
        else:
            print(f"   ❌ Failed: {api_info.get('error')}")
        
        # Test 3: Debug request
        print("\n3. Testing debug_entsoe_request...")
        debug_info = debug_entsoe_request('DE', 'load')
        if debug_info.get('status') == 'success':
            print(f"   ✅ Debug info for Germany load: {debug_info.get('area_code')}")
        else:
            print(f"   ❌ Failed: {debug_info.get('error')}")
        
        # Test 4: Actual data request (if API token available)
        if os.environ.get('ENTSOE_API_TOKEN'):
            print("\n4. Testing actual data request...")
            load_data = get_electricity_load('DE', 6)  # 6 hours of data
            if load_data.get('status') == 'success':
                points = load_data.get('total_points', 0)
                print(f"   ✅ Retrieved {points} data points for Germany")
                if points > 0:
                    sample = load_data['data_points'][0]
                    print(f"   📊 Sample: {sample['timestamp']} = {sample['value']} {sample['unit']}")
            else:
                print(f"   ❌ Failed: {load_data.get('error')}")
        else:
            print("\n4. Skipping data request (no API token)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ENTSOE tools: {e}")
        return False

def test_agent():
    """Test the electricity agent."""
    print("\n🤖 Testing Electricity Agent")
    print("-" * 30)
    
    try:
        from agents.electricity_agent import ask_electricity_agent, electricity_agent
        
        if not electricity_agent:
            print("⚠️  Agent not available (Strands framework may not be installed)")
            return False
        
        # Simple test query
        print("Testing with simple query...")
        response = ask_electricity_agent("What countries do you support?")
        
        # Handle AgentResult object or string response
        response_text = str(response)
        if hasattr(response, 'content'):
            response_text = str(response.content)
        elif hasattr(response, 'text'):
            response_text = str(response.text)
        
        if "error" not in response_text.lower():
            print("✅ Agent responded successfully")
            print(f"📝 Response preview: {response_text[:100]}...")
            return True
        else:
            print(f"❌ Agent error: {response_text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False

def main():
    print("🔌 European Electricity Market Analysis Agent - Test Suite")
    print("=" * 60)
    
    # Check environment
    print("🔧 Environment Check")
    print("-" * 20)
    
    api_token = os.environ.get('ENTSOE_API_TOKEN')
    if api_token:
        print(f"✅ ENTSOE API Token: Found (length: {len(api_token)})")
    else:
        print("⚠️  ENTSOE API Token: Not found")
    
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_key:
        print(f"✅ Anthropic API Key: Found (length: {len(anthropic_key)})")
    else:
        print("⚠️  Anthropic API Key: Not found")
    
    aws_region = os.environ.get('AWS_REGION')
    if aws_region:
        print(f"✅ AWS Region: {aws_region}")
    else:
        print("⚠️  AWS Region: Not set")
    
    print()
    
    # Test ENTSOE tools
    tools_ok = test_entsoe_tools()
    
    # Test agent (if tools work)
    if tools_ok:
        agent_ok = test_agent()
    else:
        print("\n⚠️  Skipping agent test due to tool failures")
        agent_ok = False
    
    # Summary
    print("\n📋 Test Summary")
    print("-" * 15)
    print(f"ENTSOE Tools: {'✅ PASS' if tools_ok else '❌ FAIL'}")
    print(f"Agent: {'✅ PASS' if agent_ok else '❌ FAIL'}")
    
    if tools_ok and agent_ok:
        print("\n🎉 All tests passed! The agent is ready to use.")
        print("   Run: python run_agent.py")
    elif tools_ok:
        print("\n⚠️  ENTSOE tools work, but agent needs configuration.")
        print("   You can still use the tools directly.")
    else:
        print("\n❌ Tests failed. Please check your configuration.")
        print("   Make sure ENTSOE_API_TOKEN is set in config/.env")

if __name__ == "__main__":
    main()
