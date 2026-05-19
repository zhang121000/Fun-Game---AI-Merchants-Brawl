from ai.providers.openai_compatible import OpenAICompatibleProvider
from ai.provider_registry import register_provider


@register_provider("GLM")
class GLMProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(
            api_key=api_key,
            base_url="https://api.edgefn.net/v1",
            model_name="GLM-5",
        )
