#!/usr/bin/env python3
"""
Enhanced MCP Implementation
Official MCP SDK + LangChain MCP Adapters (Current Version Compatible)
Prepared for Streamable HTTP when available
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

# Official MCP SDK
from mcp import ClientSession
from mcp.types import Tool as MCPTool, CallToolResult

# LangChain MCP Adapters
try:
    from langchain_mcp_adapters.tools import load_mcp_tools
    LANGCHAIN_MCP_AVAILABLE = True
except ImportError:
    LANGCHAIN_MCP_AVAILABLE = False
    print("⚠️ LangChain MCP adapters not available, using fallback implementation")

# LangChain Components
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field, create_model

# HTTP and Async
import httpx
import aiohttp

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
    Enhanced HTTP transport for MCP protocol
    Ready for Streamable HTTP upgrade
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
        """Send JSON-RPC request with enhanced error handling"""
        request_data = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params or {}
        }
        
        try:
            # Use a fresh session for each request to avoid context issues
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

class EnhancedMCPSession:
    """
    Enhanced MCP Session with official SDK compatibility
    """
    
    def __init__(self, transport: HTTPMCPTransport):
        self.transport = transport
        self._tools: List[MCPTool] = []
        self._initialized = False
    
    async def initialize(self) -> Dict:
        """Initialize MCP session with enhanced protocol"""
        try:
            result = await self.transport.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "enhanced-mcp-client",
                    "version": "2.0.0"
                }
            })
            
            self._initialized = True
            logger.info("✅ Enhanced MCP session initialized")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP session: {e}")
            raise
    
    async def list_tools(self) -> List[MCPTool]:
        """List tools with enhanced parsing"""
        try:
            result = await self.transport.send_request("tools/list")
            
            if "result" in result and "tools" in result["result"]:
                tools_data = result["result"]["tools"]
                self._tools = []
                
                for tool_data in tools_data:
                    # Create MCPTool with enhanced validation
                    tool = MCPTool(
                        name=tool_data.get("name", "unknown"),
                        description=tool_data.get("description", ""),
                        inputSchema=tool_data.get("inputSchema", {})
                    )
                    self._tools.append(tool)
                
                logger.info(f"✅ Found {len(self._tools)} tools")
                return self._tools
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
            return []
    
    async def call_tool(self, name: str, arguments: Dict) -> CallToolResult:
        """Call tool with enhanced error handling"""
        try:
            result = await self.transport.send_request("tools/call", {
                "name": name,
                "arguments": arguments
            })
            
            if "result" in result:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": json.dumps(result["result"])
                    }]
                )
            
            return CallToolResult(content=[{
                "type": "text", 
                "text": "No result returned"
            }])
            
        except Exception as e:
            logger.error(f"❌ Tool call failed: {e}")
            return CallToolResult(content=[{
                "type": "text",
                "text": f"Error: {str(e)}"
            }])

class EnhancedMCPToolAdapter:
    """
    Enhanced tool adapter with LangChain integration
    """
    
    def __init__(self, session: EnhancedMCPSession):
        self.session = session
    
    async def _call_tool_async(self, tool_name: str, arguments: Dict):
        """Async helper for tool calls"""
        return await self.session.call_tool(tool_name, arguments)
    
    async def create_langchain_tools(self, tools: List[MCPTool]) -> List[BaseTool]:
        """Create LangChain tools from MCP tools"""
        langchain_tools = []
        
        for mcp_tool in tools:
            # Create dynamic input model based on MCP tool schema
            input_schema = mcp_tool.inputSchema or {}
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            # Create fields for the input model
            fields = {}
            for prop_name, prop_info in properties.items():
                field_type = str  # Default to string
                field_description = prop_info.get("description", f"{prop_name} parameter")
                
                if prop_name in required:
                    fields[prop_name] = (field_type, Field(description=field_description))
                else:
                    fields[prop_name] = (field_type, Field(default=None, description=field_description))
            
            # Create dynamic input model
            ToolInput = create_model(f"{mcp_tool.name}Input", **fields)
            
            # Create tool function
            def create_tool_func(tool_name: str):
                def sync_tool_func(**kwargs) -> str:
                    try:
                        # Filter out None values
                        arguments = {k: v for k, v in kwargs.items() if v is not None}
                        logger.info(f"🔧 Executing {tool_name} with: {arguments}")
                        
                        # Use a new event loop in a thread for Streamlit compatibility
                        import threading
                        import concurrent.futures
                        
                        def run_async_in_thread():
                            # Create a new event loop for this thread
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(self._call_tool_async(tool_name, arguments))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async_in_thread)
                            result = future.result(timeout=30)
                        
                        if result.content:
                            content_item = result.content[0]
                            # Handle both dict and TextContent object formats
                            if hasattr(content_item, 'text'):
                                return content_item.text
                            elif isinstance(content_item, dict):
                                return content_item.get("text", "No content")
                            else:
                                return str(content_item)
                        return "No result"
                        
                    except Exception as e:
                        logger.error(f"❌ Tool call failed: {e}")
                        return f"Error executing {tool_name}: {str(e)}"
                
                return sync_tool_func
            
            # Create LangChain tool
            langchain_tool = StructuredTool(
                name=mcp_tool.name,
                description=mcp_tool.description or f"MCP tool: {mcp_tool.name}",
                args_schema=ToolInput,
                func=create_tool_func(mcp_tool.name)
            )
            
            langchain_tools.append(langchain_tool)
        
        return langchain_tools

class EnhancedMCPClient:
    """
    Enhanced MCP Client with official SDK integration and LangChain adapters
    """
    
    def __init__(self):
        self.sessions: Dict[str, EnhancedMCPSession] = {}
        self.transports: Dict[str, HTTPMCPTransport] = {}
        self.langchain_tools: List[BaseTool] = []
        self.agent_executor: Optional[AgentExecutor] = None
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
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
        """Add MCP server with enhanced connection"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Connecting to {server_name}...", total=None)
                
                # Create transport and session
                transport = HTTPMCPTransport(base_url)
                session = EnhancedMCPSession(transport)
                await session.initialize()
                
                # Store connections
                self.transports[server_name] = transport
                self.sessions[server_name] = session
                
                progress.update(task, description=f"✅ Connected to {server_name}")
            
            logger.info(f"✅ Added MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add server {server_name}: {e}")
            return False
    
    async def load_tools(self):
        """Load tools from all connected servers"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Loading tools...", total=None)
                
                all_tools = []
                
                for server_name, session in self.sessions.items():
                    try:
                        # Get MCP tools
                        mcp_tools = await session.list_tools()
                        
                        # Convert to LangChain tools
                        adapter = EnhancedMCPToolAdapter(session)
                        langchain_tools = await adapter.create_langchain_tools(mcp_tools)
                        
                        all_tools.extend(langchain_tools)
                        logger.info(f"✅ Loaded {len(langchain_tools)} tools from {server_name}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to load tools from {server_name}: {e}")
                
                self.langchain_tools = all_tools
                progress.update(task, description=f"✅ Loaded {len(all_tools)} total tools")
                
            if self.langchain_tools:
                await self._create_agent()
                
        except Exception as e:
            logger.error(f"❌ Failed to load tools: {e}")
    
    async def _create_agent(self):
        """Create enhanced LangChain agent"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an advanced AI assistant with access to MCP (Model Context Protocol) tools.

🎯 Your capabilities:
- Access to multiple MCP servers via enhanced HTTP transport
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
            
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.langchain_tools,
                prompt=prompt
            )
            
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.langchain_tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="generate"
            )
            
            logger.info(f"✅ Enhanced agent created with {len(self.langchain_tools)} tools")
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent: {e}")
    
    async def chat(self, message: str) -> str:
        """Chat with enhanced MCP agent"""
        try:
            if not self.agent_executor:
                return "❌ Agent not initialized. Please add MCP servers first."
            
            console.print(Panel(
                f"[bold blue]User:[/bold blue] {message}",
                border_style="blue"
            ))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Processing...", total=None)
                
                result = await self.agent_executor.ainvoke({
                    "input": message,
                    "tool_names": [tool.name for tool in self.langchain_tools]
                })
                
                progress.update(task, description="✅ Complete")
            
            response = result.get("output", "No response generated")
            
            console.print(Panel(
                f"[bold green]Assistant:[/bold green] {response}",
                border_style="green"
            ))
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Error: {e}"
            logger.error(error_msg)
            return error_msg
    
    async def close(self):
        """Clean up all connections"""
        try:
            for server_name, transport in self.transports.items():
                await transport.__aexit__(None, None, None)
                logger.info(f"✅ Closed {server_name}")
            
            self.sessions.clear()
            self.transports.clear()
            self.langchain_tools.clear()
            self.agent_executor = None
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

# Example usage
async def main():
    """Demo of Enhanced MCP Client"""
    console.print(Panel(
        "[bold cyan]🚀 Enhanced MCP Client Demo[/bold cyan]\n"
        "Official MCP SDK + Enhanced HTTP + LangChain Integration",
        border_style="cyan"
    ))
    
    client = EnhancedMCPClient()
    
    try:
        # Add MCP server
        await client.add_mcp_server("weather", "http://localhost:8001")
        
        # Load tools
        await client.load_tools()
        
        # Interactive chat
        while True:
            try:
                user_input = console.input("\n[bold blue]You:[/bold blue] ")
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    break
                
                await client.chat(user_input)
                
            except KeyboardInterrupt:
                break
    
    finally:
        await client.close()
        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")

if __name__ == "__main__":
    asyncio.run(main())