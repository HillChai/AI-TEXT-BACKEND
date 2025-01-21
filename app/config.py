from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    API_URL: str
    API_KEY: str = "your_secret_key"
    jwt_secret_key: str
    jwt_expiration_minutes: int = 30
    jwt_algorithm: str
    max_devices: int = 3
    redis_url: str
    
    class Config:
        env_file = ".env"

settings = Settings()
