"""
Factory for creating LLM providers based on configuration.
"""

from typing import Optional

from app.llm.base_provider import BaseLLMProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.ollama_provider import OllamaProvider
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider based on configuration.
        
        Args:
            provider_name: Provider to use (default from settings)
            model: Model to use (default from settings)
            temperature: Sampling temperature (default from settings)
            max_tokens: Max tokens (default from settings)
        
        Returns:
            Initialized LLM provider
        
        Raises:
            ValueError: If provider is not supported or configuration is invalid
        """
        provider = provider_name or settings.llm_provider
        temp = temperature if temperature is not None else settings.agent_temperature
        max_tok = max_tokens if max_tokens is not None else settings.agent_max_tokens
        
        logger.info(
            "creating_llm_provider",
            provider=provider,
            model=model,
            temperature=temp
        )
        
        if provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            
            model_name = model or settings.anthropic_model
            return AnthropicProvider(
                api_key=settings.anthropic_api_key,
                model=model_name,
                temperature=temp,
                max_tokens=max_tok
            )
        
        elif provider == "ollama":
            model_name = model or settings.ollama_model
            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model=model_name,
                temperature=temp,
                max_tokens=max_tok
            )
        
        elif provider == "openai":
            # Note: OpenAI provider not yet implemented
            # Would follow same pattern as Anthropic
            raise NotImplementedError("OpenAI provider not yet implemented")
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """
        Get list of available providers based on configuration.
        
        Returns:
            List of provider names that can be used
        """
        available = []
        
        if settings.anthropic_api_key:
            available.append("anthropic")
        
        # Ollama is always available (assumed to be running)
        available.append("ollama")
        
        if settings.openai_api_key:
            available.append("openai")
        
        return available


# Global provider instance (lazy loaded)
_provider: Optional[BaseLLMProvider] = None


def get_llm_provider(force_recreate: bool = False) -> BaseLLMProvider:
    """
    Get or create the global LLM provider instance.
    
    Args:
        force_recreate: Force creation of a new provider
    
    Returns:
        LLM provider instance
    """
    global _provider
    
    if _provider is None or force_recreate:
        _provider = LLMProviderFactory.create_provider()
    
    return _provider
