"""HTTP 基础的 Provider（绕过 Windows SSL 问题）"""

import httpx
import time
import json
from ai.base_provider import BaseAIProvider, AIResponse


class HttpProvider(BaseAIProvider):
    """直接用 httpx 发请求，绕过 OpenAI SDK 的 SSL 问题"""

    def __init__(self, api_key: str, base_url: str, model_name: str):
        super().__init__(api_key, base_url, model_name)

    async def _do_chat(self, messages, temperature=0.7, max_tokens=2000) -> AIResponse:
        start = time.time()

        # 构建请求体
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 使用 httpx，设置长超时和宽松的 SSL
        timeout = httpx.Timeout(60.0, connect=10.0)

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                latency = int((time.time() - start) * 1000)
                usage = data.get("usage", {})

                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                reasoning = msg.get("reasoning_content")
                if not content and reasoning:
                    content = reasoning
                elif reasoning and len(content) < 50:
                    content = reasoning + "\n" + content

                return AIResponse(
                    content=content,
                    model_name=self.model_name,
                    tokens_used=usage.get("total_tokens", 0),
                    latency_ms=latency,
                )
            except httpx.HTTPStatusError as e:
                raise Exception(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
            except Exception as e:
                raise Exception(f"请求失败: {type(e).__name__}: {str(e)[:100]}")
