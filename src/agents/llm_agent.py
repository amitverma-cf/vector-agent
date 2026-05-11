"""Pydantic AI wrapper for OpenAI-compatible structured model calls."""

from __future__ import annotations

import os
import json
from typing import Any, TypeVar

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential


T = TypeVar("T", bound=BaseModel)


def _create_retrying_http_client(timeout_seconds: float) -> httpx.AsyncClient:
    def validate_response(response: httpx.Response) -> None:
        if response.status_code in (429, 500, 502, 503, 504):
            response.raise_for_status()

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(
                (
                    httpx.HTTPStatusError,
                    httpx.TimeoutException,
                    httpx.ConnectError,
                    httpx.ReadError,
                )
            ),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=1, max=30),
                max_wait=120,
            ),
            stop=stop_after_attempt(4),
            reraise=True,
        ),
        validate_response=validate_response,
    )
    return httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(timeout_seconds),
    )


class OpenAICompatibleAgentClient:
    """Small structured-output client backed by Pydantic AI agents."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 120,
        output_retries: int = 2,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self.timeout_seconds = timeout_seconds
        self.output_retries = output_retries
        self._http_client = _create_retrying_http_client(timeout_seconds)
        self._model = OpenAIChatModel(
            model,
            provider=OpenAIProvider(
                base_url=self.base_url,
                api_key=api_key,
                http_client=self._http_client,
            ),
        )

    @classmethod
    def from_env(cls) -> "OpenAICompatibleAgentClient | None":
        load_dotenv()

        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        return cls(
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            model=os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini",
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
            output_retries=int(os.getenv("LLM_OUTPUT_RETRIES", "2")),
        )

    def generate_model(
        self,
        instructions: str,
        prompt: str,
        output_type: type[T],
        output_retries: int | None = None,
    ) -> T:
        agent = Agent(
            self._model,
            instructions=instructions,
            output_type=output_type,
            retries=self.output_retries if output_retries is None else output_retries,
        )
        result = agent.run_sync(prompt)
        return result.output

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        agent = Agent(
            self._model,
            instructions=system_prompt,
            output_type=dict[str, Any],
            retries=self.output_retries,
        )
        result = agent.run_sync(user_prompt)
        return result.output

    def generate_json_text(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        agent = Agent(
            self._model,
            instructions=f"{system_prompt}\nReturn only one valid JSON object. No markdown.",
            output_type=str,
            retries=0,
        )
        result = agent.run_sync(user_prompt)
        return _extract_json_object(result.output)


def get_default_llm_client() -> OpenAICompatibleAgentClient | None:
    return OpenAICompatibleAgentClient.from_env()


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        start = text.find("{")
        if start == -1:
            raise
        obj, _ = decoder.raw_decode(text[start:])
        if not isinstance(obj, dict):
            raise ValueError("Expected a JSON object")
        return obj
