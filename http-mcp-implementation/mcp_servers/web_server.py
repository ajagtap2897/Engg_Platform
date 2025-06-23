#!/usr/bin/env python3
"""
HTTP MCP Web Server
A simplified MCP server that works with the web_adapter client
"""

import asyncio
import json
import logging
import os
import requests
from typing import Any, Dict, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Weatherstack API configuration
WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")
WEATHERSTACK_BASE_URL = "http://api.weatherstack.com/current"

# Debug: Log API key status
if WEATHERSTACK_API_KEY:
    logger.info(f"✅ Weatherstack API key loaded: {WEATHERSTACK_API_KEY[:8]}...")
else:
    logger.warning("⚠️ Weatherstack API key not found in environment variables")

# FastAPI app
app = FastAPI(title="HTTP MCP Web Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Server info
server_info = {
    "name": "web-server",
    "version": "1.0.0",
    "description": "HTTP MCP Web Server with simplified tools and weather capabilities"
}

# Pydantic models for MCP protocol
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str
    params: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

# Available tools
TOOLS = [
    {
        "name": "get_greeting",
        "description": "Get a greeting message",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name to greet"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_time",
        "description": "Get the current server time",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_weather",
        "description": "Get current weather information for a specified city or location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city, state, or location to get weather for"
                }
            },
            "required": ["location"]
        }
    }
]

# Tool implementations
def get_greeting(name: str) -> str:
    """Get a greeting message"""
    return f"Hello, {name}! Welcome to the HTTP MCP Web Server."

def get_time() -> str:
    """Get the current server time"""
    import datetime
    now = datetime.datetime.now()
    return f"The current server time is: {now.strftime('%Y-%m-%d %H:%M:%S')}"

def get_weather_data(city: str) -> Dict[str, Any]:
    """Fetch weather data from Weatherstack API"""
    try:
        if not WEATHERSTACK_API_KEY or WEATHERSTACK_API_KEY == "your_weatherstack_api_key_here":
            return {
                "error": "Weatherstack API key not configured. Please set WEATHERSTACK_API_KEY in .env file."
            }
        
        params = {
            "access_key": WEATHERSTACK_API_KEY,
            "query": city,
            "units": "m"
        }
        
        response = requests.get(WEATHERSTACK_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            return {
                "error": f"Weather API error: {data['error'].get('info', 'Unknown error')}"
            }
        
        if "current" not in data:
            return {
                "error": f"No weather data found for {city}"
            }
        
        current = data["current"]
        location = data.get("location", {})
        
        return {
            "city": location.get("name", city),
            "country": location.get("country", "Unknown"),
            "temperature": current.get("temperature", "N/A"),
            "condition": current.get("weather_descriptions", ["Unknown"])[0],
            "humidity": current.get("humidity", "N/A"),
            "wind_speed": current.get("wind_speed", "N/A"),
            "wind_direction": current.get("wind_dir", "N/A"),
            "feels_like": current.get("feelslike", "N/A"),
            "uv_index": current.get("uv_index", "N/A"),
            "visibility": current.get("visibility", "N/A")
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching weather data: {e}")
        return {
            "error": f"Network error: Unable to fetch weather data for {city}"
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching weather data: {e}")
        return {
            "error": f"Unexpected error: {str(e)}"
        }

def format_weather_response(weather_data: Dict[str, Any]) -> str:
    """Format weather data into a user-friendly string"""
    if "error" in weather_data:
        return f"❌ {weather_data['error']}"
    
    city = weather_data.get("city", "Unknown")
    country = weather_data.get("country", "")
    location_str = f"{city}, {country}" if country else city
    
    temp = weather_data.get("temperature", "N/A")
    condition = weather_data.get("condition", "Unknown")
    humidity = weather_data.get("humidity", "N/A")
    wind_speed = weather_data.get("wind_speed", "N/A")
    wind_dir = weather_data.get("wind_direction", "N/A")
    feels_like = weather_data.get("feels_like", "N/A")
    
    response = f"🌤️ **Weather in {location_str}:**\n"
    response += f"🌡️ **Temperature:** {temp}°C (feels like {feels_like}°C)\n"
    response += f"☁️ **Condition:** {condition}\n"
    response += f"💨 **Wind:** {wind_speed} km/h {wind_dir}\n"
    response += f"💧 **Humidity:** {humidity}%\n"
    
    uv_index = weather_data.get("uv_index")
    if uv_index != "N/A":
        response += f"☀️ **UV Index:** {uv_index}\n"
    
    visibility = weather_data.get("visibility")
    if visibility != "N/A":
        response += f"👁️ **Visibility:** {visibility} km\n"
    
    return response.strip()

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP protocol endpoint"""
    try:
        # Parse request
        body = await request.json()
        
        # Check if this is a notification (no id required)
        is_notification = "id" not in body
        
        # Parse the request
        mcp_request = MCPRequest(**body)
        
        # Log based on whether it's a notification or regular request
        if is_notification:
            logger.info(f"Received MCP notification: {mcp_request.method}")
            # For notifications, we don't need to return anything
            if mcp_request.method == "notifications/initialized":
                # Handle the initialized notification
                return {}
        else:
            logger.info(f"Received MCP request: {mcp_request.method}")
        
        # Handle different methods
        if mcp_request.method == "initialize":
            # Initialize the server
            return MCPResponse(
                id=mcp_request.id,
                result={
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": server_info["name"],
                        "version": server_info["version"],
                        "vendor": "Custom"
                    },
                    "capabilities": {
                        "tools": {
                            "supports_streaming": False
                        }
                    }
                }
            )
        
        elif mcp_request.method == "tools/list":
            # List available tools
            return MCPResponse(
                id=mcp_request.id,
                result={
                    "tools": TOOLS,
                    "cursor": None  # No pagination, all tools returned at once
                }
            )
        
        elif mcp_request.method == "tools/call":
            # Call a specific tool
            tool_name = mcp_request.params.get("name")
            arguments = mcp_request.params.get("arguments", {})
            
            if tool_name == "get_greeting":
                name = arguments.get("name", "User")
                result = get_greeting(name)
                
                return MCPResponse(
                    id=mcp_request.id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                )
            
            elif tool_name == "get_time":
                result = get_time()
                
                return MCPResponse(
                    id=mcp_request.id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                )
            
            elif tool_name == "get_weather":
                location = arguments.get("location")
                if not location:
                    return MCPResponse(
                        id=mcp_request.id,
                        error={
                            "code": -32602,
                            "message": "Invalid params: location is required"
                        }
                    )
                
                logger.info(f"🌤️ Getting weather for: {location}")
                
                # Get weather data
                weather_data = get_weather_data(location)
                
                # Format response
                formatted_response = format_weather_response(weather_data)
                
                return MCPResponse(
                    id=mcp_request.id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": formatted_response
                            }
                        ]
                    }
                )
            
            else:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                )
        
        else:
            return MCPResponse(
                id=mcp_request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {mcp_request.method}"
                }
            )
    
    except Exception as e:
        logger.error(f"❌ Error handling MCP request: {e}")
        # Use a default ID if mcp_request is not defined
        request_id = 0
        try:
            if 'mcp_request' in locals() and hasattr(mcp_request, 'id'):
                request_id = mcp_request.id
            elif 'body' in locals() and 'id' in body:
                request_id = body['id']
        except:
            pass
            
        return MCPResponse(
            id=request_id,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": server_info["name"]}

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "message": "HTTP MCP Web Server",
        "server_info": server_info,
        "capabilities": {
            "weather": "Get weather information for any location",
            "greeting": "Get personalized greeting messages",
            "time": "Get current server time"
        },
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health"
        }
    }

def main():
    """Run the HTTP MCP server"""
    logger.info("🚀 Starting HTTP MCP Web Server...")
    logger.info("🌐 Server will be available at http://localhost:8080")
    logger.info("📡 MCP endpoint: http://localhost:8080/mcp")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

if __name__ == "__main__":
    main()