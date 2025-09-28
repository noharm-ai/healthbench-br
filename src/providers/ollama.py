"""Ollama provider implementation"""

from langchain_community.llms import Ollama
from langchain_core.messages import BaseMessage
from typing import List
from .base import BaseLLMProvider, ProviderConfig


class OllamaProvider(BaseLLMProvider):
    """Provider for Ollama models"""
    
    def initialize(self):
        """Initialize Ollama LLM"""
        base_url = self.config.base_url or "http://localhost:11434"
        
        return Ollama(
            model=self.config.model_name,
            temperature=self.config.temperature,
            num_predict=self.config.max_tokens,
            base_url=base_url,
            timeout=self.config.timeout,
            **self.config.extra_params
        )
    
    async def ainvoke(self, system_prompt: str, user_prompt: str) -> str:
        """Async invoke Ollama with given prompts"""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = await self.llm.ainvoke(full_prompt)
        return response.strip() if isinstance(response, str) else str(response).strip()
    
    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        """Sync invoke Ollama with given prompts"""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.llm.invoke(full_prompt)
        return response.strip() if isinstance(response, str) else str(response).strip()