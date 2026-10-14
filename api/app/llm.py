"""Tiny provider interface so the rest of the app doesn't care which LLM
(if any) turns retrieved chunks into a final answer.

"ollama" calls a locally running model over HTTP so private documents never
leave the machine. "anthropic" calls the hosted API, which does send the
retrieved chunks (not the whole document) to Anthropic. "none" returns no
answer at all, so the app is fully usable with zero API keys.
"""
from abc import ABC, abstractmethod

import httpx

from app.config import Settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...


class NoneProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("LLM_PROVIDER=none does not generate answers")


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        from anthropic import Anthropic  # imported lazily: optional dependency path

        self._client = Anthropic(api_key=api_key)
        self._model = model

    def generate(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, base_url: str):
        self._model = model
        self._base_url = base_url

    def generate(self, prompt: str) -> str:
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]


def create_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings.ollama_model, settings.ollama_url)
    if settings.llm_provider == "none":
        return NoneProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
