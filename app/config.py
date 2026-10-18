from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"

    base_url: str = "http://localhost:8000"

    rate_limit_max_requests: int = 10
    rate_limit_window_seconds: int = 60

settings = Settings()
