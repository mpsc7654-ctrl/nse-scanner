from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "NSE F&O Scanner"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://nse:nse123@localhost:5432/nse_scanner"
    REDIS_URL: str = "redis://localhost:6379/0"
    ANTHROPIC_API_KEY: str = ""
    NSE_BASE_URL: str = "https://www.nseindia.com"
    DATA_FETCH_INTERVAL: int = 60  # seconds
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
