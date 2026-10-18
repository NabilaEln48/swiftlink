"""Application settings, loaded from environment variables.

Why pydantic-settings instead of bare os.getenv?
  - One typed, validated place for every knob the app reads.
  - Fails fast at startup with a clear error if a value is malformed,
    instead of blowing up mid-request with a cryptic TypeError.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Redis connection — override with REDIS_URL in production.
    redis_url: str = "redis://localhost:6379/0"

    # Public base URL used to build the returned short links, e.g.
    # "https://sho.rt" -> "https://sho.rt/Ab3". Trailing slash is stripped.
    base_url: str = "http://localhost:8000"

    # Rate limit: max shorten requests per IP per window.
    rate_limit_max_requests: int = 10
    rate_limit_window_seconds: int = 60


settings = Settings()
