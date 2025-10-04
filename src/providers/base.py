"""Base provider module for LLM providers"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage


@dataclass
class ProviderConfig:
    """Configuration for LLM providers"""
    model_name: str
    temperature: float = 0.0
    max_tokens: int = 12000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: Optional[int] = 120
    extra_params: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._llm = None
    
    @abstractmethod
    def initialize(self) -> BaseLanguageModel:
        """Initialize and return the LangChain LLM instance"""
        pass
    
    @property
    def llm(self) -> BaseLanguageModel:
        """Get or create the LLM instance"""
        if self._llm is None:
            self._llm = self.initialize()
        return self._llm
    
    def create_messages(self, system_prompt: str, user_prompt: str) -> List[BaseMessage]:
        """Create messages for the LLM"""
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
    
    async def ainvoke(self, system_prompt: str, user_prompt: str) -> str:
        """Async invoke the LLM with given prompts"""
        import logging
        logger = logging.getLogger(__name__)

        messages = self.create_messages(system_prompt, user_prompt)
        
        try:
            response = await self.llm.ainvoke(messages)
            result = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            return result
        except Exception as e:
            logger.error(f"❌ BaseLLMProvider.ainvoke failed: {str(e)}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            raise
    
    def invoke(self, system_prompt: str, user_prompt: str) -> str:
        """Sync invoke the LLM with given prompts"""
        messages = self.create_messages(system_prompt, user_prompt)
        response = self.llm.invoke(messages)
        return response.content.strip() if hasattr(response, 'content') else str(response).strip()