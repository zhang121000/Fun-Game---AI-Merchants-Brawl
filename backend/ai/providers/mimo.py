"""小米 MiMo Provider（小米 TokenPlan 端点）"""

from ai.providers.openai_compatible import OpenAICompatibleProvider
from ai.provider_registry import register_provider


@register_provider("mimo")
class MiMoProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(
            api_key=api_key,
            base_url="https://token-plan-cn.xiaomimimo.com/v1",
            model_name="mimo-v2.5",
        )
