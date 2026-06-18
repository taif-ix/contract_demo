from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import Settings, get_settings


@lru_cache
def _make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def get_db_engine(settings: Annotated[Settings, Depends(get_settings)]) -> Engine:
    return _make_engine(settings.database_url)
