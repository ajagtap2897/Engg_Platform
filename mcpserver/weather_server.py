#!/usr/bin/env python3
"""
Weather MCP Server

This server provides weather information using a free weather API.
It demonstrates how to create an MCP server with API integration and data processing.
"""

import asyncio
import json
import logging
from typing import Any, Sequence
import requests
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-server")

# Create server instance
server = Server("weather-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather information for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city to get weather for"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial", "kelvin"],
                        "description": "Temperature units (metric=Celsius, imperial=Fahrenheit, kelvin=Kelvin)",
                        "default": "metric"
                    }
                },
                "required": ["city"]
            }
        ),
        types.Tool(
            name="get_forecast",
            description="Get 5-day weather forecast for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city to get forecast for"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial", "kelvin"],
                        "description": "Temperature units (metric=Celsius, imperial=Fahrenheit, kelvin=Kelvin)",
                        "default": "metric"
                    }
                },
                "required": ["city"]
            }
        )
    ]

def get_unit_symbol(units: str) -> str:
    """Get temperature unit symbol"""
    if units == "metric":
        return "°C"
    elif units == "imperial":
        return "°F"
    else:
        return "K"

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    """
    if not arguments:
        raise ValueError("Missing arguments")
    
    city = arguments.get("city")
    units = arguments.get("units", "metric")
    
    if not city:
        raise ValueError("City name is required")
    
    # Using WeatherStack API
    base_url = "http://api.weatherstack.com/current"
    api_key = "270afb874ba808f9799cbd2e7e876502"
    
    if name == "get_weather":
        try:
            # WeatherStack API call
            params = {
                'access_key': api_key,
                'query': city,
                'units': 'm' if units == 'metric' else ('f' if units == 'imperial' else 'k')
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Weather API Error: {data['error']['info']}"
                    )
                ]
            
            current = data['current']
            location = data['location']
            
            unit_symbol = get_unit_symbol(units)
            
            weather_report = f"""
🌤️ Current Weather for {location['name']}, {location['country']}

🌡️ Temperature: {current['temperature']}{unit_symbol}
🤔 Feels like: {current['feelslike']}{unit_symbol}
☁️ Condition: {current['weather_descriptions'][0]}
💧 Humidity: {current['humidity']}%
🌬️ Wind: {current['wind_speed']} km/h {current['wind_dir']}
📊 Pressure: {current['pressure']} mb
👁️ Visibility: {current['visibility']} km
☀️ UV Index: {current['uv_index']}
"""
            
            return [
                types.TextContent(
                    type="text",
                    text=weather_report.strip()
                )
            ]
            
        except Exception as e:
            logger.error(f"Weather API request failed: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to get weather data for {city}: {str(e)}"
                )
            ]
    
    elif name == "get_forecast":
        try:
            # Note: WeatherStack free plan doesn't include forecast
            # For forecast, you'd need a paid plan or use a different API
            # This provides a simulated forecast as an example
            
            # Get current weather first to base forecast on
            params = {
                'access_key': api_key,
                'query': city,
                'units': 'm' if units == 'metric' else ('f' if units == 'imperial' else 'k')
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Weather API Error: {data['error']['info']}"
                    )
                ]
            
            current_temp = data['current']['temperature']
            location = data['location']
            
            # Simulate 5-day forecast based on current temperature
            forecast_data = []
            import random
            
            for i in range(5):
                # Vary temperature by ±5 degrees from current
                day_temp = current_temp + random.randint(-5, 5)
                conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear"]
                
                forecast_data.append({
                    "day": f"Day {i+1}",
                    "temp_max": day_temp + 3,
                    "temp_min": day_temp - 3,
                    "description": random.choice(conditions)
                })
            
            unit_symbol = get_unit_symbol(units)
            
            forecast_report = f"📅 5-Day Weather Forecast for {location['name']}, {location['country']}\n"
            forecast_report += "⚠️ Note: This is a simulated forecast. WeatherStack free plan doesn't include forecasts.\n\n"
            
            for day_data in forecast_data:
                forecast_report += f"🗓️ {day_data['day']}: {day_data['temp_min']}{unit_symbol} - {day_data['temp_max']}{unit_symbol}, {day_data['description']}\n"
            
            return [
                types.TextContent(
                    type="text",
                    text=forecast_report.strip()
                )
            ]
            
        except Exception as e:
            logger.error(f"Forecast API request failed: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to get forecast data for {city}: {str(e)}"
                )
            ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="weather-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())