"""
Ollama local LLM provider implementation.
"""

from typing import List, Optional, Iterator
import ollama

from app.llm.base_provider import BaseLLMProvider, Message, CompletionResponse
from app.logging_config import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """LLM provider for local Ollama models."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize Ollama provider.
        
        Args:
            base_url: Ollama server URL
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(model, temperature, max_tokens)
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
        logger.info("ollama_provider_initialized", model=model, base_url=base_url)
    
    def complete(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Generate completion using Ollama.
        
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
        
        # Format messages for Ollama
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=ollama_messages,
                options={
                    "temperature": temp,
                    "num_predict": max_tok,
                },
                **kwargs
            )
            
            content = response['message']['content']
            
            # Extract usage if available
            usage = None
            if 'prompt_eval_count' in response:
                usage = {
                    "input_tokens": response.get('prompt_eval_count', 0),
                    "output_tokens": response.get('eval_count', 0)
                }
            
            return CompletionResponse(
                content=content,
                model=response.get('model', self.model),
                usage=usage,
                finish_reason=response.get('done_reason'),
                metadata={
                    "total_duration": response.get('total_duration'),
                    "load_duration": response.get('load_duration')
                }
            )
            
        except Exception as e:
            logger.error("ollama_completion_failed", error=str(e))
            raise
    
    def stream_complete(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream completion using Ollama.
        
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
        
        # Format messages for Ollama
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            stream = self.client.chat(
                model=self.model,
                messages=ollama_messages,
                options={
                    "temperature": temp,
                    "num_predict": max_tok,
                },
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    
        except Exception as e:
            logger.error("ollama_streaming_failed", error=str(e))
            raise
    
    def health_check(self) -> bool:
        """Check if Ollama server is accessible."""
        try:
            # Try to list models
            self.client.list()
            return True
        except Exception as e:
            logger.warning("ollama_health_check_failed", error=str(e))
            return False
