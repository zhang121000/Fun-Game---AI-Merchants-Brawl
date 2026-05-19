from ai.base_provider import BaseAIProvider

_registry: dict[str, type[BaseAIProvider]] = {}


def register_provider(model_key: str):
    """注册 AI 提供商的装饰器"""
    def decorator(cls):
        _registry[model_key] = cls
        return cls
    return decorator


def get_provider(model_key: str, api_key: str, **kwargs) -> BaseAIProvider:
    cls = _registry.get(model_key)
    if cls is None:
        raise ValueError(f"未知的 AI 提供商: {model_key}")
    return cls(api_key=api_key, **kwargs)


def list_providers() -> list[str]:
    return list(_registry.keys())
