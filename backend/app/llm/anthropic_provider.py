"""
Anthropic Claude provider implementation.
"""

from typing import List, Optional, Iterator
import anthropic

from app.llm.base_provider import BaseLLMProvider, Message, CompletionResponse
from app.logging_config import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """LLM provider for Anthropic Claude models."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(model, temperature, max_tokens)
        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info("anthropic_provider_initialized", model=model)
    
    def complete(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Generate completion using Claude.
        
        Args:
            messages: Conversation messages
            temperature: Override temperature
            max_tokens: Override max tokens
            **kwargs: Additional parameters
        
        Returns:
            Completion response
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        # Separate system message from conversation
        system_message = None
        conversation_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tok,
                temperature=temp,
                system=system_message,
                messages=conversation_messages,
                **kwargs
            )
            
            content = response.content[0].text
            
            return CompletionResponse(
                content=content,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error("anthropic_completion_failed", error=str(e))
            raise
    
    def stream_complete(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream completion using Claude.
        
        Args:
            messages: Conversation messages
            temperature: Override temperature
            max_tokens: Override max tokens
            **kwargs: Additional parameters
        
        Yields:
            Text chunks
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        # Separate system message
        system_message = None
        conversation_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tok,
                temperature=temp,
                system=system_message,
                messages=conversation_messages,
                **kwargs
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error("anthropic_streaming_failed", error=str(e))
            raise
    
    def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        try:
            # Make a minimal API call
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            logger.warning("anthropic_health_check_failed", error=str(e))
            return False
