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
2. Install dependencies with [uv](https://docs.astral.sh/uv/):
   ```bash
   uv sync
   ```
3. Set up your environment variables in `config/.env`:
   ```
   ENTSOE_API_TOKEN=your_entsoe_api_token_here
   AWS_REGION=eu-west-1
   BEDROCK_MODEL=qwen.qwen3-32b-v1:0
   ```

## Getting ENTSOE API Token

1. Register at [ENTSOE Transparency Platform](https://transparency.entsoe.eu/)
2. Go to Account Settings → Web API Security Token
3. Generate a new token and add it to your `.env` file

## Usage

### Python API

```python
from src.agents.electricity_agent import ask_electricity_agent

response = ask_electricity_agent("What's the current electricity situation in Germany?")
print(response)
```

### Interactive CLI

```bash
uv run python src/agents/electricity_agent.py
```

### MCP Server

The electricity tools are exposed as an [MCP](https://modelcontextprotocol.io) server, letting any MCP-compatible client (Claude Desktop, other agents) call them directly.

**Run the server:**
```bash
uv run python mcp_server.py
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "electricity-market": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "cwd": "/path/to/electricity-agent"
    }
  }
}
```

**Use from a strands agent:**
```python
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp.client.stdio import stdio_client, StdioServerParameters

params = StdioServerParameters(command="uv", args=["run", "python", "mcp_server.py"])
with MCPClient(lambda: stdio_client(params)) as client:
    agent = Agent(tools=client.list_tools_sync().items)
    print(agent("What are the day-ahead prices for Germany?"))
```

**Available MCP tools:**
- `get_electricity_load` — consumption data in MW
- `get_electricity_generation` — generation by production type
- `get_day_ahead_prices` — prices in EUR/MWh
- `get_generation_forecast_day_ahead` — day-ahead generation forecast
- `get_renewable_forecast` — wind and solar forecast
- `get_cross_border_flows` — physical flows between two countries
- `get_supported_countries` — list of supported country codes
- `get_entsoe_api_info` — API capabilities and requirements

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
- `get_cross_border_flows()` - Physical flows between countries ✅ **Fixed & Working**
- `get_renewable_forecast()` - Wind and solar forecasts
- `get_unavailability_production_units()` - Power plant outages ⚠️ **Limited Data Availability**
- `get_supported_countries()` - List of supported countries
- `get_entsoe_api_info()` - API information and status

## Example Queries

### Basic Market Data
- "What's the current electricity load in Germany?"
- "Compare electricity prices between Nordic countries"
- "Show me the renewable energy forecast for Spain"
- "Get the generation forecast day ahead for Germany"
- "What's the day-ahead generation forecast for Italy?"

### Cross-Border Analysis (Now Working!)
- "Analyze cross-border flows between Germany and France"
- "Show me electricity flows from Spain to France"
- "What are the cross-border flows between Netherlands and Belgium?"
- "Compare import/export patterns between Germany and its neighbors"

### Advanced Analysis
- "Generate a chart showing Italian electricity prices"
- "What are the key insights for European electricity markets today?"
- "Compare renewable generation forecasts across Nordic countries"
- "Analyze electricity market trends for the past week"

## Data Types & Availability

### Reliable Data Sources ✅
- **Load Data**: Electricity consumption in MW - **Excellent availability**
- **Generation Data**: Electricity production by source type in MW - **Good availability**
- **Price Data**: Day-ahead market prices in EUR/MWh - **Excellent availability**
- **Cross-Border Flows**: Physical electricity flows in MW - **Good availability** (Recently Fixed)
- **Renewable Forecasts**: Wind and solar forecasts in MW - **Good availability**

### Limited Data Sources ⚠️
- **Unavailability Data**: Power plant outages and maintenance - **Very limited availability**
  - Most TSOs do not provide this data publicly
  - Often restricted to registered market participants
  - Consider using generation data as an alternative

### Data Characteristics
- **Time Resolution**: 15-minute intervals for most data types
- **Geographic Coverage**: 17 European countries
- **Historical Access**: 2+ hour delay for real-time data
- **Timezone**: CET/CEST with automatic conversion

## Technical Details

- **API**: ENTSOE Transparency Platform REST API
- **Data Format**: XML responses parsed to structured JSON
- **Time Zones**: CET/CEST with automatic handling
- **Resolution**: 15-minute intervals for most data types
- **Historical Data**: Available with 2+ hour delay for real-time data

## Error Handling & Troubleshooting

The system includes comprehensive error handling for:
- API authentication issues
- Data availability problems
- Invalid country codes
- Network connectivity issues
- XML parsing errors

### Common Issues & Solutions

#### "No matching data found" Error
- **Cause**: Data not available for the requested time period or country
- **Solution**: Try a different time period or country, or use alternative data types

#### Cross-Border Flows Not Working
- **Status**: ✅ **FIXED** - Should work reliably now
- **If still having issues**: Check that both countries are supported and have interconnections

#### Unavailability Data Always Fails
- **Expected Behavior**: This data type has very limited availability
- **Solution**: Use `get_electricity_generation()` or `get_generation_forecast_day_ahead()` instead

#### API Token Issues
- **Check**: Ensure your ENTSOE_API_TOKEN is set correctly in `config/.env`
- **Verify**: Test your token at the [ENTSOE Transparency Platform](https://transparency.entsoe.eu/)

#### Installation Problems
- **Recommended**: Use uv: `uv sync`
- **Fallback**: `pip install -r requirements.txt`

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

## Recent Updates & Fixes

### Germany Area Code - FIXED ✅
The Germany area code has been corrected in the ENTSOE tool:
- **Fixed Area Code**: Updated from `'10Y1001A1001A82H'` to `'10Y1001A1001A83F'`
- **Critical Fix**: This was preventing all German electricity market data retrieval
- **Improved Data Retrieval**: This fix ensures proper data retrieval for all German electricity market functions
- **All Functions Affected**: Load, generation, prices, forecasts, and cross-border flows for Germany now work correctly
- **Impact**: Germany is the largest electricity market in Europe, making this fix essential for comprehensive European market analysis

### Cross-Border Flows - FIXED ✅
The `get_cross_border_flows()` function has been completely fixed and now works reliably:
- **Multiple Parameter Strategies**: Tries 4 different parameter combinations for better compatibility
- **Proper Timezone Handling**: Uses CET timezone with appropriate data delays
- **Enhanced Error Handling**: Better validation and clear error messages
- **Reverse Direction Support**: Handles interconnections that only report in one direction
- **100% Success Rate**: Successfully tested with major European interconnections (DE-FR, ES-FR, DE-NL, etc.)

### Unavailability Data - Status Update ⚠️
The `get_unavailability_production_units()` function has been improved but has inherent limitations:
- **Function Works Correctly**: Proper API calls and error handling
- **Data Availability Issue**: ENTSOE document type A77 has extremely limited availability
- **TSO Restrictions**: Most European TSOs do not provide this data publicly
- **Alternative Recommendations**: Use `get_electricity_generation()`, `get_generation_forecast_day_ahead()`, or `get_renewable_forecast()` instead

### Installation Improvements
- **uv**: Project now managed with `uv sync` via `pyproject.toml`
- **Better Error Messages**: More informative error handling throughout
- **Enhanced Documentation**: Clear warnings about data availability limitations

## Changelog

### v2.0.0 (Latest)
- ✅ **Added**: MCP server exposing all ENTSOE tools (`mcp_server.py`)
- ✅ **Updated**: strands-agents to 1.x (`BedrockModel` API, simplified response handling)
- ✅ **Switched**: Default model to `qwen.qwen3-32b-v1:0` on `eu-west-1`
- ✅ **Added**: `pyproject.toml` for uv-based dependency management

### v1.2.1
- ✅ **Fixed**: Germany area code corrected from `'10Y1001A1001A82H'` to `'10Y1001A1001A83F'`

### v1.2.0
- ✅ **Fixed**: Cross-border flows function now works reliably with all major European interconnections
- ⚠️ **Updated**: Unavailability function with clear data availability warnings

### v1.0.0
- Initial release with full ENTSOE integration
- Support for 17 European countries
- Comprehensive electricity market analysis
