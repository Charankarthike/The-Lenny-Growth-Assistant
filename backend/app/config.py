"""
Configuration management for the Lenny Growth Assistant.
Uses pydantic-settings for environment variable loading and validation.
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Lenny Growth Assistant"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://lenny_user:lenny_password@localhost:5432/lenny_assistant"
    
    # LLM Provider
    model_provider: str = "anthropic"
    model_name: str = "claude-3-5-sonnet-20241022"
    
    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # Embeddings
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Retrieval
    top_k_results: int = 5
    similarity_threshold: float = 0.3
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Agent
    temperature: float = 0.7
    max_tokens: int = 2000
    max_context_messages: int = 10
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Data
    transcript_data_path: str = "./data/transcripts"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def get_llm_config(self) -> dict:
        """Get the configuration for the selected LLM provider."""
        if self.model_provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.model_name,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        elif self.model_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.model_name,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        else:  # ollama
            return {
                "provider": "ollama",
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
    
    def get_embedding_config(self) -> dict:
        """Get the configuration for embeddings."""
        if self.embedding_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": "text-embedding-ada-002",
                "dimension": 1536
            }
        else:  # local
            return {
                "provider": "local",
                "model": self.embedding_model,
                "dimension": self.embedding_dimension
            }


# Global settings instance
settings = Settings()
