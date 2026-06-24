from pathlib import Path

from google.cloud import storage
from sqlalchemy.engine import Engine

from app.config import Settings
from app.db import (
    update_document_status,
    update_document_analysis,
    clear_document_details,
    save_parties,
    save_clauses,
    save_risks,
)
from app.services import ai_contract_analysis, normalize_analysis
from app.utils import extract_text


WORK_DIR = Path("worker_downloads")
WORK_DIR.mkdir(exist_ok=True)


def download_from_gcs(*, bucket_name: str, gcs_path: str, local_path: Path) -> None:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.download_to_filename(str(local_path))


def process_document_job(
    *,
    engine: Engine,
    settings: Settings,
    document_id: str,
    gcs_path: str,
    file_name: str,
) -> None:
    try:
        update_document_status(
            engine,
            document_id=document_id,
            status="processing",
        )

        safe_local_name = f"{document_id}_{Path(file_name).name}"
        local_path = WORK_DIR / safe_local_name

        download_from_gcs(
            bucket_name=settings.gcs_bucket_name,
            gcs_path=gcs_path,
            local_path=local_path,
        )

        extracted_text = extract_text(local_path)

        if not extracted_text or len(extracted_text.strip()) < 50:
            update_document_status(
                engine,
                document_id=document_id,
                status="failed",
                error_message="No text extracted from document.",
            )
            return

        analysis = ai_contract_analysis(
            extracted_text,
            settings.groq_api_key,
        )

        record = normalize_analysis(
            document_id,
            file_name,
            extracted_text,
            analysis,
            gcs_path,
        )

        clear_document_details(engine, document_id)

        update_document_analysis(
            engine,
            document_id=document_id,
            document_type=record.document_type,
            effective_date=record.effective_date,
            expiry_date=record.expiry_date,
            contract_value=record.contract_value,
            governing_law=record.governing_law,
            risk_score=record.risk_score,
            mode=record.mode,
            raw_text=record.raw_text,
        )

        save_parties(engine, document_id, record.parties)
        save_clauses(engine, document_id, record.key_clauses)
        save_risks(engine, document_id, record.risks)

    except Exception as exc:
        update_document_status(
            engine,
            document_id=document_id,
            status="failed",
            error_message=repr(exc),
        )