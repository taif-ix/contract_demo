import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.engine import Engine

from app.config import Settings, get_settings
from app.db import log_upload, save_document, save_parties, save_clauses, save_risks
from app.dependencies import get_db_engine
from app.schemas import AnalysisResult, ProcessedDocument, RiskItem
from app.services import ai_contract_analysis, create_excel_report, normalize_analysis, upload_file_to_gcs
from app.utils import extract_text, is_supported
from app.utils.html_renderer import render_analysis_results

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload-contracts", response_class=HTMLResponse)
async def upload_contracts(
    files: Annotated[list[UploadFile], File(...)],
    settings: Annotated[Settings, Depends(get_settings)],
    engine: Annotated[Engine, Depends(get_db_engine)],
) -> HTMLResponse:
    processed: list[ProcessedDocument] = []

    for file in files:
        # ── Validate file type ────────────────────────────────────────────────
        if not is_supported(file.filename):
            processed.append(ProcessedDocument(
                file_name=file.filename,
                status="skipped",
                analysis=AnalysisResult(
                    risks=[RiskItem(
                        risk="Unsupported file type",
                        severity="medium",
                        reason="Supported formats: PDF, DOCX, DOC, TXT",
                    )],
                ),
            ))
            continue

        document_id = str(uuid.uuid4())
        safe_name = f"{document_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_name

        content = await file.read()
        file_path.write_bytes(content)

        # ── GCS upload ────────────────────────────────────────────────────────
        gcs_path = upload_file_to_gcs(
            file_path,
            f"{settings.gcs_folder}/{safe_name}",
            settings.gcs_bucket_name,
        )

        # ── Text extraction (PDF / DOCX / DOC / TXT) ─────────────────────────
        try:
            extracted_text = extract_text(file_path)
        except Exception as exc:
            extracted_text = ""
            print(f"Extraction error for {file.filename}: {repr(exc)}")

        if not extracted_text:
            log_upload(engine, document_id=document_id, file_name=file.filename,
                       document_type="", risk_score=None, mode="",
                       status="failed_no_text", gcs_path=gcs_path)
            processed.append(ProcessedDocument(
                document_id=document_id,
                file_name=file.filename,
                status="failed",
                gcs_path=gcs_path or "",
                analysis=AnalysisResult(
                    risks=[RiskItem(
                        risk="No text extracted",
                        severity="high",
                        reason="File may be scanned, image-based, or corrupted.",
                    )],
                ),
            ))
            continue

        # ── AI analysis ───────────────────────────────────────────────────────
        analysis = ai_contract_analysis(extracted_text, settings.groq_api_key)
        record = normalize_analysis(document_id, file.filename, extracted_text, analysis, gcs_path or "")

        # ── Save to DB ────────────────────────────────────────────────────────
        save_document(
            engine,
            document_id=document_id,
            file_name=file.filename,
            document_type=record.document_type,
            effective_date=record.effective_date,
            expiry_date=record.expiry_date,
            contract_value=record.contract_value,
            governing_law=record.governing_law,
            risk_score=record.risk_score,
            mode=record.mode,
            gcs_path=record.gcs_path,
            raw_text=record.raw_text,
        )
        save_parties(engine, document_id, record.parties)
        save_clauses(engine, document_id, record.key_clauses)
        save_risks(engine, document_id, record.risks)

        log_upload(engine, document_id=document_id, file_name=file.filename,
                   document_type=record.document_type, risk_score=record.risk_score,
                   mode=record.mode, status="processed", gcs_path=gcs_path)

        processed.append(ProcessedDocument(
            document_id=document_id,
            file_name=file.filename,
            status="processed",
            risk_score=record.risk_score,
            mode=record.mode,
            gcs_path=gcs_path or "",
            analysis=analysis,
        ))

    create_excel_report(engine)
    return render_analysis_results(processed)
