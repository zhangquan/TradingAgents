#!/usr/bin/env python3
"""
Test script to verify the module split is working correctly.
"""

def test_imports():
    """Test that all modules can be imported correctly."""
    print("Testing module imports...")
    
    try:
        # Test importing individual modules
        from backend.services.agent.config_handler import ConfigHandler
        print("✓ ConfigHandler imported successfully")
        
        from backend.services.agent.memory_tracker import MemoryTracker  
        print("✓ MemoryTracker imported successfully")
        
        from backend.services.agent.analysis_executor import AnalysisExecutor
        print("✓ AnalysisExecutor imported successfully")
        
        # Test importing from package
        from backend.services.agent import ConfigHandler, MemoryTracker, AnalysisExecutor
        print("✓ Package imports working")
        
        # Test main service
        from backend.services.agent_runner_service import AnalysisRunnerService, analysis_runner_service
        print("✓ Main service imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_instantiation():
    """Test that classes can be instantiated."""
    print("\nTesting class instantiation...")
    
    try:
        from backend.services.agent.config_handler import ConfigHandler
        from backend.services.agent.memory_tracker import MemoryTracker
        from backend.services.agent.analysis_executor import AnalysisExecutor
        from backend.services.agent_runner_service import AnalysisRunnerService
        
        # Test instantiation
        config_handler = ConfigHandler()
        print("✓ ConfigHandler instantiated")
        
        memory_tracker = MemoryTracker()
        print("✓ MemoryTracker instantiated")
        
        analysis_executor = AnalysisExecutor()
        print("✓ AnalysisExecutor instantiated")
        
        analysis_runner = AnalysisRunnerService()
        print("✓ AnalysisRunnerService instantiated")
        
        print("\n🎉 All classes instantiated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        return False

def test_method_delegation():
    """Test that method delegation works in the main service."""
    print("\nTesting method delegation...")
    
    try:
        from backend.services.agent_runner_service import analysis_runner_service
        
        # Test that the main service has the required methods
        assert hasattr(analysis_runner_service, 'run_sync_analysis')
        print("✓ run_sync_analysis method exists")
        
        assert hasattr(analysis_runner_service, 'run_sync_analysis_with_memory')
        print("✓ run_sync_analysis_with_memory method exists")
        
        assert hasattr(analysis_runner_service, 'get_conversation_session')
        print("✓ get_conversation_session method exists")
        
        assert hasattr(analysis_runner_service, 'list_user_conversations')
        print("✓ list_user_conversations method exists")
        
        print("\n🎉 All method delegation working!")
        return True
        
    except Exception as e:
        print(f"❌ Method delegation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing TradingAgents module split")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_instantiation()
    success &= test_method_delegation()
    
    if success:
        print("\n🎊 All tests passed! Module split is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the module split.")
    
    return success

if __name__ == "__main__":
    main()
