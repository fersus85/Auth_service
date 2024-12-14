from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    SERVICE_URL: str = "http://localhost:8100"
    TEST_USER_LOGIN: str
    TEST_USER_PASSWORD: str


test_settings = TestSettings()
