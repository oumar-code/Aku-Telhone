from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "aku-telhone"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://aku:aku@localhost:5432/aku_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Service discovery
    aku_ai_url: str = "http://localhost:3001"
    aku_ighub_url: str = "http://localhost:3002"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"


settings = Settings()
