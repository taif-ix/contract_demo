from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    database_url: str
    groq_api_key: str = ""

    gcs_project_id: str = ""
    gcs_bucket_name: str = ""
    gcs_folder: str = "contracts"

    pubsub_project_id: str = ""
    pubsub_topic_id: str = "document-processing"


@lru_cache
def get_settings() -> Settings:
    return Settings()