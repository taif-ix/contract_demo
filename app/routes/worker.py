import base64
import json

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import create_engine

from app.config import get_settings
from worker.services.processor import process_document_job

router = APIRouter(prefix="/worker", tags=["worker"])


class ProcessRequest(BaseModel):
    document_id: str
    gcs_path: str
    file_name: str


@router.get("/health")
def health():
    return {"status": "worker route running"}


@router.post("/process")
def process(payload: ProcessRequest):
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    process_document_job(
        engine=engine,
        settings=settings,
        document_id=payload.document_id,
        gcs_path=payload.gcs_path,
        file_name=payload.file_name,
    )

    return {
        "status": "ok",
        "document_id": payload.document_id,
    }


@router.post("/pubsub")
async def pubsub_push(request: Request):
    raw_body = await request.body()

    if not raw_body:
        return {
            "status": "ignored",
            "reason": "empty request body",
        }

    body = json.loads(raw_body)
    message = body.get("message", {})
    data = message.get("data")

    if not data:
        return {
            "status": "ignored",
            "reason": "missing pubsub data",
        }

    payload = json.loads(base64.b64decode(data).decode("utf-8"))

    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    process_document_job(
        engine=engine,
        settings=settings,
        document_id=payload["document_id"],
        gcs_path=payload["gcs_path"],
        file_name=payload["file_name"],
    )

    return {
        "status": "ok",
        "document_id": payload["document_id"],
    }
