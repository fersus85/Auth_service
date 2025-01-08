import os
from enum import Enum, auto
from typing import Any, Dict

from pydantic import Field, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from models.user import Role


class StrEnum(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class UserRoleDefault(StrEnum):
    SUPERUSER = auto()
    ADMIN = auto()
    SUBSCRIBER = auto()
    USER = auto()


class EnvMode(StrEnum):
    PROD = auto()
    TEST = auto()


class JaegerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="JGR_",
    )
    HOST: str = "jaeger"
    PORT: str = "4317"


class BaseOauthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    CLIENT_ID: str
    CLIENT_SECRET: str
    CODE_URL: str
    TOKEN_URL: str
    INFO_URL: str


class YndxOauthSettings(BaseOauthSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="YNDX_",
    )


class VKOauthSettings(BaseOauthSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="VK_",
    )


class GoogleOauthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    GOOGLE_CLIENT_ID: str
    GOOGLE_PROJECT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_AUTH_URL: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_REDIRECT_URL: str

    @staticmethod
    def get_client_config() -> Dict[str, Any]:
        params = {
            "web": {
                "client_id": settings.google_oauth.GOOGLE_CLIENT_ID,
                "project_id": settings.google_oauth.GOOGLE_PROJECT_ID,
                "auth_uri": settings.google_oauth.GOOGLE_AUTH_URL,
                "token_uri": settings.google_oauth.GOOGLE_TOKEN_URL,
                "client_secret": settings.google_oauth.GOOGLE_CLIENT_SECRET,
                "response_type": "code",
            }
        }

        return {
            "client_config": params,
            "redirect_uri": settings.google_oauth.GOOGLE_REDIRECT_URL,
            "scopes": [
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    PROJECT_NAME: str = "AuthService"
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ENV: str = EnvMode.PROD

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

    jaeger: JaegerSettings = Field(default_factory=JaegerSettings)

    yndx_oauth: YndxOauthSettings = Field(default_factory=YndxOauthSettings)
    vk_oauth: VKOauthSettings = Field(default_factory=VKOauthSettings)
    google_oauth: GoogleOauthSettings = Field(
        default_factory=GoogleOauthSettings
    )

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
            Role(name=UserRoleDefault.SUPERUSER, description="Может всё"),
            Role(name=UserRoleDefault.ADMIN, description="Администратор"),
            Role(
                name=UserRoleDefault.SUBSCRIBER,
                description="Пользователь с допами",
            ),
            Role(
                name=UserRoleDefault.USER,
                description="Зарегестрированный пользователь",
            ),
        ]


settings = Settings()
