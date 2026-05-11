"""Compatibility imports for the configured LLM agent client."""

from src.agents.llm_agent import OpenAICompatibleAgentClient, get_default_llm_client

__all__ = ["OpenAICompatibleAgentClient", "get_default_llm_client"]
