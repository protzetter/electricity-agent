# European Electricity Market Analysis - Streamlit App

A web-based interface for analyzing European electricity markets using real-time data from the ENTSOE Transparency Platform.

## Features

- **Interactive Dashboard**: Web-based interface for electricity market analysis
- **Real-time Data**: Live electricity load, generation, and pricing data
- **Multi-Country Support**: 17 European countries supported
- **Visual Analytics**: Interactive charts and graphs using Plotly
- **Multiple Analysis Types**:
  - Electricity Load Analysis
  - Day-Ahead Price Analysis  
  - Generation Data Analysis
  - Generation Forecasts
  - Renewable Energy Forecasts
  - Cross-Border Flow Analysis

## Quick Start

### 1. Install Dependencies

```bash
pip install -r streamlit_requirements.txt
```

### 2. Configure API Token

Make sure your ENTSOE API token is configured in `config/.env`:

```bash
ENTSOE_API_TOKEN=your_entsoe_api_token_here
```

### 3. Run the Application

**Option A: Using the run script**
```bash
python run_streamlit.py
```

**Option B: Direct streamlit command**
```bash
streamlit run streamlit_app.py
```

### 4. Open in Browser

The app will automatically open at: http://localhost:8501

## Usage

1. **Select Country**: Choose from 17 supported European countries
2. **Choose Analysis Type**: Pick the type of electricity market data to analyze
3. **Set Time Range**: Configure the time period for historical data or forecasts
4. **View Results**: Interactive charts and data tables will display the results
5. **Export Data**: Use the expandable "Raw Data" section to view and export data

## Supported Countries

- 🇩🇪 Germany (DE)
- 🇫🇷 France (FR) 
- 🇮🇹 Italy (IT)
- 🇪🇸 Spain (ES)
- 🇳🇱 Netherlands (NL)
- 🇧🇪 Belgium (BE)
- 🇦🇹 Austria (AT)
- 🇨🇭 Switzerland (CH)
- 🇵🇱 Poland (PL)
- 🇨🇿 Czech Republic (CZ)
- 🇩🇰 Denmark (DK)
- 🇸🇪 Sweden (SE)
- 🇳🇴 Norway (NO)
- 🇫🇮 Finland (FI)
- 🇬🇧 Great Britain (GB)
- 🇮🇪 Ireland (IE)
- 🇵🇹 Portugal (PT)

## Analysis Types

### Electricity Load
- Real-time electricity consumption data
- Historical trends and patterns
- Peak and off-peak analysis

### Day-Ahead Prices
- Electricity market prices
- Price volatility analysis
- Market trends

### Generation Data
- Electricity production by source
- Generation mix analysis
- Capacity utilization

### Generation Forecasts
- Day-ahead generation predictions
- Forecast accuracy tracking
- Planning insights

### Renewable Forecasts
- Wind and solar generation forecasts
- Renewable energy integration
- Weather-dependent generation

### Cross-Border Flows
- Electricity trade between countries
- Import/export analysis
- Grid interconnection utilization

## Technical Details

- **Framework**: Streamlit
- **Visualization**: Plotly
- **Data Source**: ENTSOE Transparency Platform
- **Data Processing**: Pandas
- **Real-time Updates**: Configurable refresh intervals

## Troubleshooting

### Common Issues

1. **API Token Error**
   - Ensure your ENTSOE API token is valid and configured in `config/.env`
   - Get a token from: https://transparency.entsoe.eu/

2. **No Data Available**
   - Check if the selected country supports the requested data type
   - Some data may have publication delays (24-48 hours)

3. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r streamlit_requirements.txt`
   - Verify the `src/tools/entsoe_tool.py` file exists and is working

4. **Connection Issues**
   - Check your internet connection
   - ENTSOE API may have temporary outages

### Data Delays

Different countries have different data publication schedules:
- Germany: 48-hour delay for some data types
- Czech Republic: 24-hour delay
- Most others: 36-hour delay

## Development

To extend the application:

1. **Add New Analysis Types**: Modify the `analysis_type` selectbox and add corresponding data fetching logic
2. **Custom Visualizations**: Use Plotly to create additional chart types
3. **Enhanced Filtering**: Add more sophisticated data filtering options
4. **Export Features**: Implement CSV/Excel export functionality

## Dependencies

- `streamlit`: Web application framework
- `pandas`: Data manipulation and analysis
- `plotly`: Interactive visualizations
- `requests`: HTTP requests for API calls
- `python-dotenv`: Environment variable management
- `pytz`: Timezone handling

## License

This application uses the same license as the main electricity agent project.
