#!/usr/bin/env python3
"""
Test script for OpenAI Function Calling Assistant
"""

import sys
sys.path.append('src')

from function_client import get_function_client

def main():
    """Test the function calling client"""
    print('=== Testing OpenAI Function Calling Assistant ===')
    
    # Get function client
    client = get_function_client()
    print(f'Client initialized: {client.openai_client is not None}')
    
    # Test queries
    if client.openai_client:
        test_queries = [
            "What is the weather in London?",
            "Get me a forecast for Tokyo",
            "What's the weather in Paris and New York?",
            # Add more test cases as you add functions:
            # "Calculate BMI for height 175cm and weight 70kg",
            # "What's 15% tip on $50?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f'\n{"="*60}')
            print(f'Test {i}: "{query}"')
            print('='*60)
            response = client.process_query(query)
            print(f'Response:\n{response}')
    else:
        print('❌ Client not initialized - check API keys')

if __name__ == "__main__":
    main()