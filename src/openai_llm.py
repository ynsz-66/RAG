from typing import Any, Iterator

from openai import APIConnectionError, OpenAI

from src.ollama_llm import OllamaLLM
from src.var import VLLM_API_KEY, VLLM_LLM_MODEL, VLLM_LLM_URL, llm_backend


class OpenLLM:
    """Chat client for an OpenAI-compatible server (vLLM, Ollama ``/v1``).

    Same interface as ``OllamaLLM``: ``think`` and ``repeat_penalty`` are
    sent through ``extra_body`` (vLLM extensions, ignored by OpenAI).
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
        self.host = (host or VLLM_LLM_URL).rstrip("/")
        self.model = model or VLLM_LLM_MODEL
        self.think = think
        self.temperature = temperature
        self.repeat_penalty = repeat_penalty
        self.client = OpenAI(
            base_url=self.host, api_key=VLLM_API_KEY, timeout=self.TIMEOUT
        )

    def options(self, system: str, user: str, max_new_tokens: int
                ) -> dict[str, Any]:
        """Build the chat.completions.create keyword arguments."""
        extra: dict[str, Any] = {
            "chat_template_kwargs": {"enable_thinking": self.think}
        }
        if self.repeat_penalty is not None:
            extra["repetition_penalty"] = self.repeat_penalty
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_new_tokens,
            "extra_body": extra,
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        return kwargs

    def unreachable(self, exc: Exception) -> RuntimeError:
        """Wrap a connection error into an actionable message."""
        return RuntimeError(
            f"OpenAI-compatible server unreachable at {self.host} "
            f"(model {self.model}). Check the vLLM server / tunnel URL "
            f"(VLLM_LLM_URL) or use --llm ollama. Original error: {exc}"
        )

    def chat(
        self, system: str, user: str, max_new_tokens: int = 200
    ) -> str:
        """Blocking chat completion returning the full answer."""
        try:
            response = self.client.chat.completions.create(
                **self.options(system, user, max_new_tokens)
            )
        except APIConnectionError as exc:
            raise self.unreachable(exc) from exc
        return str(response.choices[0].message.content or "")

    def chat_stream(
        self, system: str, user: str, max_new_tokens: int = 200
    ) -> Iterator[str]:
        """Streaming chat completion yielding token deltas."""
        try:
            stream = self.client.chat.completions.create(
                stream=True, **self.options(system, user, max_new_tokens)
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APIConnectionError as exc:
            raise self.unreachable(exc) from exc


def get_llm(
    ollama_model: str | None = None, **options: Any
) -> "OpenLLM | OllamaLLM":
    """Chat client for the current backend (``--llm vllm|ollama``)."""
    if llm_backend() == "ollama":
        return OllamaLLM(model=ollama_model, **options)
    return OpenLLM(**options)
