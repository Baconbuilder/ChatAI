from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "GPT Interface"

    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]  # Vite's default port

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 90

    # Database Settings
    DATABASE_URL: str
    OPENAI_API_KEY: str

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 