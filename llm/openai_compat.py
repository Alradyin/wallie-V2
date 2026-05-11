"""OpenAI-compatible provider — covers OpenAI, Groq, and OpenRouter."""
from __future__ import annotations

import base64
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from .base import LLMError, LLMProvider


class OpenAICompatProvider(LLMProvider):
    def __init__(
        self,
        *,
        name: str,
        model: str,
        api_key: str,
        base_url: str | None = None,
        supports_vision: bool = False,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        if not api_key:
            raise LLMError(f"{name}: missing API key")
        self.name = name
        self.model = model
        self.supports_vision = supports_vision
        self._base_url = base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=extra_headers or None,
        )

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.85,
        top_p: float = 0.95,
        max_tokens: int = 500,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
    ) -> AsyncIterator[str]:
        payload = [self._encode_message(m) for m in messages]
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=payload,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                stream=True,
            )
        except Exception as e:
            raise LLMError(f"{self.name} request failed: {e}") from e

        async for event in stream:
            try:
                delta = event.choices[0].delta
                chunk = getattr(delta, "content", None)
            except (IndexError, AttributeError):
                chunk = None
            if chunk:
                yield chunk

    async def aclose(self) -> None:
        await self._client.close()

    # ----- helpers -----
    def _encode_message(self, m: dict[str, Any]) -> dict[str, Any]:
        content = m.get("content")
        if isinstance(content, list):
            blocks: list[dict[str, Any]] = []
            for b in content:
                if b.get("type") == "text":
                    blocks.append({"type": "text", "text": b.get("text", "")})
                elif b.get("type") == "image":
                    b64 = base64.b64encode(b["data"]).decode("ascii")
                    mime = b.get("mime", "image/jpeg")
                    blocks.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                                "detail": "low",
                            },
                        }
                    )
            return {"role": m["role"], "content": blocks}
        return {"role": m["role"], "content": content or ""}
