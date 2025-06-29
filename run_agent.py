#!/usr/bin/env python3
"""
Quick start script for the European Electricity Market Analysis Agent
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.electricity_agent import ask_electricity_agent, get_electricity_load, get_supported_countries

def main():
    print("🔌 European Electricity Market Analysis Agent")
    print("=" * 50)
    
    # Quick configuration check
    if not os.environ.get('ENTSOE_API_TOKEN'):
        print("⚠️  ENTSOE API Token not found!")
        print("   Please set ENTSOE_API_TOKEN in your environment or config/.env file")
        print("   Get your token at: https://transparency.entsoe.eu/")
        print()
        return
    
    print("✅ Configuration looks good!")
    print()
    
    # Quick test
    print("🧪 Running quick test...")
    try:
        test_result = get_electricity_load('DE', 6)
        if test_result.get('status') == 'success':
            points = test_result.get('total_points', 0)
            print(f"✅ Test successful! Retrieved {points} data points for Germany")
        else:
            print(f"❌ Test failed: {test_result.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"❌ Test error: {e}")
        return
    
    print()
    print("🚀 Agent is ready! Try these example queries:")
    print("   • What's the current electricity situation in Germany?")
    print("   • Compare electricity prices between France and Italy")
    print("   • Show me renewable energy forecast for Spain")
    print("   • Analyze cross-border flows between Germany and France")
    print()
    print("Type 'exit' to quit")
    print("-" * 50)
    
    # Interactive loop
    while True:
        try:
            query = input("\n🔌 Your question: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            print("\n🤖 Agent: ", end="", flush=True)
            response = ask_electricity_agent(query)
            print(response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
