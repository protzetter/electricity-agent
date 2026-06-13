#!/usr/bin/env python3
"""
Streamlit Application for European Electricity Market Analysis Agent

A web interface for analyzing European electricity markets using real-time data 
from the ENTSOE Transparency Platform.
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Add the src directory to the path
sys.path.append('src/tools')

try:
    from entsoe_tool import (
        get_electricity_load, 
        get_day_ahead_prices, 
        get_electricity_generation,
        get_generation_forecast_day_ahead,
        get_renewable_forecast,
        get_cross_border_flows,
        get_supported_countries
    )
except ImportError as e:
    st.error(f"Error importing ENTSOE tools: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="European Electricity Market Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("⚡ European Electricity Market Analysis")
st.markdown("""
Analyze European electricity markets using real-time data from the ENTSOE Transparency Platform.
Get insights on electricity load, generation, prices, and renewable forecasts across 17 European countries.
""")

# Sidebar for controls
st.sidebar.header("🔧 Controls")

# Get supported countries
try:
    supported_countries_result = get_supported_countries()
    if 'supported_countries' in supported_countries_result:
        countries = supported_countries_result['supported_countries']
    else:
        countries = ['DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'CH', 'PL', 'CZ', 'DK', 'SE', 'NO', 'FI', 'GB', 'IE', 'PT']
except:
    countries = ['DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'CH', 'PL', 'CZ', 'DK', 'SE', 'NO', 'FI', 'GB', 'IE', 'PT']

# Country selection
country_names = {
    'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'ES': 'Spain',
    'NL': 'Netherlands', 'BE': 'Belgium', 'AT': 'Austria', 'CH': 'Switzerland',
    'PL': 'Poland', 'CZ': 'Czech Republic', 'DK': 'Denmark', 'SE': 'Sweden',
    'NO': 'Norway', 'FI': 'Finland', 'GB': 'Great Britain', 'IE': 'Ireland', 'PT': 'Portugal'
}

selected_country = st.sidebar.selectbox(
    "Select Country",
    options=countries,
    format_func=lambda x: f"{country_names.get(x, x)} ({x})",
    index=0 if 'DE' in countries else 0
)

# Analysis type selection
analysis_type = st.sidebar.selectbox(
    "Analysis Type",
    ["Electricity Load", "Day-Ahead Prices", "Generation Data", "Generation Forecast", "Renewable Forecast", "Cross-Border Flows"]
)

# Time range selection
if analysis_type in ["Electricity Load", "Day-Ahead Prices", "Generation Data"]:
    time_range = st.sidebar.slider("Hours Back", min_value=1, max_value=168, value=24, step=1)
elif analysis_type in ["Generation Forecast", "Renewable Forecast"]:
    time_range = st.sidebar.slider("Days Ahead", min_value=1, max_value=7, value=1, step=1)
else:
    time_range = st.sidebar.slider("Hours Back", min_value=1, max_value=72, value=24, step=1)

# Cross-border flow specific controls
if analysis_type == "Cross-Border Flows":
    st.sidebar.subheader("Cross-Border Flow Settings")
    to_country = st.sidebar.selectbox(
        "To Country",
        options=[c for c in countries if c != selected_country],
        format_func=lambda x: f"{country_names.get(x, x)} ({x})"
    )

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Main content area
def format_data_for_display(data):
    """Format API response data for display"""
    if not data or 'error' in data:
        return None, data.get('error', 'Unknown error')
    
    if 'data_points' in data and data['data_points']:
        df = pd.DataFrame(data['data_points'])
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df, None
    elif 'data' in data and data['data']:
        df = pd.DataFrame(data['data'])
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df, None
    else:
        return None, "No data available"

def create_time_series_chart(df, value_column, title, y_label):
    """Create a time series chart"""
    fig = px.line(
        df, 
        x='timestamp', 
        y=value_column,
        title=title,
        labels={'timestamp': 'Time', value_column: y_label}
    )
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=y_label,
        hovermode='x unified'
    )
    return fig

# Main analysis section
st.header(f"📊 {analysis_type} Analysis for {country_names.get(selected_country, selected_country)}")

# Loading indicator
with st.spinner(f"Loading {analysis_type.lower()} data..."):
    try:
        # Fetch data based on analysis type
        if analysis_type == "Electricity Load":
            data = get_electricity_load(selected_country, hours_back=time_range)
            df, error = format_data_for_display(data)
            
            if df is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Data Points", len(df))
                    if 'value' in df.columns:
                        st.metric("Average Load (MW)", f"{df['value'].mean():.0f}")
                with col2:
                    if 'value' in df.columns:
                        st.metric("Max Load (MW)", f"{df['value'].max():.0f}")
                        st.metric("Min Load (MW)", f"{df['value'].min():.0f}")
                
                # Chart
                if 'value' in df.columns:
                    fig = create_time_series_chart(df, 'value', f"Electricity Load - {country_names.get(selected_country, selected_country)}", "Load (MW)")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 Raw Data"):
                    st.dataframe(df)
            else:
                st.error(f"Error loading data: {error}")

        elif analysis_type == "Day-Ahead Prices":
            data = get_day_ahead_prices(selected_country, days_back=max(1, time_range // 24))
            df, error = format_data_for_display(data)
            
            if df is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Data Points", len(df))
                    if 'price' in df.columns:
                        st.metric("Average Price (EUR/MWh)", f"{df['price'].mean():.2f}")
                with col2:
                    if 'price' in df.columns:
                        st.metric("Max Price (EUR/MWh)", f"{df['price'].max():.2f}")
                        st.metric("Min Price (EUR/MWh)", f"{df['price'].min():.2f}")
                
                # Chart
                if 'price' in df.columns:
                    fig = create_time_series_chart(df, 'price', f"Day-Ahead Prices - {country_names.get(selected_country, selected_country)}", "Price (EUR/MWh)")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 Raw Data"):
                    st.dataframe(df)
            else:
                st.error(f"Error loading data: {error}")

        elif analysis_type == "Generation Data":
            data = get_electricity_generation(selected_country, hours_back=time_range)
            df, error = format_data_for_display(data)
            
            if df is not None:
                st.metric("Total Data Points", len(df))
                
                # If generation data has multiple sources, create a stacked chart
                if 'generation_type' in df.columns and 'value' in df.columns:
                    # Pivot data for stacked chart
                    pivot_df = df.pivot_table(index='timestamp', columns='generation_type', values='value', fill_value=0)
                    
                    fig = go.Figure()
                    for gen_type in pivot_df.columns:
                        fig.add_trace(go.Scatter(
                            x=pivot_df.index,
                            y=pivot_df[gen_type],
                            mode='lines',
                            stackgroup='one',
                            name=gen_type
                        ))
                    
                    fig.update_layout(
                        title=f"Electricity Generation by Type - {country_names.get(selected_country, selected_country)}",
                        xaxis_title="Time",
                        yaxis_title="Generation (MW)",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                elif 'value' in df.columns:
                    fig = create_time_series_chart(df, 'value', f"Total Generation - {country_names.get(selected_country, selected_country)}", "Generation (MW)")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 Raw Data"):
                    st.dataframe(df)
            else:
                st.error(f"Error loading data: {error}")

        elif analysis_type == "Generation Forecast":
            data = get_generation_forecast_day_ahead(selected_country, days_ahead=time_range)
            df, error = format_data_for_display(data)
            
            if df is not None:
                st.metric("Total Forecast Points", len(df))
                
                if 'value' in df.columns:
                    fig = create_time_series_chart(df, 'value', f"Generation Forecast - {country_names.get(selected_country, selected_country)}", "Forecast Generation (MW)")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 Raw Data"):
                    st.dataframe(df)
            else:
                st.error(f"Error loading data: {error}")

        elif analysis_type == "Renewable Forecast":
            data = get_renewable_forecast(selected_country, days_ahead=time_range)
            df, error = format_data_for_display(data)
            
            if df is not None:
                st.metric("Total Forecast Points", len(df))
                
                if 'value' in df.columns:
                    fig = create_time_series_chart(df, 'value', f"Renewable Forecast - {country_names.get(selected_country, selected_country)}", "Renewable Generation (MW)")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 Raw Data"):
                    st.dataframe(df)
            else:
                st.error(f"Error loading data: {error}")

        elif analysis_type == "Cross-Border Flows":
            data = get_cross_border_flows(selected_country, to_country, hours_back=time_range)
            df, error = format_data_for_display(data)
            
            if df is not None:
                st.metric("Total Flow Data Points", len(df))
                
                if 'value' in df.columns:
                    avg_flow = df['value'].mean()
                    st.metric(f"Average Flow {selected_country}→{to_country} (MW)", f"{avg_flow:.0f}")
                    
                    fig = create_time_series_chart(
                        df, 'value', 
                        f"Cross-Border Flow: {country_names.get(selected_country, selected_country)} → {country_names.get(to_country, to_country)}", 
                        "Flow (MW)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 Raw Data"):
                    st.dataframe(df)
            else:
                st.error(f"Error loading data: {error}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check your ENTSOE API token configuration and try again.")

# Footer
st.markdown("---")
st.markdown("""
**Data Source:** ENTSOE Transparency Platform  
**Note:** Data may have delays based on country-specific publication schedules.  
For more information, visit the [ENTSOE Documentation](https://documenter.getpostman.com/view/7009892/2s93JtP3F6)
""")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ About")
st.sidebar.markdown("""
This application provides real-time analysis of European electricity markets using data from the ENTSOE Transparency Platform.

**Supported Countries:**
- 🇩🇪 Germany, 🇫🇷 France, 🇮🇹 Italy, 🇪🇸 Spain
- 🇳🇱 Netherlands, 🇧🇪 Belgium, 🇦🇹 Austria, 🇨🇭 Switzerland  
- 🇵🇱 Poland, 🇨🇿 Czech Republic, 🇩🇰 Denmark, 🇸🇪 Sweden
- 🇳🇴 Norway, 🇫🇮 Finland, 🇬🇧 Great Britain, 🇮🇪 Ireland, 🇵🇹 Portugal
""")
