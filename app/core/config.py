import os
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "CargaExpress API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Base de Datos
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cargaexpress"

    # Seguridad JWT
    SECRET_KEY: str = "ce_dev_secret_key_9f8b2c1a4e6d3f5a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TEMP_TOKEN_EXPIRE_MINUTES: int = 5

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Protección de Autenticación
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    # Notificaciones por Correo Electrónico Real (Gmail SMTP / STARTTLS)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: str = "CargaExpress Perú"
    SMTP_FROM_EMAIL: Optional[str] = None
    EMAIL_ENABLED: bool = True

    # Mailtrap & Notificaciones por Correo (Sandbox Fallback)
    MAILTRAP_API_TOKEN: str = ""
    MAILTRAP_INBOX_ID: int = 4950980
    FRONTEND_URL: str = "http://localhost:5173"
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Webhook
    WEBHOOK_SECRET_KEY: str = "whsec_simulated_dev_key_2026"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
