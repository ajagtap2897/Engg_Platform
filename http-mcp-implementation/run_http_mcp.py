#!/usr/bin/env python3
"""
Enhanced MCP Application Runner
Starts both the Enhanced MCP server and Streamlit app
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path

def run_server():
    """Run the Enhanced MCP weather server"""
    print("🌐 Starting Enhanced MCP Weather Server...")
    try:
        subprocess.run([
            sys.executable, 
            "mcp_servers/http_weather_server.py"
        ], check=True)
    except KeyboardInterrupt:
        print("🛑 Enhanced MCP Server stopped")
    except Exception as e:
        print(f"❌ Enhanced MCP Server error: {e}")

def run_streamlit():
    """Run the Enhanced MCP interactive client"""
    print("🚀 Starting Enhanced MCP Interactive Client...")
    time.sleep(3)  # Wait for server to start
    try:
        subprocess.run([
            sys.executable, 
            "src/enhanced_mcp_adapter.py"
        ], check=True)
    except KeyboardInterrupt:
        print("🛑 Enhanced MCP Interactive Client stopped")
    except Exception as e:
        print(f"❌ Enhanced MCP Interactive Client error: {e}")

def main():
    """Main function to run both server and interactive client"""
    print("🚀 Starting Enhanced MCP Application...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/enhanced_mcp_adapter.py").exists():
        print("❌ Error: Please run this script from the http-mcp-implementation directory")
        sys.exit(1)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Start interactive client
    try:
        run_streamlit()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Enhanced MCP Application...")
    except Exception as e:
        print(f"❌ Enhanced MCP Application error: {e}")

if __name__ == "__main__":
    main()