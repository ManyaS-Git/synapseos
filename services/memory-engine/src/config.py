"""Memory Engine configuration.

TODO: Implement configuration loading from environment variables.
"""

from pydantic_settings import BaseSettings


class MemoryEngineConfig(BaseSettings):
    """Configuration for the Memory Engine service."""

    # TODO: Add configuration fields
    # - Database connection strings
    # - Embedding model configuration
    # - Memory consolidation parameters
    # - Importance scoring weights
    # - Decay rates

    model_config = {"env_prefix": "MEMORY_"}


config = MemoryEngineConfig()
