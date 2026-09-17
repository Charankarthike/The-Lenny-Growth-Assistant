"""
Application configuration using pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    app_name: str = "Lenny Growth Assistant API"
    environment: str = "production"
    port: int = 8000
    
    # Database
    database_url: str
    
    # OpenAI
    openai_api_key: str
    
    # Models
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    
    # RAG
    top_k_results: int = 5
    
    # CORS
    cors_origins: str = "*"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
