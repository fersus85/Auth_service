from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    SERVICE_URL: str = "http://localhost:8000"
    TEST_USER_LOGIN: str
    TEST_USER_PASSWORD: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""

    ECHO: bool = False
    ECHO_POOL: bool = False
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 10

    @computed_field
    @property
    def DB_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host="localhost",
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


test_settings = TestSettings()
