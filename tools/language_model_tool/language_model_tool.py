"""
Simple Language Model Tool - Uses existing language model services
"""

import sys
import os
from typing import Dict, Any, Optional

# Add the parent directory to the path to import language model services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import services with error handling
try:
    from language_model_services.openai_service.openai_service import OpenAIService
except ImportError:
    OpenAIService = None

try:
    from language_model_services.groq_service.groq_service import GroqService
except ImportError:
    GroqService = None

try:
    from language_model_services.ollama_service.ollama_service import OllamaService
except ImportError:
    OllamaService = None


class LanguageModelTool:
    """
    Simple tool for using language models.
    
    This tool provides a unified interface to use different language model services
    (OpenAI, Groq, Ollama) with a simple API.
    """
    
    def __init__(self):
        """Initialize the language model tool with all available services."""
        self.services = {}
        
        # Only add services that are available
        if OpenAIService:
            try:
                self.services["openai"] = OpenAIService()
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI service: {e}")
        
        if GroqService:
            try:
                self.services["groq"] = GroqService()
            except Exception as e:
                print(f"Warning: Could not initialize Groq service: {e}")
        
        if OllamaService:
            try:
                self.services["ollama"] = OllamaService()
            except Exception as e:
                print(f"Warning: Could not initialize Ollama service: {e}")
        
        if not self.services:
            print("Warning: No language model services available. Make sure to install required packages.")
    
    def generate_response(
        self, 
        query: str, 
        service: str = "openai", 
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response using the specified language model service.
        
        Args:
            query: The prompt/query to send to the language model
            service: Which service to use ("openai", "groq", "ollama")
            model: Specific model to use (if None, uses first available model)
            system_prompt: System/base prompt to set the AI's behavior (optional)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Check if any services are available
            if not self.services:
                return {
                    "success": False,
                    "error": "No language model services available. Please install required packages (openai, groq, ollama).",
                    "response": None
                }
            
            # Validate service
            if service not in self.services:
                available_services = list(self.services.keys())
                return {
                    "success": False,
                    "error": f"Service '{service}' not available. Available services: {available_services}",
                    "response": None
                }
            
            # Get the service
            service_instance = self.services[service]
            
            # Get available models for this service
            service_info = service_instance.get_models()
            available_models = service_info["models"]
            
            # Select model
            if model is None:
                model = available_models[0]  # Use first available model
            elif model not in available_models:
                return {
                    "success": False,
                    "error": f"Model '{model}' not available for {service}. Available models: {available_models}",
                    "response": None
                }
            
            # Prepare the prompt with system message if provided
            if system_prompt:
                # Combine system prompt with user query
                full_prompt = f"System: {system_prompt}\n\nUser: {query}"
            else:
                full_prompt = query
            
            # Generate response
            response = service_instance.generate(model, full_prompt, **kwargs)
            
            return {
                "success": True,
                "response": response,
                "metadata": {
                    "service": service,
                    "model": model,
                    "query_length": len(query),
                    "response_length": len(response)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def get_available_services(self) -> Dict[str, Any]:
        """
        Get information about all available services and their models.
        
        Returns:
            Dictionary containing all services and their available models
        """
        services_info = {}
        for service_name, service_instance in self.services.items():
            services_info[service_name] = service_instance.get_models()
        return services_info
    
    def get_service_models(self, service: str) -> Dict[str, Any]:
        """
        Get available models for a specific service.
        
        Args:
            service: The service name ("openai", "groq", "ollama")
            
        Returns:
            Dictionary containing service info and available models
        """
        if service not in self.services:
            available_services = list(self.services.keys())
            return {
                "error": f"Service '{service}' not available. Available services: {available_services}"
            }
        
        return self.services[service].get_models()


# Convenience function for quick usage
def generate_with_lm(
    query: str, 
    service: str = "openai", 
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """
    Quick function to generate a response using language models.
    
    Args:
        query: The prompt/query
        service: Service to use ("openai", "groq", "ollama")
        model: Specific model (optional)
        system_prompt: System/base prompt to set AI behavior (optional)
        **kwargs: Additional parameters
        
    Returns:
        The generated response as a string, or error message if failed
    """
    tool = LanguageModelTool()
    result = tool.generate_response(query, service, model, system_prompt, **kwargs)
    
    if result["success"]:
        return result["response"]
    else:
        return f"Error: {result['error']}"
