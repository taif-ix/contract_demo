from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.engine import Engine

from app.db import get_all_documents
from app.dependencies import get_db_engine

router = APIRouter(prefix="/api", tags=["api"])