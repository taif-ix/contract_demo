import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.config import Settings
from app.dependencies import get_db_engine, get_settings


def override_settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        groq_api_key="",
        gcs_bucket_name="",
    )


def override_engine():
    return MagicMock()


app.dependency_overrides[get_settings] = override_settings
app.dependency_overrides[get_db_engine] = override_engine


@pytest.fixture
def client():
    return TestClient(app)
