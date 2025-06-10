#!/usr/bin/env python3
"""
OpenAI Function Calling Assistant - Streamlit App
Multi-purpose assistant demonstrating OpenAI Function Calling
Supports weather, calculations, and other utility functions
"""

import logging
import sys
import time
from pathlib import Path

import streamlit as st

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent))

from function_client import get_function_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="OpenAI Function Calling Assistant",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "client_initialized" not in st.session_state:
        st.session_state.client_initialized = False
    
    if "function_client" not in st.session_state:
        st.session_state.function_client = None

def add_message(role: str, content: str):
    """
    Add a message to the chat history
    
    Args:
        role: Message role ('user' or 'assistant')
        content: Message content
    """
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": time.time()
    })

def display_chat_messages():
    """Display all chat messages"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_user_query(user_input: str) -> str:
    """
    Process user query using the weather client
    
    Args:
        user_input: User's input string
        
    Returns:
        Response string
    """
    try:
        # Get function client
        if st.session_state.function_client is None:
            st.session_state.function_client = get_function_client()
        
        # Process the query
        response = st.session_state.function_client.process_query(user_input)
        st.session_state.client_initialized = True
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return f"❌ Sorry, I encountered an error: {str(e)}"

def display_sidebar():
    """Display the sidebar with information and controls"""
    with st.sidebar:
        st.header("🚀 Function Calling Assistant")
        
        st.markdown("""
        **Features:**
        - 🌤️ Current weather information
        - 📅 Weather forecasts
        - 🧠 OpenAI Function Calling
        - ⚡ Real-time data
        """)
        
        st.markdown("---")
        
        # Status
        st.header("🔌 Status")
        
        if st.session_state.client_initialized:
            st.success("✅ Weather Client Connected")
        else:
            st.info("🔄 Weather Client Ready")
        
        st.markdown("---")
        
        # Example queries
        st.header("📋 Example Queries")
        
        example_queries = [
            "What's the weather in London?",
            "How's the weather in Tokyo today?",
            "Get me weather for New York",
            "What's the temperature in Paris?",
            "Weather forecast for Sydney",
            "Is it raining in Seattle?"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{hash(query)}", use_container_width=True):
                st.session_state.example_query = query
        
        st.markdown("---")
        
        # Information
        st.header("ℹ️ How it works")
        
        st.markdown("""
        1. **User Query**: You ask about weather
        2. **OpenAI Analysis**: AI decides if weather function needed
        3. **Function Call**: Weather API called with location
        4. **Response**: Natural language weather report
        """)
        
        st.markdown("---")
        
        # Controls
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

def main():
    """Main Streamlit application"""
    
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.title("🚀 OpenAI Function Calling Assistant")
    st.markdown("*Demonstrating pure OpenAI Function Calling for weather information*")
    
    # Display sidebar
    display_sidebar()
    
    # Main chat interface
    st.markdown("### 💬 Chat with Weather Assistant")
    
    # Display chat messages
    display_chat_messages()
    
    # Handle example query from sidebar
    if hasattr(st.session_state, 'example_query'):
        user_input = st.session_state.example_query
        del st.session_state.example_query
        
        # Add user message
        add_message("user", user_input)
        
        # Process query and add response
        with st.chat_message("assistant"):
            with st.spinner("🌤️ Getting weather information..."):
                try:
                    response = process_user_query(user_input)
                    st.markdown(response)
                    add_message("assistant", response)
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    add_message("assistant", error_msg)
        
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Ask me about the weather in any city..."):
        # Add user message
        add_message("user", prompt)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🌤️ Getting weather information..."):
                try:
                    response = process_user_query(prompt)
                    st.markdown(response)
                    add_message("assistant", response)
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    add_message("assistant", error_msg)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <small>
        🌤️ Built with <strong>OpenAI Function Calling</strong> | 
        Weather data from Weatherstack API | 
        Powered by Streamlit
        </small>
    </div>
    """, unsafe_allow_html=True)
    
    # Function calling info
    with st.expander("🔍 Function Calling Details"):
        st.markdown("""
        **Available Functions:**
        - `get_current_weather(location)` - Get current weather for any location
        - `get_weather_forecast(location, days)` - Get weather forecast
        
        **How it works:**
        1. Your message is sent to OpenAI with function definitions
        2. OpenAI decides whether to call weather functions
        3. If needed, weather functions are executed with extracted parameters
        4. Results are sent back to OpenAI for natural language formatting
        5. You receive a conversational weather report
        
        This follows the exact pattern from [OpenAI Function Calling documentation](https://platform.openai.com/docs/guides/function-calling).
        """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        st.error(f"Application error: {e}")