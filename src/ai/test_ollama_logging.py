#!/usr/bin/env python3
"""
Test script to demonstrate comprehensive Ollama logging functionality.

This script shows how all Ollama model calls are now logged with full parameter details
including defaults that weren't explicitly passed.
"""

import asyncio
import json
from typing import Dict, Any

from ollama_client import OllamaClient


async def test_comprehensive_logging():
    """Test the comprehensive Ollama logging implementation."""
    print("🧪 Testing Ollama Comprehensive Logging")
    print("=" * 50)
    
    # Initialize Ollama client
    client = OllamaClient()
    
    try:
        await client.initialize()
        print("✅ Ollama client initialized")
        
        # Test 1: Generate with minimal parameters (will show many defaults)
        print("\n📝 Test 1: Generate with minimal parameters")
        result1 = await client.generate(
            model="llama2:7b",
            prompt="What is 2+2?"
        )
        print(f"Result: {result1[:100]}...")
        
        # Test 2: Generate with some custom parameters
        print("\n📝 Test 2: Generate with custom parameters")
        result2 = await client.generate(
            model="llama2:7b", 
            prompt="Explain quantum computing briefly.",
            temperature=0.3,
            max_tokens=200,
            top_p=0.95
        )
        print(f"Result: {result2[:100]}...")
        
        # Test 3: Chat with conversation
        print("\n📝 Test 3: Chat conversation")
        messages = [
            {"role": "user", "content": "Hello, who are you?"},
            {"role": "assistant", "content": "I'm an AI assistant."},
            {"role": "user", "content": "What can you help me with?"}
        ]
        result3 = await client.chat(
            model="llama2:7b",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        print(f"Result: {result3[:100]}...")
        
        # Test 4: Tactical analysis (high-level method)
        print("\n📝 Test 4: Tactical Analysis")
        game_state = {
            "units": [
                {"id": "unit1", "hp": 100, "position": {"x": 1, "y": 1}},
                {"id": "unit2", "hp": 80, "position": {"x": 3, "y": 3}}
            ],
            "turn": 5,
            "grid_size": {"width": 8, "height": 8}
        }
        result4 = await client.tactical_analysis_prompt(game_state, "unit1")
        print(f"Result: {result4[:100]}...")
        
        # Test 5: Decision making with different difficulty
        print("\n📝 Test 5: Decision Making")
        result5 = await client.decision_making_prompt(
            game_state, 
            "unit1", 
            ["move", "attack", "defend"], 
            "hard"
        )
        print(f"Result: {result5[:100]}...")
        
        print("\n✅ All tests completed successfully!")
        print("\n📊 Check the logs above to see comprehensive parameter logging")
        print("   - Model names, prompts, and all parameters are logged")
        print("   - Default values that weren't explicitly passed are shown")
        print("   - Execution times and response lengths are tracked")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_comprehensive_logging())