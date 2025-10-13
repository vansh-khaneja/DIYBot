import os
from typing import Dict, Any
from ..config import GROQ_MODELS
from groq import Groq


class GroqService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.models = GROQ_MODELS

    def generate(self, model_name: str, query: str, **kwargs) -> str:
        """Generate content using Groq models"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available. Available models: {self.models}")

        try:
            response = self.client.chat.completions.create(
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
