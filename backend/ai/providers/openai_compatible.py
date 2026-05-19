"""OpenAI 兼容格式的统一 Provider（DeepSeek / Qwen / GPT / MiMo 共用）"""

import time
from openai import AsyncOpenAI
from ai.base_provider import BaseAIProvider, AIResponse


class OpenAICompatibleProvider(BaseAIProvider):

    def __init__(self, api_key: str, base_url: str, model_name: str):
        super().__init__(api_key, base_url, model_name)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def _do_chat(self, messages, temperature=0.7, max_tokens=2000) -> AIResponse:
        start = time.time()
        resp = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = int((time.time() - start) * 1000)
        usage = resp.usage
        return AIResponse(
            content=resp.choices[0].message.content or "",
            model_name=self.model_name,
            tokens_used=usage.total_tokens if usage else 0,
            latency_ms=latency,
        )
