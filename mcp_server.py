#!/usr/bin/env python3
"""MCP server exposing the European Electricity Market Agent.

MCP clients send natural language queries; the strands agent handles
all tool orchestration against the ENTSOE Transparency Platform internally.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from src.agents.electricity_agent import ask_electricity_agent

mcp = FastMCP("electricity-market-agent")


@mcp.tool()
def ask_electricity_agent_tool(query: str) -> str:
    """Ask the European Electricity Market Agent a question.

    The agent has access to real-time ENTSOE data including electricity load,
    generation, day-ahead prices, cross-border flows, and renewable forecasts
    for 17 European countries (DE, FR, IT, ES, NL, BE, AT, CH, PL, CZ, DK,
    SE, NO, FI, GB, IE, PT).

    Args:
        query: Natural language question about European electricity markets.
               Examples:
                 - "What is the current electricity load in Germany?"
                 - "Compare day-ahead prices between France and Italy"
                 - "Show me the renewable forecast for Spain"
                 - "What are the cross-border flows from Germany to France?"
    """
    return ask_electricity_agent(query)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
