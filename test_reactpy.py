#!/usr/bin/env python3
"""
Test ReactPy Integration

Simple test script to verify ReactPy button works alongside Ursina.
Run this to test the dual button setup.
"""

import asyncio
import time
from src.ui.reactpy.app import start_reactpy_server


def test_reactpy_standalone():
    """Test ReactPy server standalone"""
    print("🧪 Testing ReactPy server standalone...")
    print("🌐 Starting ReactPy server on http://localhost:8080")
    print("📝 You should see an orange 'End Turn' button on the web page")
    print("🔄 Click the button to test functionality")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        start_reactpy_server(8080)
    except KeyboardInterrupt:
        print("\n✅ ReactPy test completed")


if __name__ == "__main__":
    test_reactpy_standalone()