from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    KEY_STORE_PATH: str = "certs/gov_cert.p12"
    KEY_STORE_PASSWORD: str = "xxxxxx"


settings = Settings()
