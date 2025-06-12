#!/usr/bin/env python3
"""
Test script for Enhanced MCP Client - Windows console safe version
"""

from src.enhanced_mcp_adapter import EnhancedMCPClient
import asyncio

async def test_client():
    """Test the enhanced MCP client functionality"""
    client = EnhancedMCPClient()
    
    try:
        # Add MCP server
        success = await client.add_mcp_server('weather', 'http://localhost:8001')
        if not success:
            print('FAIL: Failed to connect to weather server')
            return
        
        # Load tools
        await client.load_tools()
        
        # Check available tools
        if client.langchain_tools:
            print(f'SUCCESS: Available tools: {[tool.name for tool in client.langchain_tools]}')
            
            # Test a simple query
            result = await client.chat("What's the weather like in London?")
            print(f'SUCCESS: Chat result: {result}')
        else:
            print('FAIL: No tools loaded')
        
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_client())