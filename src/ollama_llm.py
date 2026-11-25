from typing import Any, Iterator

import httpx
import ollama

from src.var import OLLAMA_LLM_MODEL, OLLAMA_LLM_URL

UNREACHABLE = (ConnectionError, httpx.ConnectError)


class OllamaLLM:
    """Chat client for an Ollama server (``ollama`` lib, native ``/api/chat``).

    The native endpoint is used because only it honors ``think``.
    """

    TIMEOUT = 300.0

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        think: bool = False,
        temperature: float | None = None,
        repeat_penalty: float | None = None,
    ) -> None:
        self.host = (host or OLLAMA_LLM_URL).rstrip("/")
        self.model = model or OLLAMA_LLM_MODEL
        self.think = think
        self.options: dict[str, Any] = {
            key: value
            for key, value in (
                ("temperature", temperature),
                ("repeat_penalty", repeat_penalty),
            )
            if value is not None
        }
        self.client = ollama.Client(host=self.host, timeout=self.TIMEOUT)

    def request(
        self, system: str, user: str, max_new_tokens: int
    ) -> dict[str, Any]:
        """Build the keyword arguments for ``ollama.Client.chat``."""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "think": self.think,
            "options": {**self.options, "num_predict": max_new_tokens},
        }

    def unreachable(self, exc: Exception) -> RuntimeError:
        """Wrap a connection error into an actionable message."""
        return RuntimeError(
            f"Ollama unreachable at {self.host}. "
            f"Start it with 'ollama serve', then pull the model with "
            f"'ollama pull {self.model}'. Original error: {exc}"
        )

    def chat(
        self, system: str, user: str, max_new_tokens: int = 200
    ) -> str:
        """Blocking chat completion returning the full answer."""
        try:
            response = self.client.chat(
                **self.request(system, user, max_new_tokens)
            )
        except UNREACHABLE as exc:
            raise self.unreachable(exc) from exc
        return response.message.content or ""

    def chat_stream(
        self, system: str, user: str, max_new_tokens: int = 200
    ) -> Iterator[str]:
        """Streaming chat completion yielding token deltas."""
        try:
            for chunk in self.client.chat(
                **self.request(system, user, max_new_tokens), stream=True
            ):
                if chunk.message.content:
                    yield chunk.message.content
        except UNREACHABLE as exc:
            raise self.unreachable(exc) from exc
