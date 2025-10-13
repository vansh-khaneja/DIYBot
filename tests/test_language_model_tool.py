"""
Test script for the Language Model Tool
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools', 'language_model_tool'))

try:
    from language_model_tool import LanguageModelTool, generate_with_lm
except ImportError as e:
    print(f"[FAIL] Import Error: {e}")
    print("[TIP] Make sure to install required packages:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

def test_language_model_tool():
    """Test the language model tool functionality"""
    
    print("Testing Language Model Tool...")
    print("=" * 50)
    
    # Create tool instance
    tool = LanguageModelTool()
    
    print("\n1. Getting available services...")
    services = tool.get_available_services()
    print(f"Available services: {list(services.keys())}")
    
    for service_name, service_info in services.items():
        print(f"   - {service_name}: {len(service_info['models'])} models")
        print(f"     Models: {service_info['models']}")
    
    # Test 2: Test each service (if API keys are available)
    print("\n2. Testing service responses...")
    
    test_query = "Hello! Can you tell me a short joke?"
    
    for service_name in services.keys():
        print(f"\nTesting {service_name} service...")
        
        try:
            # Get first available model for this service
            service_models = tool.get_service_models(service_name)
            if "error" in service_models:
                print(f"   [FAIL] {service_models['error']}")
                continue
                
            first_model = service_models["models"][0]
            print(f"   Using model: {first_model}")
            
            # Generate response
            result = tool.generate_response(
                query=test_query,
                service=service_name,
                model=first_model,
                temperature=0.7,
                max_tokens=100
            )
            
            if result["success"]:
                print(f"   [OK] Success!")
                print(f"   Response: {result['response'][:100]}...")
                print(f"   Metadata: {result['metadata']}")
            else:
                print(f"   [FAIL] Error: {result['error']}")
                
        except Exception as e:
            print(f"   [FAIL] Exception: {str(e)}")
    
    # Test 3: Test system prompt functionality
    print("\n3. Testing system prompt functionality...")
    try:
        system_prompt = "You are a helpful math tutor. Always explain your answers step by step."
        result = tool.generate_response(
            query="What is 2+2?",
            service="openai",
            system_prompt=system_prompt,
            temperature=0.3
        )
        if result["success"]:
            print(f"[OK] System prompt test successful!")
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"[FAIL] System prompt test failed: {result['error']}")
    except Exception as e:
        print(f"[FAIL] System prompt test error: {str(e)}")
    
    # Test 4: Test convenience function with system prompt
    print("\n4. Testing convenience function with system prompt...")
    try:
        response = generate_with_lm(
            query="What is 2+2?",
            service="openai",
            system_prompt="You are a helpful assistant. Be concise.",
            temperature=0.3
        )
        print(f"[OK] Quick response with system prompt: {response[:100]}...")
    except Exception as e:
        print(f"[FAIL] Quick function error: {str(e)}")
    
    # Test 5: Test error handling
    print("\n5. Testing error handling...")
    
    # Invalid service
    result = tool.generate_response(
        query="test",
        service="invalid_service"
    )
    print(f"Invalid service test: {result['success']} - {result.get('error', 'No error')}")
    
    # Invalid model
    result = tool.generate_response(
        query="test",
        service="openai",
        model="invalid_model"
    )
    print(f"Invalid model test: {result['success']} - {result.get('error', 'No error')}")
    
    print("\n" + "=" * 50)
    print("Language Model Tool testing completed!")


if __name__ == "__main__":
    test_language_model_tool()
