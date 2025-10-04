"""Factory for creating LLM providers"""

from typing import Optional
from .base import BaseLLMProvider, ProviderConfig
from .maritaca import MaritacaProvider
from .openai_provider import OpenAIProvider
from .ollama import OllamaProvider
from .bedrock import BedrockProvider


class ProviderFactory:
    """Factory for creating LLM provider instances"""
    
    @staticmethod
    def create_from_config(provider_config) -> BaseLLMProvider:
        """Create a provider instance from configuration"""
        
        # Create base provider config
        base_config = ProviderConfig(
            model_name=provider_config.model,
            temperature=provider_config.temperature,
            max_tokens=provider_config.max_tokens,
            api_key=provider_config.api_key,
            base_url=provider_config.base_url,
            timeout=provider_config.timeout,
            extra_params=provider_config.extra_params
        )
        
        # Create provider based on type
        if provider_config.type == "maritaca":
            return MaritacaProvider(base_config)
        
        elif provider_config.type == "openai":
            return OpenAIProvider(base_config)
        
        elif provider_config.type == "ollama":
            return OllamaProvider(base_config)
        
        elif provider_config.type == "aws_bedrock":
            # Bedrock needs special handling for AWS credentials
            return BedrockProvider(
                config=base_config,
                aws_bearer_token=provider_config.aws_bearer_token,
                region_name=provider_config.region
            )
        
        else:
            raise ValueError(f"Unknown provider type: {provider_config.type}")
    
    @staticmethod
    def create(
        provider_type: str,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 12000,
        timeout: int = 120,
        **kwargs
    ) -> BaseLLMProvider:
        """Create a provider instance with direct parameters"""
        
        config = ProviderConfig(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        
        if provider_type == "maritaca":
            return MaritacaProvider(config)
        elif provider_type == "openai":
            return OpenAIProvider(config)
        elif provider_type == "ollama":
            return OllamaProvider(config)
        elif provider_type == "aws_bedrock":
            return BedrockProvider(
                config=config,
                aws_bearer_token=kwargs.get('aws_bearer_token'),
                aws_access_key_id=kwargs.get('aws_access_key_id'),
                aws_secret_access_key=kwargs.get('aws_secret_access_key'),
                aws_session_token=kwargs.get('aws_session_token'),
                region_name=kwargs.get('region_name', 'us-east-1')
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")