import os
from typing import Dict, Any
from ..config import OLLAMA_MODELS
import ollama


class OllamaService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.models = OLLAMA_MODELS

    def generate(self, model_name: str, query: str, **kwargs) -> str:
        """Generate content using Ollama models"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available. Available models: {self.models}")

        try:
            # Map common parameters to Ollama's parameter names
            ollama_kwargs = {}
            if 'max_tokens' in kwargs:
                ollama_kwargs['num_predict'] = kwargs['max_tokens']
            if 'temperature' in kwargs:
                ollama_kwargs['temperature'] = kwargs['temperature']
            # Add other Ollama-specific options here as needed
            
            # Merge with any remaining kwargs that don't need mapping
            for key, value in kwargs.items():
                if key not in ['max_tokens', 'temperature']:  # Already handled above
                    ollama_kwargs[key] = value
            
            response = ollama.generate(
                model=model_name,
                prompt=query,
                options=ollama_kwargs  # Pass options as a separate parameter
            )
            return response["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")

    def get_models(self) -> Dict[str, Any]:
        """Get available Ollama models"""
        return {
            "service": "ollama",
            "models": self.models
        }
