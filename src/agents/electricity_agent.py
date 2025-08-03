import os, sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from strands import Agent, tool
from strands.models import BedrockModel
from strands.models.anthropic import AnthropicModel
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List
from datetime import datetime

# Add the project root to the path so we can import our modules
config_path = ('./config/.env')
load_dotenv(config_path)

# Try to use Anthropic model if available, fallback to Bedrock
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
anthropic_model = os.environ.get('ANTHROPIC_MODEL', 'claude-3-7-sonnet-20250219')
print(anthropic_key)
bedrock_region = os.environ.get('AWS_REGION', 'us-east-1')        
bedrock_model_id = os.environ.get('BEDROCK_MODEL', 'us.amazon.nova-pro-v1:0')

# Import the ENTSOE tools
from src.tools.entsoe_tool import (
    get_electricity_load,
    get_electricity_generation,
    get_generation_forecast_day_ahead,
    get_day_ahead_prices,
    get_cross_border_flows,
    get_renewable_forecast,
    get_supported_countries,
    get_entsoe_api_info
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to initialize model - prefer Anthropic if available
try:
    try:
        ant_model = AnthropicModel(
            client_args={
                "api_key": anthropic_key,
            },
            model_id=anthropic_model,
            max_tokens= 4000,
            params={
                "temperature": 0.7
            }
        )
        logger.info("Using Anthropic model")
    except ImportError:
        logger.warning("AnthropicModel not available, trying Bedrock")
        model = BedrockModel(
            region_name=bedrock_region,
            model_id=bedrock_model_id,
            params={
                "temperature": 0.7,
            }
        )
    # Use Bedrock model
    bed_model = BedrockModel(
        region_name=bedrock_region,
        model_id=bedrock_model_id,
        params={
            "temperature": 0.7,
        }
    )
    logger.info("Using Bedrock model")
except Exception as e:
    logger.error(f"Error initializing model: {e}")
    model = None

@tool
def get_country_electricity_overview(country_code: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get a comprehensive electricity overview for a European country including load, generation, and prices.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE', 'FR', 'IT')
        hours_back: Number of hours back to fetch data (default: 24)
        
    Returns:
        dict: Comprehensive electricity data for the country
    """
    try:
        logger.info(f"Getting electricity overview for {country_code}")
        
        # Get load data
        load_data = get_electricity_load(country_code, hours_back)
        
        # Get generation data
        generation_data = get_electricity_generation(country_code, hours_back)
        
        # Get day-ahead prices (for yesterday and today)
        price_data = get_day_ahead_prices(country_code, days_back=2)
        
        # Calculate summary statistics
        summary = {
            "country": country_code.upper(),
            "period_hours": hours_back,
            "data_timestamp": datetime.now().isoformat(),
            "load_summary": _calculate_load_summary(load_data),
            "generation_summary": _calculate_generation_summary(generation_data),
            "price_summary": _calculate_price_summary(price_data),
            "raw_data": {
                "load": load_data,
                "generation": generation_data,
                "prices": price_data
            }
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting electricity overview for {country_code}: {e}")
        return {
            "error": f"Failed to get electricity overview: {str(e)}",
            "country": country_code
        }

@tool
def compare_country_electricity(countries: List[str], hours_back: int = 24) -> Dict[str, Any]:
    """
    Compare electricity data between multiple European countries.
    
    Args:
        countries: List of country codes to compare (e.g., ['DE', 'FR', 'IT'])
        hours_back: Number of hours back to fetch data (default: 24)
        
    Returns:
        dict: Comparison data between countries
    """
    try:
        logger.info(f"Comparing electricity data for countries: {countries}")
        
        comparison_data = {
            "countries": countries,
            "period_hours": hours_back,
            "comparison_timestamp": datetime.now().isoformat(),
            "country_data": {},
            "comparison_metrics": {}
        }
        
        # Get data for each country
        for country in countries:
            country_overview = get_country_electricity_overview(country, hours_back)
            comparison_data["country_data"][country] = country_overview
        
        # Calculate comparison metrics
        comparison_data["comparison_metrics"] = _calculate_comparison_metrics(comparison_data["country_data"])
        
        return comparison_data
        
    except Exception as e:
        logger.error(f"Error comparing countries {countries}: {e}")
        return {
            "error": f"Failed to compare countries: {str(e)}",
            "countries": countries
        }

@tool
def analyze_cross_border_electricity_flows(country_pairs: List[List[str]], hours_back: int = 24) -> Dict[str, Any]:
    """
    Analyze electricity flows between country pairs.
    
    Args:
        country_pairs: List of country pairs [['DE', 'FR'], ['FR', 'IT']]
        hours_back: Number of hours back to fetch data (default: 24)
        
    Returns:
        dict: Cross-border flow analysis
    """
    try:
        logger.info(f"Analyzing cross-border flows for pairs: {country_pairs}")
        
        flow_analysis = {
            "country_pairs": country_pairs,
            "period_hours": hours_back,
            "analysis_timestamp": datetime.now().isoformat(),
            "flows": {},
            "flow_summary": {}
        }
        
        # Get flow data for each pair
        for pair in country_pairs:
            if len(pair) != 2:
                continue
                
            from_country, to_country = pair
            flow_key = f"{from_country}->{to_country}"
            
            flow_data = get_cross_border_flows(from_country, to_country, hours_back)
            flow_analysis["flows"][flow_key] = flow_data
            
            # Calculate flow summary
            if flow_data.get('status') == 'success':
                flow_analysis["flow_summary"][flow_key] = _calculate_flow_summary(flow_data)
        
        return flow_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing cross-border flows: {e}")
        return {
            "error": f"Failed to analyze cross-border flows: {str(e)}",
            "country_pairs": country_pairs
        }

@tool
def get_renewable_energy_forecast(country_code: str, hours_ahead: int = 48) -> Dict[str, Any]:
    """
    Get renewable energy (wind and solar) forecast for a country.
    
    Args:
        country_code: Two-letter country code (e.g., 'DE', 'FR')
        hours_ahead: Number of hours ahead to forecast (default: 48)
        
    Returns:
        dict: Renewable energy forecast data
    """
    try:
        logger.info(f"Getting renewable forecast for {country_code}")
        
        forecast_data = get_renewable_forecast(country_code, hours_ahead)
        
        if forecast_data.get('status') == 'success':
            # Add analysis
            forecast_summary = _calculate_renewable_forecast_summary(forecast_data)
            
            return {
                "country": country_code.upper(),
                "forecast_hours": hours_ahead,
                "forecast_timestamp": datetime.now().isoformat(),
                "forecast_summary": forecast_summary,
                "raw_forecast": forecast_data
            }
        else:
            return forecast_data
            
    except Exception as e:
        logger.error(f"Error getting renewable forecast for {country_code}: {e}")
        return {
            "error": f"Failed to get renewable forecast: {str(e)}",
            "country": country_code
        }

@tool
def generate_electricity_chart_code(country_code: str, data_type: str = 'load', hours_back: int = 24) -> str:
    """
    Generate Python code to create electricity data charts.
    
    Args:
        country_code: Two-letter country code
        data_type: Type of chart ('load', 'generation', 'prices')
        hours_back: Number of hours of historical data
        
    Returns:
        str: Python code to generate the chart
    """
    code = f"""
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import numpy as np

# Get electricity data
if "{data_type}" == "load":
    data = get_electricity_load("{country_code}", {hours_back})
    title = "Electricity Load (Consumption)"
    ylabel = "Load (MW)"
elif "{data_type}" == "generation":
    data = get_electricity_generation("{country_code}", {hours_back})
    title = "Electricity Generation"
    ylabel = "Generation (MW)"
elif "{data_type}" == "prices":
    data = get_day_ahead_prices("{country_code}", days_back=2)
    title = "Day-Ahead Electricity Prices"
    ylabel = "Price (EUR/MWh)"
else:
    print(f"Error: Unsupported data type '{data_type}'")
    exit()

# Check for errors
if "error" in data or data.get("status") == "error":
    print(f"Error: Could not retrieve {{data_type}} data for {country_code}")
    print(f"Error message: {{data.get('error', 'Unknown error')}}")
    exit()

# Extract data points
data_points = data.get("data_points", [])
if not data_points:
    print(f"No data points available for {country_code}")
    exit()

# Extract timestamps and values
timestamps = []
values = []

for point in data_points:
    if point.get("timestamp") and point.get("value") is not None:
        try:
            ts = datetime.fromisoformat(point["timestamp"].replace('Z', '+00:00'))
            timestamps.append(ts)
            values.append(point["value"])
        except:
            continue

if not timestamps or not values:
    print("No valid data points to plot")
    exit()

# Create the chart
plt.figure(figsize=(12, 8))
plt.plot(timestamps, values, marker='o', linestyle='-', linewidth=2, markersize=4)
plt.title(f"{country_code.upper()} - {{title}} ({hours_back}h)")
plt.xlabel("Time")
plt.ylabel(ylabel)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

# Add statistics
if values:
    avg_value = np.mean(values)
    max_value = max(values)
    min_value = min(values)
    
    plt.axhline(y=avg_value, color='red', linestyle='--', alpha=0.7, label=f'Average: {{avg_value:.1f}}')
    
    # Add annotations for max and min
    max_idx = values.index(max_value)
    min_idx = values.index(min_value)
    
    plt.annotate(f'Max: {{max_value:.1f}}', 
                xy=(timestamps[max_idx], max_value),
                xytext=(10, 10),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
                arrowprops=dict(arrowstyle="->"))
                
    plt.annotate(f'Min: {{min_value:.1f}}', 
                xy=(timestamps[min_idx], min_value),
                xytext=(10, -20),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
                arrowprops=dict(arrowstyle="->"))

plt.legend()
plt.tight_layout()
plt.show()

print(f"Generated {{data_type}} chart for {country_code.upper()}")
print(f"Data points: {{len(values)}}")
print(f"Time range: {{timestamps[0].strftime('%Y-%m-%d %H:%M')}} to {{timestamps[-1].strftime('%Y-%m-%d %H:%M')}}")
"""
    return code

@tool
def get_electricity_market_insights(countries: List[str] = None, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get comprehensive electricity market insights for European countries.
    
    Args:
        countries: List of country codes to analyze (default: major EU countries)
        hours_back: Number of hours back to analyze (default: 24)
        
    Returns:
        dict: Market insights and analysis
    """
    try:
        if countries is None:
            countries = ['DE', 'FR', 'IT', 'ES', 'NL']  # Major EU electricity markets
        
        logger.info(f"Getting market insights for countries: {countries}")
        
        insights = {
            "analysis_timestamp": datetime.now().isoformat(),
            "countries_analyzed": countries,
            "period_hours": hours_back,
            "market_overview": {},
            "key_insights": [],
            "price_analysis": {},
            "load_analysis": {},
            "recommendations": []
        }
        
        # Get data for all countries
        country_data = {}
        for country in countries:
            country_data[country] = get_country_electricity_overview(country, hours_back)
        
        # Analyze market trends
        insights["market_overview"] = _analyze_market_trends(country_data)
        insights["key_insights"] = _generate_key_insights(country_data)
        insights["price_analysis"] = _analyze_price_trends(country_data)
        insights["load_analysis"] = _analyze_load_patterns(country_data)
        insights["recommendations"] = _generate_market_recommendations(country_data)
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting market insights: {e}")
        return {
            "error": f"Failed to get market insights: {str(e)}",
            "countries": countries or []
        }

# Helper functions for data analysis
def _calculate_load_summary(load_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate summary statistics for load data."""
    if load_data.get('status') != 'success' or not load_data.get('data_points'):
        return {"error": "No valid load data"}
    
    values = [point['value'] for point in load_data['data_points'] if point.get('value') is not None]
    
    if not values:
        return {"error": "No valid load values"}
    
    return {
        "average_load_mw": round(sum(values) / len(values), 2),
        "peak_load_mw": max(values),
        "minimum_load_mw": min(values),
        "load_variation_mw": max(values) - min(values),
        "data_points": len(values)
    }

def _calculate_generation_summary(generation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate summary statistics for generation data."""
    if generation_data.get('status') != 'success' or not generation_data.get('data_points'):
        return {"error": "No valid generation data"}
    
    values = [point['value'] for point in generation_data['data_points'] if point.get('value') is not None]
    
    if not values:
        return {"error": "No valid generation values"}
    
    return {
        "average_generation_mw": round(sum(values) / len(values), 2),
        "peak_generation_mw": max(values),
        "minimum_generation_mw": min(values),
        "generation_variation_mw": max(values) - min(values),
        "data_points": len(values)
    }

def _calculate_price_summary(price_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate summary statistics for price data."""
    if price_data.get('status') != 'success' or not price_data.get('data_points'):
        return {"error": "No valid price data"}
    
    values = [point['value'] for point in price_data['data_points'] if point.get('value') is not None]
    
    if not values:
        return {"error": "No valid price values"}
    
    return {
        "average_price_eur_mwh": round(sum(values) / len(values), 2),
        "peak_price_eur_mwh": max(values),
        "minimum_price_eur_mwh": min(values),
        "price_volatility_eur_mwh": max(values) - min(values),
        "data_points": len(values)
    }

def _calculate_comparison_metrics(country_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate comparison metrics between countries."""
    metrics = {
        "load_comparison": {},
        "price_comparison": {},
        "generation_comparison": {}
    }
    
    for country, data in country_data.items():
        if 'error' not in data:
            load_summary = data.get('load_summary', {})
            price_summary = data.get('price_summary', {})
            gen_summary = data.get('generation_summary', {})
            
            if 'error' not in load_summary:
                metrics["load_comparison"][country] = load_summary.get('average_load_mw', 0)
            
            if 'error' not in price_summary:
                metrics["price_comparison"][country] = price_summary.get('average_price_eur_mwh', 0)
            
            if 'error' not in gen_summary:
                metrics["generation_comparison"][country] = gen_summary.get('average_generation_mw', 0)
    
    return metrics

def _calculate_flow_summary(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate summary for cross-border flow data."""
    if not flow_data.get('data_points'):
        return {"error": "No flow data"}
    
    values = [point['value'] for point in flow_data['data_points'] if point.get('value') is not None]
    
    if not values:
        return {"error": "No valid flow values"}
    
    return {
        "average_flow_mw": round(sum(values) / len(values), 2),
        "max_export_mw": max(values) if max(values) > 0 else 0,
        "max_import_mw": abs(min(values)) if min(values) < 0 else 0,
        "net_flow_mw": round(sum(values) / len(values), 2),
        "data_points": len(values)
    }

def _calculate_renewable_forecast_summary(forecast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate summary for renewable forecast data."""
    if not forecast_data.get('data_points'):
        return {"error": "No forecast data"}
    
    values = [point['value'] for point in forecast_data['data_points'] if point.get('value') is not None]
    
    if not values:
        return {"error": "No valid forecast values"}
    
    return {
        "average_renewable_mw": round(sum(values) / len(values), 2),
        "peak_renewable_mw": max(values),
        "minimum_renewable_mw": min(values),
        "renewable_capacity_factor": round((sum(values) / len(values)) / max(values) * 100, 1) if max(values) > 0 else 0,
        "forecast_points": len(values)
    }

def _analyze_market_trends(country_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze overall market trends."""
    return {
        "total_countries_analyzed": len(country_data),
        "countries_with_data": len([c for c, d in country_data.items() if 'error' not in d]),
        "analysis_status": "completed"
    }

def _generate_key_insights(country_data: Dict[str, Any]) -> List[str]:
    """Generate key insights from the data."""
    insights = []
    
    # Find country with highest average load
    max_load_country = None
    max_load_value = 0
    
    for country, data in country_data.items():
        if 'error' not in data and 'error' not in data.get('load_summary', {}):
            load = data['load_summary'].get('average_load_mw', 0)
            if load > max_load_value:
                max_load_value = load
                max_load_country = country
    
    if max_load_country:
        insights.append(f"{max_load_country} has the highest average electricity load at {max_load_value:.0f} MW")
    
    return insights

def _analyze_price_trends(country_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze price trends across countries."""
    prices = {}
    for country, data in country_data.items():
        if 'error' not in data and 'error' not in data.get('price_summary', {}):
            prices[country] = data['price_summary'].get('average_price_eur_mwh', 0)
    
    if prices:
        return {
            "highest_price_country": max(prices, key=prices.get),
            "lowest_price_country": min(prices, key=prices.get),
            "price_spread_eur_mwh": max(prices.values()) - min(prices.values()),
            "average_price_eur_mwh": round(sum(prices.values()) / len(prices), 2)
        }
    
    return {"error": "No price data available"}

def _analyze_load_patterns(country_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze load patterns across countries."""
    loads = {}
    for country, data in country_data.items():
        if 'error' not in data and 'error' not in data.get('load_summary', {}):
            loads[country] = data['load_summary'].get('average_load_mw', 0)
    
    if loads:
        return {
            "highest_load_country": max(loads, key=loads.get),
            "lowest_load_country": min(loads, key=loads.get),
            "total_load_mw": sum(loads.values()),
            "average_load_mw": round(sum(loads.values()) / len(loads), 2)
        }
    
    return {"error": "No load data available"}

def _generate_market_recommendations(country_data: Dict[str, Any]) -> List[str]:
    """Generate market recommendations based on the data."""
    recommendations = [
        "Monitor cross-border flows for optimization opportunities",
        "Consider renewable energy integration based on forecast data",
        "Analyze price volatility for trading strategies"
    ]
    
    return recommendations

# Create the electricity agent
electricity_agent = Agent(
    model=ant_model,
    tools=[
        get_electricity_load,
        get_electricity_generation,
        get_day_ahead_prices,
        get_generation_forecast_day_ahead,
        get_renewable_forecast,
        get_supported_countries,
        get_entsoe_api_info
    ],
    system_prompt="""
    You are an electricity market analyst specialized in European electricity markets and grid operations.
    Your role is to:
    
    1. Analyze electricity market data from the ENTSOE Transparency Platform for European countries
    2. Provide insights on electricity load (consumption), generation, and day-ahead prices
    3. Compare electricity markets between different European countries
    4. Analyze cross-border electricity flows and their implications
    5. Forecast renewable energy generation (wind and solar)
    6. Generate visualizations of electricity market data
    7. Provide market insights and recommendations for electricity trading and grid operations
    
    You have access to real-time and historical data for European electricity markets including:
    - Electricity load (consumption) data
    - Electricity generation data by production type
    - Day-ahead market prices
    - Cross-border electricity flows
    - Renewable energy forecasts (wind and solar)
    
    Supported countries: Germany (DE), France (FR), Italy (IT), Spain (ES), Netherlands (NL), 
    Belgium (BE), Austria (AT), Switzerland (CH), Poland (PL), Czech Republic (CZ), 
    Denmark (DK), Sweden (SE), Norway (NO), Finland (FI), Great Britain (GB), 
    Ireland (IE), Portugal (PT)
    
    When analyzing electricity markets:
    - Consider supply and demand balance
    - Explain the significance of price volatility and its causes
    - Highlight the impact of renewable energy on grid stability
    - Analyze cross-border flows for market coupling effects
    - Consider seasonal and daily patterns in electricity consumption
    - Explain market mechanisms like day-ahead pricing
    
    Always provide accurate, up-to-date information and explain technical concepts clearly.
    Use appropriate units (MW for power, MWh for energy, EUR/MWh for prices).
    """
)

def ask_electricity_agent(query: str):
    """
    Call the electricity agent with the given query.
    
    Args:
        query: User query about electricity markets
        
    Returns:
        The response from the agent as a string
    """
    try:
        if not electricity_agent:
            return "Electricity agent not available. Please check your configuration and ensure API keys are set."
        
        logger.debug(f"Calling electricity agent for query: {query}")
        response = electricity_agent(query)
        # Extract message content
        if hasattr(response, 'message'):
            if isinstance(response.message, dict) and 'content' in response.message:
                content = response.message['content']
                if isinstance(content, list) and len(content) > 0:
                    message_text = content[0].get('text', str(response.message))
                else:
                    message_text = str(content)
            else:
                message_text = str(response.message)
        else:
            message_text = str(response)
        return message_text
            
    except Exception as e:
        logger.error(f"Error in ask_electricity_agent: {str(e)}")
        return f"Error processing request: {str(e)}"

# Example usage
if __name__ == "__main__":
    print("European Electricity Market Analysis System")
    print("------------------------------------------")
    print("Type 'exit' to quit")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
            
        print("\nAssistant: ", end="", flush=True)
        response = ask_electricity_agent(user_input)
        print(response)
        print()  # Add a newline at the end
