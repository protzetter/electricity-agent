#!/usr/bin/env python3
"""
Simple Streamlit Chat Application for European Electricity Market Analysis Agent

A conversational interface for analyzing European electricity markets.
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append('src/agents')
sys.path.append('src/tools')

# Page configuration
st.set_page_config(
    page_title="Electricity Agent Chat",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Title
st.title("⚡ Chat with Electricity Agent")
st.markdown("Ask questions about European electricity markets, prices, generation, and forecasts!")

# Try to import the electricity agent with fallback
agent_available = False
ask_electricity_agent = None

try:
    from electricity_agent import ask_electricity_agent
    agent_available = True
    st.success("✅ Electricity Agent loaded successfully!")
except ImportError:
    try:
        # Fallback: try to create a simple agent function using the tools directly
        from entsoe_tool import (
            get_electricity_load, 
            get_day_ahead_prices, 
            get_electricity_generation,
            get_renewable_forecast
        )
        
        def simple_electricity_agent(query):
            """Simple fallback agent using ENTSOE tools directly"""
            query_lower = query.lower()
            
            # Extract country code (simple pattern matching)
            countries = ['de', 'fr', 'it', 'es', 'nl', 'be', 'at', 'ch', 'pl', 'cz', 'dk', 'se', 'no', 'fi', 'gb', 'ie', 'pt']
            country_names = {
                'germany': 'DE', 'france': 'FR', 'italy': 'IT', 'spain': 'ES',
                'netherlands': 'NL', 'belgium': 'BE', 'austria': 'AT', 'switzerland': 'CH',
                'poland': 'PL', 'czech': 'CZ', 'denmark': 'DK', 'sweden': 'SE',
                'norway': 'NO', 'finland': 'FI', 'britain': 'GB', 'ireland': 'IE', 'portugal': 'PT'
            }
            
            # Find country
            country_code = 'DE'  # Default to Germany
            for country in countries:
                if country in query_lower:
                    country_code = country.upper()
                    break
            for name, code in country_names.items():
                if name in query_lower:
                    country_code = code
                    break
            
            # Determine query type and call appropriate function
            if 'load' in query_lower or 'consumption' in query_lower:
                result = get_electricity_load(country_code, 24)
                if result.get('status') == 'success':
                    avg_load = sum(point['value'] for point in result['data_points']) / len(result['data_points'])
                    return f"**Electricity Load for {country_code}:**\n\n📊 Average load over last 24 hours: **{avg_load:.0f} MW**\n\n✅ Data points: {result['total_points']}\n⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}"
                else:
                    return f"❌ Could not retrieve load data for {country_code}: {result.get('error', 'Unknown error')}"
            
            elif 'price' in query_lower:
                result = get_day_ahead_prices(country_code, 1)
                if result.get('status') == 'success':
                    avg_price = sum(point['value'] for point in result['data_points']) / len(result['data_points'])
                    return f"**Day-Ahead Prices for {country_code}:**\n\n💰 Average price: **{avg_price:.2f} EUR/MWh**\n\n✅ Data points: {result['total_points']}\n📅 Date: {result['time_range']['target_date']}"
                else:
                    return f"❌ Could not retrieve price data for {country_code}: {result.get('error', 'Unknown error')}"
            
            elif 'generation' in query_lower:
                result = get_electricity_generation(country_code, 24)
                if result.get('status') == 'success':
                    avg_gen = sum(point['value'] for point in result['data_points']) / len(result['data_points'])
                    return f"**Electricity Generation for {country_code}:**\n\n⚡ Average generation over last 24 hours: **{avg_gen:.0f} MW**\n\n✅ Data points: {result['total_points']}\n⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}"
                else:
                    return f"❌ Could not retrieve generation data for {country_code}: {result.get('error', 'Unknown error')}"
            
            elif 'renewable' in query_lower or 'forecast' in query_lower:
                result = get_renewable_forecast(country_code, 24)
                if result.get('status') == 'success':
                    return f"**Renewable Forecast for {country_code}:**\n\n🌱 Forecast points: {result['total_points']}\n⏰ Time range: {result['time_range']['start']} to {result['time_range']['end']}\n🔧 Method: {result.get('method_used', 'Unknown')}"
                else:
                    return f"❌ Could not retrieve renewable forecast for {country_code}: {result.get('error', 'Unknown error')}"
            
            else:
                return f"""I can help you with electricity market data for European countries! 

**Try asking:**
- "What's the electricity load in Germany?"
- "Show me prices for France"  
- "Get generation data for Italy"
- "Renewable forecast for Spain"

**Supported countries:** DE, FR, IT, ES, NL, BE, AT, CH, PL, CZ, DK, SE, NO, FI, GB, IE, PT"""
        
        ask_electricity_agent = simple_electricity_agent
        agent_available = True
        st.warning("⚠️ Using simplified agent (main agent not found)")
        
    except ImportError as e:
        st.error(f"❌ Could not load electricity tools: {e}")
        st.info("Please check your setup and make sure the ENTSOE tools are available.")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Example questions
if len(st.session_state.messages) == 0:
    st.markdown("### 💡 Try asking questions like:")
    st.markdown("""
    - "What's the current electricity load in Germany?"
    - "Compare electricity prices between France and Italy"
    - "Show me renewable energy forecast for Spain"
    - "What are the day-ahead prices for Netherlands?"
    - "Get generation data for Sweden"
    - "Analyze cross-border flows between Germany and France"
    """)

# Accept user input
if prompt := st.chat_input("Ask about European electricity markets..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        if agent_available:
            with st.spinner("Analyzing electricity data..."):
                try:
                    # Get response from electricity agent
                    response = ask_electricity_agent(prompt)
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            error_msg = "Electricity agent is not available. Please check the setup."
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This chat interface connects you with an AI agent specialized in European electricity market analysis.
    
    **Supported Countries:**
    🇩🇪 Germany, 🇫🇷 France, 🇮🇹 Italy, 🇪🇸 Spain, 🇳🇱 Netherlands, 🇧🇪 Belgium, 🇦🇹 Austria, 🇨🇭 Switzerland, 🇵🇱 Poland, 🇨🇿 Czech Republic, 🇩🇰 Denmark, 🇸🇪 Sweden, 🇳🇴 Norway, 🇫🇮 Finland, 🇬🇧 Great Britain, 🇮🇪 Ireland, 🇵🇹 Portugal
    
    **Data Types:**
    - Electricity Load
    - Generation Data  
    - Day-Ahead Prices
    - Renewable Forecasts
    - Cross-Border Flows
    """)
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Data Source:** ENTSOE Transparency Platform")
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>European Electricity Market Analysis Agent | Powered by ENTSOE Data</small>
</div>
""", unsafe_allow_html=True)
