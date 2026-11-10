from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./cloudservice.db"
    
    # JWT
    jwt_secret: str = "workerscraft-dev-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    
    # Cloudflare R2 (optional - file upload will be unavailable if not set)
    r2_endpoint: str = ''
    r2_access_key_id: str = ''
    r2_secret_access_key: str = ''
    r2_bucket_name: str = ''
    r2_public_url: str = ''
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "*"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
