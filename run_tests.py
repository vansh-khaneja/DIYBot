"""
Test Runner - Run all tests from the tests directory
"""

import subprocess
import sys
import os

def run_test(test_file):
    """Run a single test file"""
    print(f"\nRunning {test_file}...")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              cwd=os.path.join(os.path.dirname(__file__), 'tests'),
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Test passed!")
        else:
            print("❌ Test failed!")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running test: {e}")

def main():
    """Run all tests"""
    print("DIYBot Test Suite")
    print("=" * 50)
    
    test_files = [
        "test_node_registry.py",
        "test_language_model_tool.py", 
        "test_language_model_node.py",
        "test_all_refactored_nodes.py"
        # Skip test_language_model_Service.py due to missing groq dependency
    ]
    
    for test_file in test_files:
        run_test(test_file)
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main()
