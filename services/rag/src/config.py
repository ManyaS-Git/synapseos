"""RAG Pipeline configuration."""

from pydantic_settings import BaseSettings


class RAGConfig(BaseSettings):
    """Configuration for the RAG Pipeline service."""

    # TODO: Add configuration fields
    # - Retrieval parameters
    # - Chunk size and overlap
    # - Top-k results
    # - Re-ranking model
    # - Context window limits

    model_config = {"env_prefix": "RAG_"}


config = RAGConfig()
