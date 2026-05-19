"""OpenAI 兼容格式的统一 Provider（GLM / Qwen / GPT / Kimi 共用）"""

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
        msg = resp.choices[0].message
        content = msg.content or ""
        if not content:
            # 推理模型（如 GLM-5）在 max_tokens 不够时 content 为空，
            # 实际输出在 reasoning_content 中
            reasoning = getattr(msg, "reasoning_content", None)
            if reasoning:
                content = reasoning
        return AIResponse(
            content=content,
            model_name=self.model_name,
            tokens_used=usage.total_tokens if usage else 0,
            latency_ms=latency,
        )
