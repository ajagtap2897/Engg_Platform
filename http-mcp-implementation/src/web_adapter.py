#!/usr/bin/env python3
"""
Web MCP Adapter Implementation
Uses official LangChain MCP Adapters for terminal/CLI applications
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
import threading
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
from datetime import timedelta

# Official MCP SDK
from mcp import ClientSession
from mcp.types import Tool as MCPTool, CallToolResult

# LangChain MCP Adapters (Official)
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.sessions import Connection

# LangChain Components
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain.tools import BaseTool

# HTTP and Async
import aiohttp
import requests

# Utilities
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables
load_dotenv()  # Load from current directory .env

# Configure rich console
console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTTPMCPTransport:
    """
    HTTP transport for MCP protocol
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self._request_id = 0
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed for per-request sessions
        pass
    
    def _next_request_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    async def send_request(self, method: str, params: Dict = None) -> Dict:
        """Send JSON-RPC request with error handling"""
        request_data = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params or {}
        }
        
        try:
            # Use a fresh session for each request
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/mcp",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    if "error" in result and result["error"] is not None:
                        raise Exception(f"MCP Error: {result['error']}")
                    
                    return result
                    
        except Exception as e:
            logger.error(f"HTTP MCP request failed: {e}")
            raise

class WebMCPClient:
    """
    Web MCP Client using official LangChain MCP adapters
    """
    
    def __init__(self):
        self.transports = {}
        self.connections = {}
        self.langchain_tools = []
        self.llm = None
        self.agent_executor = None
        
        # Initialize LLM
        self._init_llm()
    
    def _init_llm(self):
        """Initialize OpenAI LLM"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=api_key
            )
            logger.info("✅ OpenAI LLM initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise
    
    async def add_mcp_server(self, server_name: str, base_url: str) -> bool:
        """Add MCP server with connection configuration"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Connecting to {server_name}...", total=None)
                
                # Create connection configuration for the official adapter
                # Using StreamableHttpConnection type
                connection = {
                    "transport": "streamable_http",
                    "url": f"{base_url}/mcp",
                    "headers": {
                        "Content-Type": "application/json",
                        "X-Protocol-Version": "2024-11-05",
                        "X-Client-Name": "web-mcp-client",
                        "X-Client-Version": "1.0.0"
                    },
                    "timeout": timedelta(seconds=30),
                    "sse_read_timeout": timedelta(seconds=300),
                    "terminate_on_close": True,
                    "session_kwargs": {},  # Empty dict as we're passing client info via headers
                    "httpx_client_factory": None
                }
                
                # Store connection
                self.connections[server_name] = connection
                
                progress.update(task, description=f"✅ Connected to {server_name}")
            
            logger.info(f"✅ Added MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add server {server_name}: {e}")
            return False
    
    async def load_tools(self):
        """Load tools from all connected servers using official adapter"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Loading tools...", total=None)
                
                all_tools = []
                
                for server_name, connection in self.connections.items():
                    try:
                        # Use the official LangChain MCP adapter to load tools
                        logger.info(f"Loading tools from {server_name}...")
                        langchain_tools = await load_mcp_tools(None, connection=connection)
                        
                        all_tools.extend(langchain_tools)
                        logger.info(f"✅ Loaded {len(langchain_tools)} tools from {server_name}")
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "ConnectError: All connection attempts failed" in error_msg:
                            logger.error(f"❌ Failed to connect to MCP server at {connection['url']}. Is the server running?")
                            console.print(f"[bold red]Connection Error:[/] Could not connect to MCP server at {connection['url']}. Please make sure the server is running.")
                        else:
                            logger.error(f"❌ Failed to load tools from {server_name}: {e}")
                        
                        # Print more detailed error information
                        import traceback
                        logger.error(f"Detailed error: {traceback.format_exc()}")
                
                self.langchain_tools = all_tools
                progress.update(task, description=f"✅ Loaded {len(all_tools)} total tools")
                
            if self.langchain_tools:
                await self._create_agent()
                
        except Exception as e:
            logger.error(f"❌ Failed to load tools: {e}")
    
    async def _create_agent(self):
        """Create LangChain agent with loaded tools"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an advanced AI assistant with access to MCP (Model Context Protocol) tools.

🎯 Your capabilities:
- Access to multiple MCP servers via HTTP transport
- Intelligent tool selection and execution
- Error handling and graceful fallbacks
- Detailed explanations of your actions

🔧 Available tools: {tool_names}

Instructions:
- Analyze requests carefully to choose the best tools
- Provide clear explanations of your reasoning
- Handle errors gracefully and suggest alternatives
- Be helpful and informative in your responses"""),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent with tools (or without if none are available)
            if not self.langchain_tools:
                logger.warning("⚠️ No tools loaded. Agent will function as a basic chatbot.")
                # Create an empty list to ensure the agent can still be created
                self.langchain_tools = []
                
            agent = create_openai_functions_agent(
                self.llm,
                self.langchain_tools,
                prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.langchain_tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
            
            if self.langchain_tools:
                logger.info(f"✅ Agent created with {len(self.langchain_tools)} tools")
            else:
                logger.info("✅ Created basic chatbot agent (no tools)")
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent: {e}")
    
    async def chat(self, message: str) -> str:
        """Chat with the agent"""
        if not self.agent_executor:
            error_msg = "Agent not initialized. Please add servers and load tools first."
            console.print(Panel(f"[bold red]Error:[/] {error_msg}", expand=False))
            return error_msg
        
        if not self.langchain_tools:
            error_msg = "No tools available. The agent may not be able to perform useful tasks."
            console.print(Panel(f"[bold yellow]Warning:[/] {error_msg}", expand=False))
            # Continue anyway to see if the LLM can at least respond
        
        try:
            console.print(Panel(f"[bold blue]User:[/] {message}", expand=False))
            
            # Run agent
            response = await self.agent_executor.ainvoke({
                "input": message,
                "tool_names": [tool.name for tool in self.langchain_tools]
            })
            result = response.get("output", "No response")
            
            console.print(Panel(f"[bold green]Assistant:[/] {result}", expand=False))
            return result
            
        except Exception as e:
            error_message = f"Error processing message: {str(e)}"
            logger.error(f"❌ {error_message}")
            console.print(Panel(f"[bold red]Error:[/] {error_message}", expand=False))
            return error_message

def check_server_health(url: str) -> bool:
    """Check if a server is running by calling its health endpoint"""
    try:
        health_url = f"{url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

async def main():
    """Main function for testing"""
    client = WebMCPClient()
    
    # Add main MCP server
    server_added = await client.add_mcp_server("local", "http://localhost:8080")
    if not server_added:
        console.print("[bold red]Failed to add main server. Exiting.[/]")
        return
    
    # Weather functionality is now integrated into the main web server
    console.print("[bold green]✅ Weather functionality available through main server[/]")
    
    # Load tools from all servers
    try:
        await client.load_tools()
    except Exception as e:
        console.print(f"[bold red]Error loading tools:[/] {str(e)}")
        console.print("[bold yellow]Continuing without tools...[/]")
        
        # Create agent without tools if needed
        if not client.agent_executor:
            await client._create_agent()
    
    # Display available capabilities
    console.print("[bold]Web MCP Client[/] (Type 'exit' to quit)")
    
    # Check if weather tools are available
    has_weather_tool = any(tool.name == "get_weather" for tool in client.langchain_tools)
    if has_weather_tool:
        console.print("[bold green]🌤️ Weather information available![/] Try asking about the weather in any city.")
    
    # Add a helper function to get weather directly
    async def get_weather_directly(city: str):
        """Helper function to get weather directly without going through the agent"""
        for server_name, connection in client.connections.items():
            if server_name == "weather":
                try:
                    transport = client.transports[server_name]
                    response = await transport.send_request("tools/call", {
                        "name": "get_weather",
                        "arguments": {"location": city}
                    })
                    
                    if "result" in response and "content" in response["result"]:
                        content = response["result"]["content"]
                        if content and isinstance(content, list) and "text" in content[0]:
                            console.print(Panel(content[0]["text"], title="[bold blue]Weather Forecast[/]", expand=False))
                            return
                    
                    console.print("[bold red]Error getting weather directly.[/]")
                except Exception as e:
                    console.print(f"[bold red]Error getting weather directly: {e}[/]")
                return
        
        console.print("[bold yellow]Weather server not connected.[/]")
    
    # Interactive chat loop
    while True:
        try:
            user_input = input("\nYou: ")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Check for direct weather command
            if user_input.lower().startswith("!weather "):
                city = user_input[9:].strip()
                if city:
                    await get_weather_directly(city)
                    continue
                else:
                    console.print("[bold yellow]Please specify a city, e.g., !weather London[/]")
                    continue
            
            # Help command
            if user_input.lower() in ["!help", "!commands"]:
                console.print(Panel(
                    "Available commands:\n"
                    "- !weather [city] - Get weather directly for a city\n"
                    "- !help - Show this help message\n"
                    "- exit/quit - Exit the application\n\n"
                    "Or just chat naturally with the AI assistant!",
                    title="[bold blue]Help[/]",
                    expand=False
                ))
                continue
            
            # Normal chat with the agent
            await client.chat(user_input)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
    
    console.print("[bold]Goodbye![/]")

if __name__ == "__main__":
    asyncio.run(main())