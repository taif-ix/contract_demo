import base64
import json
import logging
import traceback

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import create_engine

from app.config import get_settings
from worker.services.processor import process_document_job

router = APIRouter(prefix="/worker", tags=["worker"])
logger = logging.getLogger(__name__)


class ProcessRequest(BaseModel):
    document_id: str
    gcs_path: str
    file_name: str


@router.get("/health")
def health():
    return {"status": "worker route running"}


@router.post("/process")
def process(payload: ProcessRequest):
    logger.info("Manual worker process requested for document_id=%s file_name=%s", payload.document_id, payload.file_name)
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
    try:
        raw_body = await request.body()
        logger.info("Pub/Sub push received. body_size=%s", len(raw_body))

        if not raw_body:
            logger.warning("Pub/Sub push ignored: empty request body")
            return {
                "status": "ignored",
                "reason": "empty request body",
            }

        body = json.loads(raw_body)
        logger.info("Pub/Sub envelope keys=%s", list(body.keys()))

        message = body.get("message", {})
        data = message.get("data")

        if not data:
            logger.warning("Pub/Sub push ignored: missing message.data. body=%s", body)
            return {
                "status": "ignored",
                "reason": "missing pubsub data",
            }

        payload = json.loads(base64.b64decode(data).decode("utf-8"))
        logger.info("Pub/Sub decoded payload=%s", payload)

        settings = get_settings()
        engine = create_engine(settings.database_url, pool_pre_ping=True)

        process_document_job(
            engine=engine,
            settings=settings,
            document_id=payload["document_id"],
            gcs_path=payload["gcs_path"],
            file_name=payload["file_name"],
        )

        logger.info("Pub/Sub document processed successfully. document_id=%s", payload["document_id"])
        return {
            "status": "ok",
            "document_id": payload["document_id"],
        }
    except Exception as exc:
        logger.error("Pub/Sub worker failed: %s", exc)
        logger.error(traceback.format_exc())
        raise
