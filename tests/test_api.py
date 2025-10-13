"""
Test script for the BotCanvas API
"""

import requests
import json

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing BotCanvas API...")
    print("=" * 50)
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test nodes endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/nodes/")
        print(f"✅ Nodes endpoint: {response.status_code}")
        data = response.json()
        print(f"   Total nodes: {data['data']['total_count']}")
        print(f"   Node names: {data['data']['nodes']}")
        
        # Show first node schema as example
        if data['data']['schemas']:
            first_node = list(data['data']['schemas'].keys())[0]
            print(f"\n   Example schema for '{first_node}':")
            print(f"   {json.dumps(data['data']['schemas'][first_node], indent=4)}")
            
    except Exception as e:
        print(f"❌ Nodes endpoint failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed!")

if __name__ == "__main__":
    test_api()
