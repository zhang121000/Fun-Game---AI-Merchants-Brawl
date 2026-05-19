import time
import json
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps


@dataclass
class AIResponse:
    content: str
    model_name: str
    tokens_used: int = 0
    latency_ms: int = 0
    parsed_data: dict | None = None


def with_retry(max_retries: int = 3, backoff_factor: float = 2.0):
    """指数退避重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff_factor ** attempt)
            raise last_err
        return wrapper
    return decorator


class BaseAIProvider(ABC):
    """所有 AI 提供商的统一接口"""

    def __init__(self, api_key: str, base_url: str | None = None, model_name: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self._semaphore = asyncio.Semaphore(2)

    @abstractmethod
    async def _do_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        ...

    @with_retry(max_retries=3, backoff_factor=2.0)
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        async with self._semaphore:
            return await self._do_chat(messages, temperature, max_tokens)

    async def generate_structured(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> dict | None:
        """调用 AI 并强制解析为 JSON，自动处理 markdown 包裹和残缺 JSON"""
        import re
        messages = [
            {"role": "system", "content": "你必须只输出合法的 JSON，不要包含任何其他文字、解释或 markdown 标记。"},
            {"role": "user", "content": prompt},
        ]
        resp = await self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        raw = resp.content.strip()

        # 1) 直接尝试解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 2) 去掉 markdown 代码块后解析
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 3) 用正则提取第一个 {...} 块（处理 AI 输出多余文字或缺括号的情况）
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                # 最后尝试补齐括号
                fragment = match.group()
                open_braces = fragment.count("{") - fragment.count("}")
                if open_braces > 0:
                    try:
                        return json.loads(fragment + "}" * open_braces)
                    except json.JSONDecodeError:
                        pass

        resp.parsed_data = None
        return None
