"""AWS Bedrock provider implementation"""

from langchain_aws import ChatBedrock
from .base import BaseLLMProvider, ProviderConfig
import boto3
from typing import Optional


class BedrockProvider(BaseLLMProvider):
    """Provider for AWS Bedrock models"""
    
    def __init__(self, config: ProviderConfig, 
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_session_token: Optional[str] = None,
                 aws_bearer_token: Optional[str] = None,
                 region_name: str = "us-east-1"):
        super().__init__(config)
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.aws_bearer_token = aws_bearer_token
        self.region_name = region_name
    
    def initialize(self):
        """Initialize AWS Bedrock LLM"""
        
        # Create boto3 client with credentials if provided
        client_kwargs = {
            "service_name": "bedrock-runtime",
            "region_name": self.region_name
        }
        
        # Support for bearer token authentication
        if self.aws_bearer_token:
            import requests
            from botocore.credentials import Credentials
            from botocore.session import Session
            
            # Create custom session with bearer token
            session = Session()
            session.set_credentials(
                access_key='bearer',
                secret_key=self.aws_bearer_token,
                token=self.aws_bearer_token
            )
            bedrock_client = session.create_client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
        elif self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = self.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
            if self.aws_session_token:
                client_kwargs["aws_session_token"] = self.aws_session_token
            bedrock_client = boto3.client(**client_kwargs)
        else:
            # Use default AWS credentials chain
            bedrock_client = boto3.client(**client_kwargs)
        
        # Map common model names to Bedrock model IDs
        model_mapping = {
            "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
            "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "claude-2": "anthropic.claude-v2:1",
            "claude-instant": "anthropic.claude-instant-v1",
            "llama2-70b": "meta.llama2-70b-chat-v1",
            "llama2-13b": "meta.llama2-13b-chat-v1",
            "mistral-large": "mistral.mistral-large-2402-v1:0",
            "mixtral-8x7b": "mistral.mixtral-8x7b-instruct-v0:1"
        }
        
        model_id = model_mapping.get(self.config.model_name, self.config.model_name)
        
        return ChatBedrock(
            client=bedrock_client,
            model_id=model_id,
            model_kwargs={
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                **self.config.extra_params
            }
        )