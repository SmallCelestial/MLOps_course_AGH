from fastmcp import FastMCP
import httpx
import os
import asyncio
from dotenv import load_dotenv
from geopy import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

load_dotenv()

mcp = FastMCP("Weather Assistant")
OWM_API_KEY = os.getenv("OWM_API_KEY")
print(f"OWM API key: {OWM_API_KEY}")

geolocator = Nominatim(user_agent="weather_mcp_assistant")

async def get_coords(city: str):
    try:
        location = await asyncio.to_thread(geolocator.geocode, city)

        if location:
            return location.latitude, location.longitude
        else:
            raise ValueError(f"City '{city}' not found")
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        raise ValueError(f"Geocoding service error: {e}")


@mcp.tool(description="Get specific daily weather forecasts for a city. Use this for near-term trip planning for specific dates (up to 16 days into the future). Returns temperature and conditions.")
async def get_daily_forecast(city: str, days: int = 16) -> str:
    days = min(days, 16)

    lat, lon = await get_coords(city)

    async with httpx.AsyncClient() as client:
        url = f"http://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={days}&appid={OWM_API_KEY}&units=metric"

        resp = await client.get(url)
        if resp.status_code != 200:
            print(f"Error fetching forecast: {resp.text}")
            return f"Error fetching forecast: {resp.text}"

        data = resp.json()

        summary = []
        for item in data.get('list', []):
            temp_day = item['temp']['day']
            desc = item['weather'][0]['description']
            summary.append(f"Day {len(summary) + 1}: {desc}, {temp_day}C")

        return "\n".join(summary)


@mcp.tool(description="Get historical monthly weather means/averages (temperature, precipitation, pressure). Use this for general long-term trip planning when the trip is months away and specific daily forecasts are unavailable.")
async def get_monthly_averages(city: str, month: int) -> str:
    lat, lon = await get_coords(city)

    async with httpx.AsyncClient() as client:
        url = f"https://history.openweathermap.org/data/2.5/aggregated/month?month={month}&lat={lat}&lon={lon}&appid={OWM_API_KEY}"

        resp = await client.get(url)
        if resp.status_code != 200:
            return f"Error fetching stats (Note: requires specific API subscription): {resp.text}"

        data = resp.json()
        result = data.get('result', {})

        temp = result.get('temp', {})
        pressure = result.get('pressure', {})

        return (
            f"Monthly Averages for month {month}:\n"
            f"- Temp: Avg {temp.get('mean', 'N/A')}K, (Range: {temp.get('record_min', 'N/A')} - {temp.get('record_max', 'N/A')})\n"
            f"- Pressure: {pressure.get('mean', 'N/A')} hPa\n"
            f"- Precipitation: {result.get('precipitation', {}).get('mean', 'N/A')} mm"
        )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)