"""AWS Bedrock provider implementation"""

from langchain_aws import ChatBedrock
from .base import BaseLLMProvider, ProviderConfig
import os
from typing import Optional


class BedrockProvider(BaseLLMProvider):
    """Provider for AWS Bedrock models"""
    
    def __init__(self, config: ProviderConfig, 
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_session_token: Optional[str] = None,
                 aws_bearer_token: Optional[str] = None,
                 credentials_profile_name: Optional[str] = None,
                 region_name: str = "us-east-1"):
        super().__init__(config)
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.aws_bearer_token = aws_bearer_token
        self.credentials_profile_name = credentials_profile_name
        self.region_name = region_name
    
    def initialize(self):
        """Initialize AWS Bedrock LLM following the validated pattern"""
        
        # Prepare kwargs for ChatBedrock
        bedrock_kwargs = {
            "model_id": self.config.model_name,
            "region_name": self.region_name,
            "temperature": self.config.temperature,
            "model_kwargs": {
                "max_tokens": self.config.max_tokens,
                **self.config.extra_params
            }
        }
        
        # Handle credentials profile name if provided
        if self.credentials_profile_name:
            bedrock_kwargs["credentials_profile_name"] = self.credentials_profile_name
        
        # Handle bearer token - set environment variable if provided
        if self.aws_bearer_token:
            # Resolve environment variable if it's in ${VAR} format
            if self.aws_bearer_token.startswith('${') and self.aws_bearer_token.endswith('}'):
                env_var = self.aws_bearer_token[2:-1]
                token_value = os.getenv(env_var)
                if token_value:
                    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token_value
            else:
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = self.aws_bearer_token
        
        # Return ChatBedrock with proper configuration
        # ChatBedrock will handle credentials automatically via boto3's credential chain
        return ChatBedrock(**bedrock_kwargs)