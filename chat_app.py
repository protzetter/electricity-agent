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
    st.error("❌ Could not load Electricity Agent. Please check the setup.")
    st.markdown("**Error:** Make sure the electricity_agent module is available in the src/agents directory.")
    
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
