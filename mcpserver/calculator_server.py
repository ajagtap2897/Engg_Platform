#!/usr/bin/env python3
"""
Calculator MCP Server

This server provides basic mathematical operations.
It demonstrates how to create a simple MCP server with multiple tools.
"""

import asyncio
import json
import logging
import math
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("calculator-server")

# Create server instance
server = Server("calculator-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="add",
            description="Add two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number", 
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="subtract",
            description="Subtract second number from first number",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number (minuend)"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number (subtrahend)"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="multiply",
            description="Multiply two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="divide",
            description="Divide first number by second number",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "Dividend"
                    },
                    "b": {
                        "type": "number",
                        "description": "Divisor"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="power",
            description="Raise first number to the power of second number",
            inputSchema={
                "type": "object",
                "properties": {
                    "base": {
                        "type": "number",
                        "description": "Base number"
                    },
                    "exponent": {
                        "type": "number",
                        "description": "Exponent"
                    }
                },
                "required": ["base", "exponent"]
            }
        ),
        types.Tool(
            name="sqrt",
            description="Calculate square root of a number",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {
                        "type": "number",
                        "description": "Number to calculate square root of",
                        "minimum": 0
                    }
                },
                "required": ["number"]
            }
        ),
        types.Tool(
            name="factorial",
            description="Calculate factorial of a non-negative integer",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Non-negative integer",
                        "minimum": 0
                    }
                },
                "required": ["n"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    """
    if not arguments:
        raise ValueError("Missing arguments")
    
    try:
        if name == "add":
            a = arguments["a"]
            b = arguments["b"]
            result = a + b
            return [
                types.TextContent(
                    type="text",
                    text=f"{a} + {b} = {result}"
                )
            ]
        
        elif name == "subtract":
            a = arguments["a"]
            b = arguments["b"]
            result = a - b
            return [
                types.TextContent(
                    type="text",
                    text=f"{a} - {b} = {result}"
                )
            ]
        
        elif name == "multiply":
            a = arguments["a"]
            b = arguments["b"]
            result = a * b
            return [
                types.TextContent(
                    type="text",
                    text=f"{a} × {b} = {result}"
                )
            ]
        
        elif name == "divide":
            a = arguments["a"]
            b = arguments["b"]
            if b == 0:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Division by zero is not allowed"
                    )
                ]
            result = a / b
            return [
                types.TextContent(
                    type="text",
                    text=f"{a} ÷ {b} = {result}"
                )
            ]
        
        elif name == "power":
            base = arguments["base"]
            exponent = arguments["exponent"]
            result = base ** exponent
            return [
                types.TextContent(
                    type="text",
                    text=f"{base}^{exponent} = {result}"
                )
            ]
        
        elif name == "sqrt":
            number = arguments["number"]
            if number < 0:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Cannot calculate square root of negative number"
                    )
                ]
            result = math.sqrt(number)
            return [
                types.TextContent(
                    type="text",
                    text=f"√{number} = {result}"
                )
            ]
        
        elif name == "factorial":
            n = arguments["n"]
            if n < 0:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Factorial is not defined for negative numbers"
                    )
                ]
            result = math.factorial(n)
            return [
                types.TextContent(
                    type="text",
                    text=f"{n}! = {result}"
                )
            ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except KeyError as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error: Missing required argument {e}"
            )
        ]
    except Exception as e:
        logger.error(f"Calculation error: {e}")
        return [
            types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )
        ]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="calculator-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())