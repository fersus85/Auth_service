import os

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from models.user import Role


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    PROJECT_NAME: str = "AuthService"
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""

    ECHO: bool = False
    ECHO_POOL: bool = False
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 10

    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379

    JWT_TOKEN_SECRET_KEY: str
    JWT_TOKEN_ALGORITHM: str = "HS256"
    JWT_TOKEN_EXPIRE_TIME_M: int = 15

    REQUEST_LIMIT_PER_SECOND: int = 10

    @computed_field
    @property
    def DB_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @property
    def DEFAULT_ROLES(self):
        return [
            Role(name="superuser", description="Может всё"),
            Role(name="admin", description="Администратор"),
            Role(name="subscriber", description="Пользователь с допами"),
            Role(name="user", description="Зарегестрированный пользователь"),
        ]


settings = Settings()
