#!/usr/bin/env python3
"""
Functions for OpenAI Function Calling
Collection of utility functions (weather, calculations, etc.)
"""

import os
import logging
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Weather API configuration
WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")
WEATHERSTACK_BASE_URL = "http://api.weatherstack.com/current"

def get_current_weather(location: str) -> Dict[str, Any]:
    """
    Get current weather information for a location
    
    Args:
        location: City or location name
        
    Returns:
        Dictionary with weather information
    """
    logger.info(f"🌤️ Getting weather for: {location}")
    
    if not WEATHERSTACK_API_KEY or WEATHERSTACK_API_KEY == "your_weatherstack_api_key_here":
        return {
            "location": location,
            "error": "Weather API key not configured. Please set WEATHERSTACK_API_KEY in your .env file"
        }
    
    try:
        params = {
            "access_key": WEATHERSTACK_API_KEY,
            "query": location,
            "units": "m"  # Metric units
        }
        
        response = requests.get(WEATHERSTACK_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            return {
                "location": location,
                "error": f"Weather API error: {data['error'].get('info', 'Unknown error')}"
            }
        
        if "current" not in data:
            return {
                "location": location,
                "error": f"No weather data found for {location}"
            }
        
        current = data["current"]
        location_data = data.get("location", {})
        
        return {
            "location": location_data.get("name", location),
            "country": location_data.get("country", "Unknown"),
            "temperature": current.get("temperature"),
            "condition": current.get("weather_descriptions", ["Unknown"])[0],
            "humidity": current.get("humidity"),
            "wind_speed": current.get("wind_speed"),
            "wind_direction": current.get("wind_dir"),
            "feels_like": current.get("feelslike"),
            "observation_time": current.get("observation_time")
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching weather data: {e}")
        return {
            "location": location,
            "error": f"Network error: Unable to fetch weather data"
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching weather data: {e}")
        return {
            "location": location,
            "error": f"Unexpected error: {str(e)}"
        }

def get_weather_forecast(location: str, days: int = 3) -> Dict[str, Any]:
    """
    Get weather forecast for a location
    Note: This is a simplified version - Weatherstack forecast requires paid plan
    
    Args:
        location: City or location name
        days: Number of days for forecast
        
    Returns:
        Dictionary with forecast information
    """
    logger.info(f"🌤️ Getting {days}-day forecast for: {location}")
    
    # For this demo, we'll return current weather with a note about forecast
    current_weather = get_current_weather(location)
    
    if "error" in current_weather:
        return current_weather
    
    return {
        "location": current_weather["location"],
        "country": current_weather["country"],
        "forecast_note": f"Forecast for {days} days requested. Current weather provided (forecast requires paid API plan).",
        "current_weather": {
            "temperature": current_weather["temperature"],
            "condition": current_weather["condition"],
            "humidity": current_weather["humidity"],
            "wind_speed": current_weather["wind_speed"]
        },
        "forecast_days": days
    }