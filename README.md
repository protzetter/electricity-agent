# European Electricity Market Analysis Agent

A specialized AI agent for analyzing European electricity markets using real-time data from the ENTSOE Transparency Platform.

## Features

- **Real-time Electricity Data**: Access to live electricity load, generation, and pricing data
- **Multi-Country Analysis**: Support for 17 European countries
- **Market Insights**: Comprehensive analysis of electricity markets and trends
- **Cross-Border Flows**: Analysis of electricity flows between countries
- **Renewable Forecasts**: Wind and solar generation forecasting
- **Data Visualization**: Generate Python code for creating electricity market charts
- **Price Analysis**: Day-ahead electricity price analysis and trends

## Supported Countries

- Germany (DE), France (FR), Italy (IT), Spain (ES)
- Netherlands (NL), Belgium (BE), Austria (AT), Switzerland (CH)
- Poland (PL), Czech Republic (CZ), Denmark (DK), Sweden (SE)
- Norway (NO), Finland (FI), Great Britain (GB), Ireland (IE), Portugal (PT)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables in `config/.env`:
   ```
   ENTSOE_API_TOKEN=your_entsoe_api_token_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   AWS_REGION=us-east-1
   ```

## Getting ENTSOE API Token

1. Register at [ENTSOE Transparency Platform](https://transparency.entsoe.eu/)
2. Go to Account Settings → Web API Security Token
3. Generate a new token and add it to your `.env` file

## Usage

### Basic Usage

```python
from src.agents.electricity_agent import ask_electricity_agent

# Get electricity overview for Germany
response = ask_electricity_agent("What's the current electricity situation in Germany?")
print(response)

# Compare multiple countries
response = ask_electricity_agent("Compare electricity prices between Germany, France, and Italy")
print(response)

# Analyze renewable energy
response = ask_electricity_agent("What's the renewable energy forecast for Spain?")
print(response)
```

### Interactive Mode

```bash
python src/agents/electricity_agent.py
```

### Direct Tool Usage

```python
from src.tools.entsoe_tool import get_electricity_load, get_day_ahead_prices, get_generation_forecast_day_ahead

# Get load data for Germany (last 24 hours)
load_data = get_electricity_load('DE', hours_back=24)

# Get day-ahead prices for France
price_data = get_day_ahead_prices('FR', days_back=1)

# Get generation forecast for Germany (today's forecast)
forecast_data = get_generation_forecast_day_ahead('DE', days_ahead=1)
```

## Available Tools

### High-Level Analysis Tools
- `get_country_electricity_overview()` - Comprehensive country analysis
- `compare_country_electricity()` - Multi-country comparison
- `analyze_cross_border_electricity_flows()` - Cross-border flow analysis
- `get_renewable_energy_forecast()` - Renewable energy forecasting
- `get_electricity_market_insights()` - Market insights and trends
- `generate_electricity_chart_code()` - Visualization code generation

### ENTSOE Data Tools
- `get_electricity_load()` - Electricity consumption data
- `get_electricity_generation()` - Generation data by type
- `get_generation_forecast_day_ahead()` - Day-ahead generation forecasts
- `get_day_ahead_prices()` - Day-ahead market prices
- `get_cross_border_flows()` - Physical flows between countries
- `get_renewable_forecast()` - Wind and solar forecasts
- `get_supported_countries()` - List of supported countries
- `debug_entsoe_request()` - Debug API requests

## Example Queries

- "What's the current electricity load in Germany?"
- "Compare electricity prices between Nordic countries"
- "Show me the renewable energy forecast for Spain"
- "Get the generation forecast day ahead for Germany"
- "What's the day-ahead generation forecast for Italy?"
- "Analyze cross-border flows between Germany and France"
- "Generate a chart showing Italian electricity prices"
- "What are the key insights for European electricity markets today?"

## Data Types

- **Load Data**: Electricity consumption in MW
- **Generation Data**: Electricity production by source type in MW
- **Price Data**: Day-ahead market prices in EUR/MWh
- **Flow Data**: Cross-border electricity flows in MW
- **Forecast Data**: Renewable energy forecasts in MW

## Technical Details

- **API**: ENTSOE Transparency Platform REST API
- **Data Format**: XML responses parsed to structured JSON
- **Time Zones**: CET/CEST with automatic handling
- **Resolution**: 15-minute intervals for most data types
- **Historical Data**: Available with 2+ hour delay for real-time data

## Error Handling

The system includes comprehensive error handling for:
- API authentication issues
- Data availability problems
- Invalid country codes
- Network connectivity issues
- XML parsing errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues related to:
- **ENTSOE API**: Check [ENTSOE Documentation](https://documenter.getpostman.com/view/7009892/2s93JtP3F6)
- **This Tool**: Open an issue in this repository

## Changelog

### v1.0.0
- Initial release with full ENTSOE integration
- Support for 17 European countries
- Comprehensive electricity market analysis
- Real-time data access and forecasting
