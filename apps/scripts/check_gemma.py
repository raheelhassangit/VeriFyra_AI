import asyncio
import sys

from app.config import Settings
from app.services.gemma import GemmaClient, GemmaError


async def main() -> int:
    s = Settings()
    print(f"Model: {s.ollama_model} @ {s.ollama_base_url}")
    try:
        text = await GemmaClient(s).chat([{"role": "user", "content": "Reply with exactly one word: pong"}])
    except GemmaError as e:
        print(f"FAILED: {e}")
        return 1
    print(f"OK: {text.strip()[:200]}")
    return 0


sys.exit(asyncio.run(main()))