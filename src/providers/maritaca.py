"""Maritaca/Sabiá provider implementation"""

from langchain_openai import ChatOpenAI
from .base import BaseLLMProvider, ProviderConfig


class MaritacaProvider(BaseLLMProvider):
    """Provider for Maritaca/Sabiá models"""
    
    def initialize(self):
        """Initialize Maritaca/Sabiá LLM using OpenAI-compatible endpoint"""
        if not self.config.api_key:
            raise ValueError("Maritaca API key is required")
        
        base_url = self.config.base_url or "https://api.maritaca.ai/v1"
        
        return ChatOpenAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=self.config.api_key,
            base_url=base_url,
            timeout=self.config.timeout,
            **self.config.extra_params
        )