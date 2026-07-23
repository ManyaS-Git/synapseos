"""Agent Runtime configuration."""

from pydantic_settings import BaseSettings


class AgentRuntimeConfig(BaseSettings):
    """Configuration for the Agent Runtime service."""

    # TODO: Add configuration fields
    # - Agent defaults
    # - Max concurrent agents
    # - Timeout settings
    # - Model routing preferences

    model_config = {"env_prefix": "AGENT_"}


config = AgentRuntimeConfig()
