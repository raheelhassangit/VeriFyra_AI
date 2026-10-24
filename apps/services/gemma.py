import asyncio
import logging
import random
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.errors import AgentError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GemmaError(AgentError): ...
class GemmaConfigError(GemmaError): ...
class GemmaAuthError(GemmaError): ...
class GemmaRequestError(GemmaError): ...
class GemmaTransientError(GemmaError): ...
class GemmaOutputError(GemmaError): ...


def _delay(attempt, response):
    if response is not None:
        ra = response.headers.get("retry-after", "")
        if ra.isdigit():
            return min(int(ra), 30)
    return min(2 ** attempt, 30) + random.uniform(0, 0.5)


class GemmaClient:
    def __init__(self, settings: Settings, *, transport=None, sleep=asyncio.sleep):
        self._s = settings
        self._transport = transport  # tests inject httpx.MockTransport
        self._sleep = sleep

    async def chat(self, messages: list[dict], *, schema: dict | None = None) -> str:
        s = self._s
        if not s.ollama_api_key:
            raise GemmaConfigError("OLLAMA_API_KEY is not configured.")
        body = {"model": s.ollama_model, "messages": messages, "stream": False}
        if schema:
            body["format"] = schema
        url = s.ollama_base_url.rstrip("/") + "/api/chat"
        headers = {"Authorization": f"Bearer {s.ollama_api_key}"}
        attempts = s.ollama_max_retries + 1
        reason = "unknown"

        async with httpx.AsyncClient(timeout=s.ollama_timeout, transport=self._transport) as http:
            for attempt in range(attempts):
                started = time.monotonic()
                response = None
                try:
                    response = await http.post(url, json=body, headers=headers)
                    reason = f"HTTP {response.status_code}"
                except httpx.TransportError as e:
                    reason = type(e).__name__
                logger.info("gemma_call attempt=%d result=%s duration_ms=%d",
                            attempt + 1, reason, (time.monotonic() - started) * 1000)

                if response is not None:
                    code = response.status_code
                    if code == 200:
                        return self._content(response)
                    if code in (401, 403):
                        raise GemmaAuthError("Ollama rejected the API key, or the account lacks access to the model.")
                    if code == 404:
                        raise GemmaRequestError("Model or endpoint not found. Check OLLAMA_MODEL and OLLAMA_BASE_URL.")
                    if code != 429 and code < 500:
                        raise GemmaRequestError(f"Ollama rejected the request (HTTP {code}).")
                if attempt < attempts - 1:
                    await self._sleep(_delay(attempt, response))

        raise GemmaTransientError(f"Ollama unavailable after {attempts} attempts ({reason}).")

    @staticmethod
    def _content(response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            raise GemmaOutputError("Ollama returned a non-JSON response.") from None
        message = data.get("message") if isinstance(data, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise GemmaOutputError("Ollama returned an empty response.")
        return content

    async def generate_structured(self, model_cls: type[T], *, system: str, user: str) -> T:
        schema = model_cls.model_json_schema()
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        for attempt in range(2):  # one repair attempt
            text = await self.chat(messages, schema=schema)
            try:
                return model_cls.model_validate_json(text)
            except ValidationError as e:
                problems = "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()[:5])
                logger.warning("gemma_structured_invalid attempt=%d", attempt + 1)
                messages = messages + [
                    {"role": "assistant", "content": text[:2000]},
                    {"role": "user", "content": f"That reply did not match the schema. Reply again with only valid JSON. Problems: {problems}"},
                ]
        raise GemmaOutputError("Model output failed schema validation.")