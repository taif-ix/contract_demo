import uuid
from pathlib import Path
from typing import Annotated
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, File, UploadFile
from app.db import get_all_documents
# from fastapi.responses import HTMLResponse
# from app.utils.html_renderer import render_analysis_results
# from pathlib import Path
from sqlalchemy.engine import Engine
from typing import List
from app.config import Settings, get_settings
from app.db import log_upload, save_document, save_parties, save_clauses, save_risks
from app.dependencies import get_db_engine
from app.schemas import AnalysisResult, ProcessedDocument, RiskItem
from app.services import ai_contract_analysis, create_excel_report, normalize_analysis, upload_file_to_gcs
from app.utils import extract_text, is_supported
from app.db import (
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
) -> dict:
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
        # safe_name = f"{document_id}_{file.filename}"

        original_name = Path(file.filename).name
        safe_name = f"{document_id}_{original_name}"
        file_path = UPLOAD_DIR / safe_name

        content = await file.read()
        file_path.write_bytes(content)

        print("Bucket:", settings.gcs_bucket_name)
        print("Folder:", settings.gcs_folder)
        
        # ── GCS upload ────────────────────────────────────────────────────────
        gcs_path = upload_file_to_gcs(
            file_path,
            f"{settings.gcs_folder}/{safe_name}",
            settings.gcs_bucket_name,
        )
        print("GCS upload result:", gcs_path)

        # ── Text extraction (PDF / DOCX / DOC / TXT) ─────────────────────────
        try:
            extracted_text = extract_text(file_path)
            if extracted_text:
                printable_ratio = (
                    sum(c.isprintable() for c in extracted_text)
                    / len(extracted_text)
                )

                if printable_ratio < 0.8:
                    extracted_text = ""

                if len(extracted_text.strip()) < 50:
                    extracted_text = ""

            print("Extracted length:", len(extracted_text))
            print("Preview:", repr(extracted_text[:200]))
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
                        reason = (
                            "Document text could not be extracted. "
                            "The file may be scanned, corrupted, or an unsupported "
                            "legacy Word format (.doc)."
                        )
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
    return JSONResponse(
        content={
            "message": "Documents processed",
            "contracts": [doc.model_dump() for doc in processed],
        }
    )


@router.get("/api/contracts")
async def get_contracts(
    engine: Annotated[Engine, Depends(get_db_engine)],
):
    rows = get_all_documents(engine)

    contracts = []

    for row in rows:
        risk_score = row.risk_score or 0

        status = "High Risk" if risk_score >= 70 else "Completed"

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
            "summary": "",
            "clauses": clause_items,
            "warnings": warnings,
        })

    return contracts