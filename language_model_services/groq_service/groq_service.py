import os
from typing import Dict, Any
from ..config import GROQ_MODELS
from groq import Groq


class GroqService:
    def __init__(self):
        self.models = GROQ_MODELS
        self._client = None
        self._api_key = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize or reinitialize the Groq client with current API key"""
        current_api_key = os.getenv("GROQ_API_KEY")
        if current_api_key != self._api_key:
            self._api_key = current_api_key
            if self._api_key:
                self._client = Groq(api_key=self._api_key)
            else:
                self._client = None

    def generate(self, model_name: str, query: str, **kwargs) -> str:
        """Generate content using Groq models"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available. Available models: {self.models}")

        # Reinitialize client if API key has changed
        self._initialize_client()
        
        if not self._client:
            raise Exception("Groq API key not found. Please set GROQ_API_KEY environment variable.")

        try:
            response = self._client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": query}],
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")

    def get_models(self) -> Dict[str, Any]:
        """Get available Groq models"""
        return {
            "service": "groq",
            "models": self.models
        }
