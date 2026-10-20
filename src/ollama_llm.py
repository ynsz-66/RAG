import json
import os
from typing import Any, Iterator

import httpx


class OllamaLLM:
    """Chat client for a local Ollama server (native ``/api/chat``).

    The native endpoint is used because only it honors ``think``.
    """

    DEFAULT_HOST = "http://localhost:11434"
    TIMEOUT = 300.0

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        think: bool = False,
    ) -> None:
        host = host or os.environ.get("OLLAMA_HOST", self.DEFAULT_HOST)
        self.host = host.rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL", "qwen3:8b")
        self.think = think
        self.client = httpx.Client(base_url=self.host, timeout=self.TIMEOUT)

    def payload(
        self, system: str, user: str, max_new_tokens: int, stream: bool
    ) -> dict[str, Any]:
        """Build the /api/chat request body."""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": stream,
            "think": self.think,
            "options": {"num_predict": max_new_tokens},
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
            response = self.client.post(
                "/api/chat",
                json=self.payload(system, user, max_new_tokens, False),
            )
        except httpx.ConnectError as exc:
            raise self.unreachable(exc) from exc
        response.raise_for_status()
        message: dict[str, Any] = response.json().get("message", {})
        return str(message.get("content", ""))

    def chat_stream(
        self, system: str, user: str, max_new_tokens: int = 200
    ) -> Iterator[str]:
        """Streaming chat completion yielding token deltas."""
        try:
            with self.client.stream(
                "POST",
                "/api/chat",
                json=self.payload(system, user, max_new_tokens, True),
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    delta = chunk.get("message", {}).get("content")
                    if delta:
                        yield delta
        except httpx.ConnectError as exc:
            raise self.unreachable(exc) from exc
