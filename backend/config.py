from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_health_mall.db"

    DEEPSEEK_API_KEY: str = ""
    DOUBAO_API_KEY: str = ""
    DOUBAO_ENDPOINT_ID: str = ""
    GPT_API_KEY: str = ""
    MIMO_API_KEY: str = ""
    QWEN_API_KEY: str = ""

    # 平台AI配置（DeepSeek V4 Flash）
    PLATFORM_AI_API_KEY: str = ""
    PLATFORM_AI_BASE_URL: str = "https://api.deepseek.com"
    PLATFORM_AI_MODEL: str = "deepseek-chat"

    SIMULATION_INTERVAL_MINUTES: int = 10
    MARKETING_INTERVAL_HOURS: int = 4
    MAX_DAILY_ORDERS: int = 500
    DEFAULT_TRAFFIC_POOL: int = 5000

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
