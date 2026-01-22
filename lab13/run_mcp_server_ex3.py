from datetime import datetime

from fastmcp import FastMCP

mcp = FastMCP("Time Server")

@mcp.tool(description="Get the current date in 'Year-Month-Day' (YYYY-MM-DD) format")
def get_current_date() -> str:
    now = datetime.now()
    return now.strftime("%Y-%m-%d")

@mcp.tool(description="Get the current date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")
def get_current_datetime() -> str:
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%S")

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8002, host="0.0.0.0")
