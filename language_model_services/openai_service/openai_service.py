import os
import openai
from typing import List, Dict, Any
from ..config import OPENAI_MODELS


class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.models = OPENAI_MODELS

    def generate(self, model_name: str, query: str, **kwargs) -> str:
        """Generate content using OpenAI models"""
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
            raise Exception(f"OpenAI API error: {str(e)}")

    def get_models(self) -> Dict[str, Any]:
        """Get available OpenAI models"""
        return {
            "service": "openai",
            "models": self.models
        }
