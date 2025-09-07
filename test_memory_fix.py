#!/usr/bin/env python3
"""
Test script to verify that the memory initialization issue has been fixed.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.analysis_services import AnalysisService
from tradingagents.default_config import DEFAULT_CONFIG

def test_memory_initialization():
    """Test that memory collections are properly initialized."""
    print("Testing memory initialization fix...")
    
    # Load environment variables
    load_dotenv()
    
    # Create analysis service
    service = AnalysisService()
    
    # Prepare test config
    test_config = {
        "llm_provider": "aliyun",
        "backend_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "deep_think_llm": "qwen2.5-72b-instruct",
        "quick_think_llm": "qwen2.5-32b-instruct",
        "aliyun_api_key": os.getenv("ALIYUN_API_KEY", "test-key"),
        "analysts": ["market", "news"]
    }
    
    try:
        # Test getting trading graph with analysts specified
        trading_graph = service.get_trading_graph(test_config)
        print("✓ Trading graph created successfully")
        
        # Test that memory collections are accessible
        print(f"✓ Bull memory collection: {trading_graph.bull_memory.situation_collection.name}")
        print(f"✓ Bear memory collection: {trading_graph.bear_memory.situation_collection.name}")
        print(f"✓ Trader memory collection: {trading_graph.trader_memory.situation_collection.name}")
        
        # Test that we can add situations (even empty ones)
        test_situations = [("Test situation", "Test recommendation")]
        trading_graph.bull_memory.add_situations(test_situations)
        print("✓ Successfully added test situation to bull memory")
        
        # Test retrieval
        memories = trading_graph.bull_memory.get_memories("Test query")
        print(f"✓ Successfully retrieved {len(memories)} memories")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_memory_initialization()
    if success:
        print("\n🎉 All tests passed! Memory initialization issue appears to be fixed.")
    else:
        print("\n❌ Tests failed. Memory initialization issue may still exist.")
    
    sys.exit(0 if success else 1)
