"""
Configuration endpoint for retrieving system configuration.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter()


class ConfigResponse(BaseModel):
    """Response model for configuration endpoint."""
    model_provider: str
    model_name: str
    available_providers: list[str]
    embedding_model: str
    embedding_dimension: int
    features: dict[str, bool]


@router.get("", response_model=ConfigResponse)
async def get_config(settings: Settings = Depends(get_settings)):
    """
    Get current system configuration.
    
    Returns information about the active LLM provider, embedding model,
    and enabled features. Useful for frontend to adapt UI based on
    available capabilities.
    """
    llm_config = settings.get_llm_config()
    embedding_config = settings.get_embedding_config()
    
    # Determine which providers are available
    available_providers = []
    if settings.anthropic_api_key:
        available_providers.append("anthropic")
    if settings.openai_api_key:
        available_providers.append("openai")
    # Ollama is always available (assuming it's running)
    available_providers.append("ollama")
    
    return ConfigResponse(
        model_provider=llm_config["provider"],
        model_name=llm_config.get("model", "unknown"),
        available_providers=available_providers,
        embedding_model=embedding_config["model"],
        embedding_dimension=embedding_config["dimension"],
        features={
            "streaming": settings.enable_streaming,
            "artifact_generation": settings.enable_artifact_generation,
            "ship_30_for_30": True,
        }
    )
