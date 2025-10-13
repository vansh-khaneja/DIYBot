#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env file
load_dotenv()

from language_model_services.openai_service.openai_service import OpenAIService
from language_model_services.groq_service.groq_service import GroqService
from language_model_services.ollama_service.ollama_service import OllamaService

# Initialize services
openai_service = OpenAIService()
groq_service = GroqService()
ollama_service = OllamaService()

services = {
    "openai": openai_service,
    "groq": groq_service,
    "ollama": ollama_service
}

def generate_response(service_name: str, model_name: str, query: str, **kwargs) -> str:
    """
    Unified function to generate responses from any language model service.
    
    Args:
        service_name (str): Name of the service ('openai', 'groq', or 'ollama')
        model_name (str): Name of the model to use
        query (str): The prompt/query to send to the model
        **kwargs: Additional parameters (max_tokens, temperature, etc.)
    
    Returns:
        str: The generated response from the model
    
    Raises:
        ValueError: If service_name is not supported
        Exception: If there's an error with the model generation
    """
    if service_name not in services:
        available_services = list(services.keys())
        raise ValueError(f"Service '{service_name}' not supported. Available services: {available_services}")
    
    service = services[service_name]
    return service.generate(model_name, query, **kwargs)

print("=== Language Model Services Test ===")

# Show available models
print("\nAvailable Models:")
for name, service in services.items():
    try:
        models = service.get_models()
        print(f"\n{name}:")
        for model in models["models"]:
            print(f"  - {model}")
    except Exception as e:
        print(f"\n{name}: Error - {e}")

# Test the unified function
print("\n=== Testing Unified Function ===")

test_query = "Hello world in 2 sentences."

# Test examples using the unified function
test_cases = [
    ("openai", "gpt-3.5-turbo", test_query),
    ("groq", "llama-3.1-8b-instant", test_query),
    ("ollama", "phi3:mini", test_query)
]

for service_name, model_name, query in test_cases:
    print(f"\nTesting {service_name} with {model_name}...")
    try:
        response = generate_response(service_name, model_name, query, max_tokens=50)
        print(f"✓ {service_name} Success with {model_name}")
        print(f"  Response: {response}")
    except Exception as e:
        print(f"✗ {service_name} - Error: {e}")

print("\n=== Test Complete ===")
