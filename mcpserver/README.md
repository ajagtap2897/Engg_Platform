# MCP Servers Collection

This directory contains three Model Context Protocol (MCP) servers that demonstrate different capabilities:

## Servers Included

### 1. Meme Generator Server (`meme_server.py`)
- **Purpose**: Generate memes using popular templates
- **Tools**:
  - `generate_meme`: Create a meme with top and bottom text
  - `list_meme_templates`: List available meme templates
- **Templates**: Drake, Distracted Boyfriend, Woman Yelling at Cat, Two Buttons, Change My Mind, and more
- **API**: Uses imgflip.com API for meme generation (configured with real credentials)

### 2. Weather Server (`weather_server.py`)
- **Purpose**: Provide weather information and forecasts
- **Tools**:
  - `get_weather`: Get current weather for a city
  - `get_forecast`: Get 5-day weather forecast
- **Units**: Supports metric (Celsius), imperial (Fahrenheit), and Kelvin
- **API**: Uses WeatherStack API for real weather data (configured with real API key)

### 3. Calculator Server (`calculator_server.py`)
- **Purpose**: Perform mathematical calculations
- **Tools**:
  - `add`: Addition
  - `subtract`: Subtraction
  - `multiply`: Multiplication
  - `divide`: Division (with zero-division protection)
  - `power`: Exponentiation
  - `sqrt`: Square root
  - `factorial`: Factorial calculation

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### 2. Installation
```bash
# Navigate to the mcpserver directory
cd d:/mcp/mcpserver

# Activate the virtual environment
.\Scripts\Activate.ps1

# Install required packages
pip install mcp requests
```

### 3. Testing Individual Servers
You can test each server individually:

```bash
# Test meme server
python meme_server.py

# Test weather server  
python weather_server.py

# Test calculator server
python calculator_server.py
```

### 4. Cursor IDE Integration

To use these servers with Cursor IDE:

1. **Create MCP config file**:
   - Windows: `~/.cursor/mcp.json`
   - macOS: `~/.cursor/mcp.json`

2. **Add the following configuration**:
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["path/to/mcpserver/weather_server.py"],
      "env": {
        "PYTHONPATH": "path/to/mcpserver"
      }
    },
    "calculator": {
      "command": "python", 
      "args": ["path/to/mcpserver/calculator_server.py"],
      "env": {
        "PYTHONPATH": "path/to/mcpserver"
      }
    },
    "meme-generator": {
      "command": "python",
      "args": ["path/to/mcpserver/meme_server.py"],
      "env": {
        "PYTHONPATH": "path/to/mcpserver"
      }
    }
  }
}
```

3. **Replace `path/to/mcpserver`** with the actual path to your mcpserver directory.

4. **Restart Cursor IDE** for the changes to take effect.

5. **Enable MCP in Cursor**: Go to Settings → MCP and ensure MCP servers are enabled.

### 5. Demo: How MCP Servers Work

#### 🏗️ **What is MCP (Model Context Protocol)?**

MCP is a protocol that allows AI assistants (like Claude, Cursor AI) to connect to external tools and services. Think of it as a bridge between AI and your applications.

```
┌─────────────┐    MCP Protocol    ┌─────────────────┐    API Calls    ┌─────────────┐
│   Cursor    │ ◄─────────────────► │   MCP Server    │ ◄──────────────► │ External API│
│     AI      │                    │ (Python Script) │                  │ (Weather,   │
│             │                    │                 │                  │  Memes)     │
└─────────────┘                    └─────────────────┘                  └─────────────┘
```

#### 🔧 **How Our MCP Servers Are Built**

Each server follows this structure:

```python
# 1. Import MCP framework
from mcp import ClientSession, StdioServerParameters
from mcp.server import Server
from mcp.server.stdio import stdio_server

# 2. Create server instance
app = Server("server-name")

# 3. Define available tools
@app.list_tools()
async def list_tools():
    return [
        Tool(name="tool_name", description="What it does", inputSchema={...})
    ]

# 4. Implement tool functionality
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "tool_name":
        # Your logic here
        return [TextContent(type="text", text="Result")]

# 5. Run the server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
```

#### 🚀 **Step-by-Step Connection Demo**

**Step 1: Create MCP Server** (Already done!)
```bash
# Our servers are ready:
d:/mcp/mcpserver/
├── weather_server.py    # Connects to WeatherStack API
├── meme_server.py       # Connects to ImgFlip API  
└── calculator_server.py # Pure math calculations
```

**Step 2: Configure Cursor** (What we did)
```json
// ~/.cursor/mcp.json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["d:/mcp/mcpserver/weather_server.py"]
    }
  }
}
```

**Step 3: Cursor Connects to Server**
```
Cursor AI ──► Reads ~/.cursor/mcp.json
          ──► Launches: python weather_server.py
          ──► Establishes MCP connection
          ──► Discovers available tools
          ──► Ready to use tools!
```

**Step 4: AI Uses Tools**
```
User: "What's the weather in Tokyo?"
  ↓
Cursor AI: Calls weather_server → get_weather(city="Tokyo")
  ↓
MCP Server: Makes API call to WeatherStack
  ↓
WeatherStack: Returns weather data
  ↓
MCP Server: Formats response for AI
  ↓
Cursor AI: Shows user the weather information
```

#### 🎯 **Live Usage Examples**

Once configured with Cursor IDE, you can use these tools by asking the AI to:

**Meme Generator**:
- "Generate a Drake meme with 'Old way of doing things' on top and 'New MCP way' on bottom"
- "List all available meme templates"
- "Create a 'Woman Yelling at Cat' meme about debugging code"

**Weather**:
- "What's the weather like in New York?"
- "Get a 5-day forecast for London in Fahrenheit"
- "Compare the weather in Tokyo and Sydney"

**Calculator**:
- "Calculate 15 + 27"
- "What's the square root of 144?"
- "Calculate 5 factorial"
- "What's 2 to the power of 10?"

#### 🔍 **Behind the Scenes**

When you ask Cursor AI to "Get weather for Paris":

1. **AI Decision**: Cursor recognizes this needs the weather tool
2. **MCP Call**: Sends `get_weather(city="Paris", units="metric")` to weather_server.py
3. **API Request**: Server calls WeatherStack API with your request
4. **Data Processing**: Server formats the JSON response into readable text
5. **Response**: AI receives formatted weather data and presents it to you

#### 🛠️ **Extending the Servers**

Want to add a new tool? Here's how:

```python
# Add to list_tools()
Tool(
    name="get_humidity", 
    description="Get humidity for a city",
    inputSchema={"type": "object", "properties": {"city": {"type": "string"}}}
)

# Add to call_tool()
elif name == "get_humidity":
    city = arguments.get("city")
    # Your implementation here
    return [TextContent(type="text", text=f"Humidity in {city}: 65%")]
```

#### 🌐 **Why MCP is Powerful**

- **Standardized**: Works with any MCP-compatible AI (Claude, Cursor, etc.)
- **Secure**: AI can't directly access your system - only through defined tools
- **Extensible**: Easy to add new capabilities
- **Isolated**: Each server runs independently
- **Real-time**: Live data from APIs, not static information

## File Structure

### Essential Files (Required)
```
mcpserver/
├── meme_server.py              # Meme generator MCP server
├── weather_server.py           # Weather information MCP server
├── calculator_server.py        # Mathematical calculator MCP server
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # This documentation
```


## 🏗️ Development Architecture

### MCP Server Design Pattern

Our servers follow a consistent architecture:

```python
# 1. Server Setup
app = Server("server-name")

# 2. Tool Registration  
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(...), Tool(...)]

# 3. Tool Implementation
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "tool1":
        return handle_tool1(arguments)
    elif name == "tool2": 
        return handle_tool2(arguments)

# 4. Server Runtime
async def main():
    async with stdio_server() as streams:
        await app.run(*streams, app.create_initialization_options())
```

### 🔧 **Server Comparison**

| Server | External API | Complexity | Use Case |
|--------|-------------|------------|----------|
| **Calculator** | ❌ None | Simple | Pure computation, input validation |
| **Weather** | ✅ WeatherStack | Medium | API integration, data formatting |
| **Meme** | ✅ ImgFlip | Medium | API auth, image generation |

### 🚀 **Development Process**

#### **1. Planning Phase**
```
Identify Need → Define Tools → Choose APIs → Design Schema
```

#### **2. Implementation Phase**
```python
# Example: Adding a new "translate" tool
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="translate_text",
            description="Translate text between languages", 
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to translate"},
                    "from_lang": {"type": "string", "description": "Source language"},
                    "to_lang": {"type": "string", "description": "Target language"}
                },
                "required": ["text", "to_lang"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "translate_text":
        # Implementation here
        text = arguments["text"]
        to_lang = arguments["to_lang"]
        # Call translation API...
        return [TextContent(type="text", text=f"Translated: {result}")]
```

#### **3. Testing Phase**
```bash
# Test server directly
python new_server.py

# Test with Cursor
# Add to ~/.cursor/mcp.json and test through AI
```

### 🛡️ **Error Handling Strategy**

All servers implement layered error handling:

```python
async def call_tool(name: str, arguments: dict):
    try:
        # 1. Input validation
        if not arguments.get("required_param"):
            return [TextContent(type="text", text="Error: Missing required parameter")]
        
        # 2. Business logic
        result = await external_api_call(arguments)
        
        # 3. Response formatting
        return [TextContent(type="text", text=format_response(result))]
        
    except APIError as e:
        # 4. API-specific errors
        return [TextContent(type="text", text=f"API Error: {e}")]
    except Exception as e:
        # 5. Unexpected errors
        logging.error(f"Unexpected error: {e}")
        return [TextContent(type="text", text="An unexpected error occurred")]
```

### 📊 **Performance Considerations**

- **Async/Await**: All operations are asynchronous for better performance
- **Connection Pooling**: Reuse HTTP connections for API calls
- **Caching**: Consider caching frequently requested data
- **Timeouts**: Set reasonable timeouts for external API calls

### 🔄 **Adding New Tools**

To add new tools to any server:

1. **Define the tool** in `list_tools()`:
```python
Tool(name="new_tool", description="What it does", inputSchema={...})
```

2. **Implement the logic** in `call_tool()`:
```python
elif name == "new_tool":
    return handle_new_tool(arguments)
```

3. **Add helper function**:
```python
async def handle_new_tool(arguments: dict) -> list[TextContent]:
    # Your implementation
    return [TextContent(type="text", text="Result")]
```

4. **Update server version** if needed

### 🧪 **Testing Strategy**

```python
# Unit testing individual functions
def test_calculator_add():
    result = add(5, 3)
    assert result == 8

# Integration testing with MCP
async def test_mcp_tool():
    result = await call_tool("add", {"a": 5, "b": 3})
    assert "8" in result[0].text

# End-to-end testing with Cursor
# Manual testing through Cursor AI interface
```

### 📝 **Logging & Debugging**

Each server includes comprehensive logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Usage in tools
logging.info(f"Processing request: {name} with args: {arguments}")
logging.error(f"API call failed: {error}")
```

## Troubleshooting

### ⚠️ **Critical Environment Issue We Encountered**

**Problem**: Virtual Environment Path Conflicts

When we initially set up the MCP servers, we encountered a critical issue where Cursor couldn't find the required MCP packages, even though they were installed in our virtual environment.

#### **The Issue**
```json
// ❌ This configuration failed:
{
  "mcpServers": {
    "weather": {
      "command": "d:/mcp/Scripts/python.exe",  // Virtual env Python
      "args": ["d:/mcp/mcpserver/weather_server.py"]
    }
  }
}
```

**Error Messages**:
- `ModuleNotFoundError: No module named 'mcp'`
- `ImportError: cannot import name 'Server' from 'mcp.server'`
- Servers would fail to start in Cursor

#### **Root Cause**
The virtual environment's Python interpreter couldn't locate the MCP packages when launched by Cursor, even though:
- ✅ Packages were installed: `pip install mcp`
- ✅ Virtual environment was activated
- ✅ Servers worked when run manually: `python weather_server.py`

#### **The Solution**
We switched to using the **system Python** instead of the virtual environment Python:


#### **Why This Works**
1. **System Python**: Uses the global Python installation
2. **PYTHONPATH**: Ensures Python can find modules in the project directory
3. **Cursor Compatibility**: System Python integrates better with Cursor's process management


### Common Issues

1. **Import Errors**: Make sure the MCP package is installed in your Python environment
2. **Path Issues**: Ensure all paths in the configuration are absolute and correct
3. **Permission Issues**: Make sure Python has permission to execute the server files
4. **API Limits**: The meme server uses a public test account which may have rate limits
5. **Virtual Environment Conflicts**: See the detailed section above for environment-related issues

### 🧪 **Testing Connection**

You can test if a server is working by running it directly:

```bash
# Test individual server
python weather_server.py

# Should show: Server starting and waiting for connections...
# Press Ctrl+C to stop
```

### 🔍 **Debugging Environment Issues**

If your servers aren't working in Cursor, run these diagnostic commands:

```bash
# 1. Check which Python Cursor is using
where python

# 2. Check if MCP is installed in that Python
python -c "import mcp; print('MCP installed successfully')"

# 3. Test server manually
python d:/mcp/mcpserver/weather_server.py

# 4. Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

**Expected Output**:
- ✅ `MCP installed successfully`
- ✅ `Server starting and waiting for connections...`
- ❌ `ModuleNotFoundError` → Install MCP in the correct Python environment

## 📚 Resources

### **MCP Documentation**
- [Official MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### **API Resources**
- [WeatherStack API](https://weatherstack.com/documentation)
- [ImgFlip API](https://imgflip.com/api)

### **Cursor IDE**
- [Cursor Documentation](https://docs.cursor.com/)
- [MCP Integration Guide](https://docs.cursor.com/mcp)



