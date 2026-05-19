from ai.providers.openai_compatible import OpenAICompatibleProvider
from ai.provider_registry import register_provider


@register_provider("gpt")
class GPTProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(
            api_key=api_key,
            base_url="https://api.freemodel.dev/v1",
            model_name="gpt-5.4",
        )
