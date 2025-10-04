"""Maritaca/Sabiá provider implementation using direct OpenAI client"""

from typing import List, Optional, Any, AsyncIterator, Iterator
from .base import BaseLLMProvider, ProviderConfig
import os
import asyncio
import logging
import json

# Configure logging for Maritaca provider
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# LangChain imports
try:
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.outputs.chat_generation import ChatGenerationChunk
    from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
    from langchain.chat_models.base import BaseChatModel
except ImportError:
    # Fallback imports for older versions
    from langchain.schema import BaseLanguageModel
    from langchain.schema.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
    from langchain.schema.output import ChatResult, ChatGeneration
    from langchain.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
    from langchain.chat_models.base import BaseChatModel
    # Create a dummy ChatGenerationChunk for compatibility
    class ChatGenerationChunk:
        pass

# OpenAI imports
try:
    import openai
    from openai import OpenAI
except ImportError:
    raise ImportError("Please install openai: pip install openai")


class MaritacaOpenAIWrapper(BaseChatModel):
    """Custom wrapper for Maritaca using direct OpenAI client"""
    
    client: Any  # OpenAI client instance
    model: str
    temperature: float = 0.0
    max_tokens: int = 12000
    timeout: int = 120
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 12000,
        timeout: Optional[int] = 120,
        **kwargs
    ):
        # Initialize the OpenAI client first
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout or 120,
            max_retries=2
        )
        
        # Call parent with all required fields
        super().__init__(
            client=client,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout or 120,
            **kwargs
        )
    
    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "maritaca-openai"
    
    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[dict]:
        """Convert LangChain messages to OpenAI format"""
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                # Default to user message
                openai_messages.append({"role": "user", "content": str(msg.content)})
        return openai_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion using OpenAI client"""
        
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Call OpenAI API with max_tokens (not max_completion_tokens)
        try:
            # Filter out problematic parameters
            original_kwargs = kwargs.copy()
            filtered_kwargs = {k: v for k, v in kwargs.items()
                      if k not in ['max_completion_tokens']}
            
            # Prepare API call parameters
            api_params = {
                'model': self.model,
                'messages': openai_messages,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens,
                'stop': stop,
                **filtered_kwargs
            }
            
            response = self.client.chat.completions.create(**api_params)
            
            # Extract the response content
            content = response.choices[0].message.content or ""
            
            # Create LangChain ChatGeneration
            generation = ChatGeneration(
                message=AIMessage(content=content),
                generation_info={
                    "finish_reason": response.choices[0].finish_reason,
                    "model": response.model,
                }
            )
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"❌ Maritaca API call failed: {str(e)}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Original kwargs: {original_kwargs if 'original_kwargs' in locals() else 'N/A'}")
            logger.error(f"❌ Filtered kwargs: {filtered_kwargs if 'filtered_kwargs' in locals() else 'N/A'}")
            # Handle API errors
            raise RuntimeError(f"Maritaca API call failed: {str(e)}")
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate - delegate to sync for now"""
        
        # For simplicity, we'll run the sync version in an executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate,
            messages,
            stop,
            run_manager,
            **kwargs
        )
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream is not implemented for this wrapper"""
        raise NotImplementedError("Streaming is not supported for Maritaca wrapper")
    
    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """Async stream is not implemented for this wrapper"""
        raise NotImplementedError("Async streaming is not supported for Maritaca wrapper")


class MaritacaProvider(BaseLLMProvider):
    """Provider for Maritaca/Sabiá models using direct OpenAI client"""
    
    def initialize(self) -> BaseLanguageModel:
        """Initialize Maritaca/Sabiá LLM using direct OpenAI client"""
        # Get API key - resolve environment variable if needed
        api_key = self.config.api_key
        if api_key and api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]
            api_key = os.getenv(env_var)
        
        if not api_key:
            raise ValueError("Maritaca API key is required")
        
        # Use the correct base URL from documentation
        base_url = self.config.base_url or "https://chat.maritaca.ai/api"
        
        # Map model names to Maritaca model IDs
        model_mapping = {
            "sabia-3": "sabia-3",
            "sabia-3-large": "sabia-3",  # Alias
            "sabiazinho-3": "sabiazinho-3",
            "sabia-2-small": "sabia-2-small",
            "sabia-2-medium": "sabia-2-medium",
        }
        
        model_name = model_mapping.get(self.config.model_name, self.config.model_name)
        
        # Return our custom wrapper that uses OpenAI client directly
        return MaritacaOpenAIWrapper(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout or 120  # Default timeout if None
        )