"""豆包 Provider（通过 EdgeFN 网关，使用 MiniMax-M2.5）"""

from ai.providers.openai_compatible import OpenAICompatibleProvider
from ai.provider_registry import register_provider


@register_provider("doubao")
class DoubaoProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(
            api_key=api_key,
            base_url="https://api.edgefn.net/v1",
            model_name="MiniMax-M2.5",
        )
