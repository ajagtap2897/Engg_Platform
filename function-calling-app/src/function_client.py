#!/usr/bin/env python3
"""
OpenAI Function Calling Client
Implements the exact flow from OpenAI Function Calling documentation
Supports multiple function types (weather, calculations, etc.)
"""

import json
import logging
import os
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

from functions import get_current_weather, get_weather_forecast

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FunctionClient:
    """
    OpenAI Function Calling Client
    Follows the exact pattern from OpenAI documentation
    Supports multiple function types (weather, calculations, utilities, etc.)
    """
    
    def __init__(self):
        """Initialize the function calling client"""
        self.openai_client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Function definitions following OpenAI format
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_weather_forecast",
                    "description": "Get weather forecast for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days for forecast (1-7)",
                                "minimum": 1,
                                "maximum": 7
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        logger.info("🚀 Function Client initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the OpenAI client
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_openai_api_key_here":
                logger.error("❌ OPENAI_API_KEY not configured")
                return False
            
            self.openai_client = OpenAI(api_key=api_key)
            
            # Test connection
            try:
                test_response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                logger.info("✅ OpenAI API connection verified")
                return True
            except Exception as e:
                logger.error(f"❌ OpenAI API test failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    def process_query(self, user_input: str) -> str:
        """
        Process user query using OpenAI Function Calling
        Follows the exact flow from OpenAI documentation
        
        Args:
            user_input: User's query string
            
        Returns:
            Response string
        """
        logger.info(f"🔍 Processing query: {user_input}")
        
        if not self.openai_client:
            return "❌ Weather client not initialized. Please check your OpenAI API key."
        
        try:
            # Step 1: Send the conversation and available functions to the model
            messages = [{"role": "user", "content": user_input}]
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"  # Let the model decide whether to call functions
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Step 2: Check if the model wanted to call a function
            if tool_calls:
                # Step 3: Call the function
                # Note: the JSON response may not always be valid; be sure to handle errors
                available_functions = {
                    "get_current_weather": get_current_weather,
                    "get_weather_forecast": get_weather_forecast,
                }
                
                messages.append(response_message)  # Extend conversation with assistant's reply
                
                # Step 4: Send the info for each function call and function response to the model
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"🔧 Calling function: {function_name} with args: {function_args}")
                    
                    function_response = function_to_call(**function_args)
                    
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        }
                    )
                
                # Get a new response from the model where it can see the function response
                second_response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                
                result = second_response.choices[0].message.content
                logger.info("✅ Function calling completed successfully")
                return result
            
            else:
                # No function call needed
                logger.info("🧠 Direct response (no function call needed)")
                return response_message.content
                
        except Exception as e:
            logger.error(f"❌ Error in function calling: {e}")
            return f"❌ Sorry, I encountered an error: {str(e)}"

# Global client instance
_function_client = None

def get_function_client() -> FunctionClient:
    """
    Get or create the global function client
    
    Returns:
        Function client instance
    """
    global _function_client
    
    if _function_client is None:
        _function_client = FunctionClient()
        _function_client.initialize()
    
    return _function_client