#!/usr/bin/env python3
"""MCP server exposing European electricity market tools via the ENTSOE Transparency Platform."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from src.tools.entsoe_tool import (
    get_electricity_load as _get_electricity_load,
    get_electricity_generation as _get_electricity_generation,
    get_generation_forecast_day_ahead as _get_generation_forecast_day_ahead,
    get_day_ahead_prices as _get_day_ahead_prices,
    get_cross_border_flows as _get_cross_border_flows,
    get_renewable_forecast as _get_renewable_forecast,
    get_supported_countries as _get_supported_countries,
    get_entsoe_api_info as _get_entsoe_api_info,
)

mcp = FastMCP("electricity-market")


@mcp.tool()
def get_electricity_load(country_code: str, hours_back: int = 6) -> dict:
    """Get electricity load (consumption) data for a European country.

    Args:
        country_code: Two-letter country code (e.g. 'DE', 'FR', 'IT')
        hours_back: Number of hours of historical data to fetch (default: 6)
    """
    return _get_electricity_load(country_code, hours_back)


@mcp.tool()
def get_electricity_generation(country_code: str, hours_back: int = 6) -> dict:
    """Get electricity generation data by production type for a European country.

    Args:
        country_code: Two-letter country code (e.g. 'DE', 'FR', 'IT')
        hours_back: Number of hours of historical data to fetch (default: 6)
    """
    return _get_electricity_generation(country_code, hours_back)


@mcp.tool()
def get_day_ahead_prices(country_code: str, days_back: int = 1) -> dict:
    """Get day-ahead electricity prices (EUR/MWh) for a European country.

    Args:
        country_code: Two-letter country code (e.g. 'DE', 'FR', 'IT')
        days_back: Number of days back to fetch prices (default: 1)
    """
    return _get_day_ahead_prices(country_code, days_back)


@mcp.tool()
def get_generation_forecast_day_ahead(country_code: str, days_ahead: int = 1) -> dict:
    """Get the day-ahead generation forecast for a European country.

    Args:
        country_code: Two-letter country code (e.g. 'DE', 'FR', 'IT')
        days_ahead: Number of days to fetch forecast data (1-7, default: 1)
    """
    return _get_generation_forecast_day_ahead(country_code, days_ahead)


@mcp.tool()
def get_renewable_forecast(country_code: str, hours_ahead: int = 48) -> dict:
    """Get wind and solar generation forecast for a European country.

    Args:
        country_code: Two-letter country code (e.g. 'DE', 'FR', 'IT')
        hours_ahead: Number of hours ahead to forecast (default: 48, max: 72)
    """
    return _get_renewable_forecast(country_code, hours_ahead)


@mcp.tool()
def get_cross_border_flows(from_country: str, to_country: str, hours_back: int = 24) -> dict:
    """Get physical electricity flows between two European countries.

    Positive values = flow from source to destination.
    Negative values = flow from destination to source.

    Args:
        from_country: Source country code (e.g. 'DE')
        to_country: Destination country code (e.g. 'FR')
        hours_back: Number of hours of historical data to fetch (default: 24)
    """
    return _get_cross_border_flows(from_country, to_country, hours_back)


@mcp.tool()
def get_supported_countries() -> dict:
    """Get the list of supported European countries and their codes."""
    return _get_supported_countries()


@mcp.tool()
def get_entsoe_api_info() -> dict:
    """Get information about the ENTSOE API, available data types, and requirements."""
    return _get_entsoe_api_info()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
