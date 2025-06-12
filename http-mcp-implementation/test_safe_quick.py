#!/usr/bin/env python3
"""
Quick test script - Windows console safe version (no emojis)
"""

import asyncio
import sys
sys.path.append('src')

from enhanced_mcp_adapter import EnhancedMCPClient

async def quick_test():
    """Quick test of the Enhanced MCP system"""
    print("Testing Enhanced MCP System...")
    print("=" * 40)
    
    client = EnhancedMCPClient()
    
    try:
        # Test connection
        print("Testing server connection...")
        success = await client.add_mcp_server('weather', 'http://localhost:8001')
        
        if success:
            print("SUCCESS: Server connection successful!")
            
            # Load tools
            print("Loading tools...")
            await client.load_tools()
            
            if client.langchain_tools:
                print(f"SUCCESS: Loaded {len(client.langchain_tools)} tools:")
                for tool in client.langchain_tools:
                    print(f"   - {tool.name}: {tool.description}")
                
                # Test a simple query
                print("\nTesting query...")
                result = await client.chat("What's the weather in London?")
                print(f"SUCCESS: Response: {result[:100]}...")
                
                print("\nAll tests passed! System is ready.")
                return True
            else:
                print("FAIL: No tools loaded")
                return False
        else:
            print("FAIL: Server connection failed")
            print("Make sure the server is running:")
            print("   python mcp_servers/http_weather_server.py")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if success:
        print("\nReady to start Streamlit app!")
        print("Run: python run_http_mcp.py")
    else:
        print("\nPlease fix the issues above before starting the app")