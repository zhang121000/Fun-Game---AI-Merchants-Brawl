"""Kimi Provider（小米 TokenPlan 端点）"""

from ai.providers.openai_compatible import OpenAICompatibleProvider
from ai.provider_registry import register_provider
from config import get_settings


@register_provider("Kimi")
class KimiProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, **kwargs):
        settings = get_settings()
        super().__init__(
            api_key=api_key or settings.EDGEFN_API_KEY,
            base_url=kwargs.get("base_url") or settings.EDGEFN_BASE_URL,
            model_name=kwargs.get("model_name") or "Kimi-K2-Instruct",
        )
