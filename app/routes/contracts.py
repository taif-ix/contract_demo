import uuid
from pathlib import Path
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine

from app.config import Settings, get_settings
from app.dependencies import get_db_engine
from app.services import upload_file_to_gcs
from app.services.pubsub import publish_document_job
from app.utils import is_supported
from app.db import (
    create_queued_document,
    get_all_documents,
    get_document_clauses,
    get_document_risks,
    get_document_parties,
)

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload-contracts")
async def upload_contracts(
    files: List[UploadFile] = File(...),
    settings: Settings = Depends(get_settings),
    engine: Engine = Depends(get_db_engine),
):
    queued = []

    for file in files:
        if not is_supported(file.filename):
            queued.append({
                "file_name": file.filename,
                "status": "skipped",
                "reason": "Unsupported file type. Supported formats: PDF, DOCX, DOC, TXT",
            })
            continue

        document_id = str(uuid.uuid4())
        original_name = Path(file.filename).name
        safe_name = f"{document_id}_{original_name}"
        file_path = UPLOAD_DIR / safe_name

        content = await file.read()
        file_path.write_bytes(content)

        gcs_path = upload_file_to_gcs(
            file_path,
            f"{settings.gcs_folder}/{safe_name}",
            settings.gcs_bucket_name,
        )

        create_queued_document(
            engine,
            document_id=document_id,
            file_name=original_name,
            gcs_path=gcs_path,
        )

        message_id = publish_document_job(
            project_id=settings.pubsub_project_id or settings.gcs_project_id,
            topic_id=settings.pubsub_topic_id,
            document_id=document_id,
            gcs_path=gcs_path,
            file_name=original_name,
        )

        queued.append({
            "document_id": document_id,
            "file_name": original_name,
            "status": "queued",
            "gcs_path": gcs_path,
            "message_id": message_id,
        })

    return JSONResponse({
        "message": f"Queued {len(queued)} document(s)",
        "documents": queued,
    })

@router.get("/api/contracts")
async def get_contracts(
    engine: Annotated[Engine, Depends(get_db_engine)],
):
    rows = get_all_documents(engine)
    contracts = []

    for row in rows:
        risk_score = row.risk_score or 0
        db_status = (row.status or "").lower()

        if db_status == "queued":
            status = "Processing"
        elif db_status == "processing":
            status = "Processing"
        elif db_status == "failed":
            status = "Failed"
        elif risk_score >= 70:
            status = "High Risk"
        else:
            status = "Completed"

        clauses = get_document_clauses(engine, row.document_id)
        risks = get_document_risks(engine, row.document_id)
        parties = get_document_parties(engine, row.document_id)

        clause_items = []

        for index, clause in enumerate(clauses):
            clause_items.append({
                "id": f"{row.document_id}-clause-{index}",
                "title": clause.clause_type or "Clause",
                "text": clause.clause_text or "",
                "riskLevel": "Low",
                "explanation": "",
                "recommendation": "",
            })

        for index, risk in enumerate(risks):
            severity = (risk.severity or "medium").lower()
            risk_level = "High" if severity == "high" else "Medium" if severity == "medium" else "Low"

            clause_items.append({
                "id": f"{row.document_id}-risk-{index}",
                "title": risk.risk or "Risk",
                "text": risk.reason or "",
                "riskLevel": risk_level,
                "explanation": risk.reason or "",
                "recommendation": "",
            })

        warnings = sum(1 for item in clause_items if item["riskLevel"] == "High")

        contracts.append({
            "id": row.document_id,
            "fileName": row.file_name,
            "fileSize": "",
            "fileType": row.file_name.split(".")[-1].lower(),
            "uploadedAt": str(row.uploaded_at),
            "status": status,
            "riskScore": risk_score,
            "contractType": row.document_type or "Contract",
            "parties": [p.party_name for p in parties],
            "effectiveDate": row.effective_date or "",
            "duration": row.expiry_date or "",
            "summary": row.error_message or "",
            "clauses": clause_items,
            "warnings": warnings,
            "gcsPath": row.gcs_path,
        })

    return contracts