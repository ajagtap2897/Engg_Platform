#!/usr/bin/env python3
"""
Meme Generator MCP Server

This server provides tools for generating memes using the imgflip API.
It demonstrates how to create an MCP server with external API integration.
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
logger = logging.getLogger("meme-server")

# Create server instance
server = Server("meme-server")

# Popular meme templates with their IDs from imgflip
MEME_TEMPLATES = {
    "drake": "181913649",
    "distracted_boyfriend": "112126428", 
    "woman_yelling_at_cat": "188390779",
    "two_buttons": "87743020",
    "change_my_mind": "129242436",
    "expanding_brain": "93895088",
    "surprised_pikachu": "155067746",
    "this_is_fine": "55311130",
    "success_kid": "61544",
    "bad_luck_brian": "61585"
}

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="generate_meme",
            description="Generate a meme using popular templates",
            inputSchema={
                "type": "object",
                "properties": {
                    "template": {
                        "type": "string",
                        "enum": list(MEME_TEMPLATES.keys()),
                        "description": f"Meme template to use. Available: {', '.join(MEME_TEMPLATES.keys())}"
                    },
                    "top_text": {
                        "type": "string",
                        "description": "Text for the top of the meme"
                    },
                    "bottom_text": {
                        "type": "string", 
                        "description": "Text for the bottom of the meme"
                    }
                },
                "required": ["template", "top_text", "bottom_text"]
            }
        ),
        types.Tool(
            name="list_meme_templates",
            description="List all available meme templates",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "list_meme_templates":
        template_list = "\n".join([f"- {name}: {template_id}" for name, template_id in MEME_TEMPLATES.items()])
        return [
            types.TextContent(
                type="text",
                text=f"Available meme templates:\n{template_list}"
            )
        ]
    
    elif name == "generate_meme":
        if not arguments:
            raise ValueError("Missing arguments for generate_meme")
        
        template = arguments.get("template")
        top_text = arguments.get("top_text", "")
        bottom_text = arguments.get("bottom_text", "")
        
        if template not in MEME_TEMPLATES:
            raise ValueError(f"Unknown template: {template}")
        
        template_id = MEME_TEMPLATES[template]
        
        # Call imgflip API to generate meme
        try:
            url = "https://api.imgflip.com/caption_image"
            params = {
                'template_id': template_id,
                'username': 'adityajag2897',
                'password': 'M3fTquKHz8.k9.6',
                'text0': top_text,
                'text1': bottom_text
            }
            
            response = requests.post(url, data=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                meme_url = result['data']['url']
                return [
                    types.TextContent(
                        type="text",
                        text=f"Meme generated successfully!\nTemplate: {template}\nTop text: {top_text}\nBottom text: {bottom_text}\nURL: {meme_url}"
                    )
                ]
            else:
                error_message = result.get('error_message', 'Unknown error')
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to generate meme: {error_message}"
                    )
                ]
                
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to generate meme due to API error: {str(e)}"
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
                server_name="meme-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())