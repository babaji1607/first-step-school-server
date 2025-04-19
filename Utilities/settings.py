# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    CLERK_FRONTEND_API: str
    CLERK_ISSUER: str
    CLERK_JWKS_URL: str
    CLERK_AUDIENCE: str

    class Config:
        env_file = ".env.local"  # change it to .env for production

settings = Settings()
