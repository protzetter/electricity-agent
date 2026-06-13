#!/usr/bin/env python3
"""
Simple test functions for all ENTSOE tools.
Usage: python test_all_tools.py [country_code]
Example: python test_all_tools.py DE
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src/tools'))
# Add the project root to the path so we can import our modules
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config/.env')
load_dotenv(config_path)

# Also try loading from current directory and parent directories as fallback
load_dotenv()  # Load from current directory
load_dotenv(dotenv_path='.env')  # Load from .env in current dir
load_dotenv(dotenv_path='config/.env')  # Load from config/.env

def test_electricity_load(country_code):
    """Test electricity load function."""
    print(f"🔋 Testing Electricity Load for {country_code}")
    print("-" * 40)
    
    try:
        from entsoe_tool import get_electricity_load
        result = get_electricity_load(country_code, 12)
        
        if result['status'] == 'success':
            print(f"✅ SUCCESS: {result['total_points']} data points")
            print(f"⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}")
            print(f"🕐 Data delay: {result['time_range']['data_delay_hours']} hours")
            
            if result['data_points']:
                sample = result['data_points'][0]
                value = sample.get('value', sample.get('load_mw', 'unknown'))
                print(f"📊 Sample: {sample['timestamp']} - {value} MW")
        else:
            print(f"❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_electricity_generation(country_code):
    """Test electricity generation function."""
    print(f"\n⚡ Testing Electricity Generation for {country_code}")
    print("-" * 45)
    
    try:
        from entsoe_tool import get_electricity_generation
        result = get_electricity_generation(country_code, 12)
        
        if result['status'] == 'success':
            print(f"✅ SUCCESS: {result['total_points']} data points")
            print(f"⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}")
            print(f"🕐 Data delay: {result['time_range']['data_delay_hours']} hours")
            
            if result['data_points']:
                sample = result['data_points'][0]
                value = sample.get('value', 'unknown')
                print(f"📊 Sample: {sample['timestamp']} - {value} MW")
        else:
            print(f"❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_day_ahead_prices(country_code):
    """Test day-ahead prices function."""
    print(f"\n💰 Testing Day-Ahead Prices for {country_code}")
    print("-" * 40)
    
    try:
        from entsoe_tool import get_day_ahead_prices
        result = get_day_ahead_prices(country_code, 1)
        
        if result['status'] == 'success':
            print(f"✅ SUCCESS: {result['total_points']} data points")
            print(f"📅 Target date: {result['time_range']['target_date']}")
            print(f"💱 Currency: {result.get('currency', 'EUR')}")
            
            if result['data_points']:
                sample = result['data_points'][0]
                value = sample.get('value', 'unknown')
                unit = sample.get('unit', 'EUR/MWh')
                print(f"💶 Sample: {sample['timestamp']} - {value} {unit}")
        else:
            print(f"❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_renewable_forecast(country_code):
    """Test renewable forecast function."""
    print(f"\n🌱 Testing Renewable Forecast for {country_code}")
    print("-" * 40)
    
    try:
        from entsoe_tool import get_renewable_forecast
        result = get_renewable_forecast(country_code, 24)
        
        if result['status'] == 'success':
            print(f"✅ SUCCESS: {result['total_points']} data points")
            print(f"⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}")
            print(f"🕐 Forecast delay: {result['time_range']['forecast_delay_hours']} hours")
            print(f"🔧 Method used: {result.get('method_used', 'unknown')}")
            print(f"🌿 Forecast types: {result.get('forecast_types', [])}")
            
            if result['data_points']:
                sample = result['data_points'][0]
                value = sample.get('value', 'unknown')
                unit = sample.get('unit', 'MW')
                print(f"📈 Sample: {sample['timestamp']} - {value} {unit}")
        else:
            print(f"❌ FAILED: {result['error']}")
            if 'suggestions' in result:
                print("💡 Suggestions:")
                for suggestion in result['suggestions'][:2]:
                    print(f"   • {suggestion}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_unavailability_production_units(country_code):
    """Test unavailability production units function."""
    print(f"\n🔧 Testing Unavailability Production Units for {country_code}")
    print("-" * 55)
    
    try:
        from entsoe_tool import get_unavailability_production_units
        result = get_unavailability_production_units(country_code)
        
        if result['status'] == 'success':
            print(f"✅ SUCCESS: {result['total_points']} unavailability events")
            print(f"⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}")
            print(f"🕐 Data delay: {result['time_range']['data_delay_hours']} hours")
            print(f"🏭 Affected units: {len(result.get('affected_units', []))}")
            print(f"🏷️  Types: {result.get('unavailability_types', [])}")
            print(f"📁 Format: {result.get('response_format', 'XML')}")
            
            if result.get('affected_units'):
                units = result['affected_units'][:3]  # First 3 units
                print(f"🏭 Sample units: {units}")
        else:
            print(f"❌ FAILED: {result['error']}")
            if 'suggestions' in result:
                print("💡 Suggestions:")
                for suggestion in result['suggestions'][:2]:
                    print(f"   • {suggestion}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_actual_generation_per_unit(country_code):
    """Test actual generation per unit function."""
    print(f"\n🏭 Testing Actual Generation Per Unit for {country_code}")
    print("-" * 50)
    
    try:
        from entsoe_tool import get_actual_generation_per_unit
        result = get_actual_generation_per_unit(country_code)
        
        if result['status'] == 'success':
            print(f"✅ SUCCESS: {result['total_points']} data points")
            print(f"⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}")
            print(f"🕐 Data delay: {result['time_range']['data_delay_hours']} hours")
            print(f"🏭 Total units: {len(result.get('generation_units', []))}")
            print(f"⚡ Generation types: {result.get('generation_types', [])}")
            
            if result.get('generation_units'):
                units = result['generation_units'][:3]  # First 3 units
                print(f"🏭 Sample units: {units}")
            
            if result['data_points']:
                sample = result['data_points'][0]
                value = sample.get('value', sample.get('generation_mw', 'unknown'))
                unit_name = sample.get('unit_name', 'unknown')
                gen_type = sample.get('generation_type', 'unknown')
                print(f"📊 Sample: {sample['timestamp']} - {unit_name} ({gen_type}): {value} MW")
        else:
            print(f"❌ FAILED: {result['error']}")
            if 'suggestions' in result:
                print("💡 Suggestions:")
                for suggestion in result['suggestions'][:2]:
                    print(f"   • {suggestion}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_generation_forecast_day_ahead(country_code):
    """Test generation forecast day ahead function."""
    print(f"\n📈 Testing Generation Forecast Day Ahead for {country_code}")
    print("-" * 50)
    
    try:
        from entsoe_tool import get_generation_forecast_day_ahead
        result = get_generation_forecast_day_ahead(country_code, 1)
        
        if result['status'] == 'success':
            print(f"✅ SUCCESS: {result['total_points']} data points")
            print(f"⏰ Time range: {result.get('time_range', {}).get('start', 'unknown')} to {result.get('time_range', {}).get('end', 'unknown')}")
            
            if result['data_points']:
                sample = result['data_points'][0]
                value = sample.get('value', 'unknown')
                unit = sample.get('unit', 'MW')
                print(f"📊 Sample: {sample['timestamp']} - {value} {unit}")
        else:
            print(f"❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def run_all_tests(country_code):
    """Run all tests for a given country code."""
    print(f"🧪 ENTSOE Tools Test Suite for {country_code.upper()}")
    print("=" * 60)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all functions
    test_electricity_load(country_code)
    test_electricity_generation(country_code)
 #   test_actual_generation_per_unit(country_code)
    test_day_ahead_prices(country_code)
    test_renewable_forecast(country_code)
    test_generation_forecast_day_ahead(country_code)
    
    print(f"\n" + "=" * 60)
    print("✅ All tests completed!")
    print(f"\n💡 SUMMARY FOR {country_code.upper()}:")
    print("   • Load data: Historical electricity consumption")
    print("   • Generation data: Actual electricity production by source")
 #   print("   • Generation per unit: Individual power plant/unit generation")
    print("   • Day-ahead prices: Market prices for electricity")
    print("   • Renewable forecast: Wind and solar predictions")
    print("   • Generation forecast: Predicted total generation")

def show_supported_countries():
    """Show list of supported countries."""
    countries = {
        'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'ES': 'Spain',
        'NL': 'Netherlands', 'BE': 'Belgium', 'AT': 'Austria', 'CH': 'Switzerland',
        'PL': 'Poland', 'CZ': 'Czech Republic', 'DK': 'Denmark', 'SE': 'Sweden',
        'NO': 'Norway', 'FI': 'Finland', 'GB': 'Great Britain', 'IE': 'Ireland',
        'PT': 'Portugal'
    }
    
    print("🌍 SUPPORTED COUNTRIES:")
    print("=" * 25)
    for code, name in countries.items():
        print(f"   {code}: {name}")

def interactive_mode():
    """Interactive mode for testing different countries."""
    print("🔄 INTERACTIVE MODE")
    print("=" * 20)
    print("Enter country codes to test (or 'quit' to exit)")
    print("Examples: DE, FR, IT, ES, NL, BE")
    
    while True:
        try:
            country = input("\n🌍 Enter country code: ").strip().upper()
            
            if country in ['QUIT', 'EXIT', 'Q']:
                print("👋 Goodbye!")
                break
            elif country == 'HELP':
                show_supported_countries()
            elif len(country) == 2:
                run_all_tests(country)
            else:
                print("❌ Please enter a 2-letter country code (e.g., DE, FR, IT)")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        country_code = sys.argv[1].upper()
        if country_code == 'HELP':
            show_supported_countries()
        else:
            run_all_tests(country_code)
    else:
        # Interactive mode
        print("🧪 ENTSOE Tools Test Suite")
        print("=" * 30)
        print("Usage:")
        print("  python test_all_tools.py DE     # Test Germany")
        print("  python test_all_tools.py FR     # Test France") 
        print("  python test_all_tools.py help   # Show countries")
        print("  python test_all_tools.py        # Interactive mode")
        
        choice = input("\nPress Enter for interactive mode, or Ctrl+C to exit: ")
        interactive_mode()
