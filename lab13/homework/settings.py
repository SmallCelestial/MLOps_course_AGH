import os
from dotenv import load_dotenv

load_dotenv()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
WEATHER_MCP_URL = os.getenv("WEATHER_MCP_URL", "http://localhost:8001/mcp")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_MCP_URL = os.getenv("TAVILY_MCP_URL", f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}")
