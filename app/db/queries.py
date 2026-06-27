from typing import Any, Optional

from sqlalchemy.engine import Engine
from sqlalchemy import text


# ── poc_ai_doc write helpers ──────────────────────────────────────────────────

def save_document(engine: Engine, *, document_id: str, file_name: str,
                  document_type: str, effective_date: str, expiry_date: str,
                  contract_value: str, governing_law: str, risk_score: Any,
                  mode: str, gcs_path: str, raw_text: str) -> None:
    risk_val: Optional[int] = None
    if risk_score not in (None, ""):
        try:
            risk_val = int(float(risk_score))
        except (ValueError, TypeError):
            pass
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO poc_ai_doc.documents
                (document_id, file_name, document_type, effective_date, expiry_date,
                 contract_value, governing_law, risk_score, mode, gcs_path, raw_text)
            VALUES
                (:document_id, :file_name, :document_type, :effective_date, :expiry_date,
                 :contract_value, :governing_law, :risk_score, :mode, :gcs_path, :raw_text)
        """), {
            "document_id": document_id, "file_name": file_name,
            "document_type": document_type, "effective_date": effective_date,
            "expiry_date": expiry_date, "contract_value": contract_value,
            "governing_law": governing_law, "risk_score": risk_val,
            "mode": mode, "gcs_path": gcs_path, "raw_text": raw_text,
        })


def save_parties(engine: Engine, document_id: str, parties: list[str]) -> None:
    if not parties:
        return
    with engine.begin() as conn:
        for party in parties:
            conn.execute(text("""
                INSERT INTO poc_ai_doc.parties (document_id, party_name)
                VALUES (:document_id, :party_name)
            """), {"document_id": document_id, "party_name": party})


def save_clauses(engine: Engine, document_id: str, clauses: list[dict]) -> None:
    if not clauses:
        return
    with engine.begin() as conn:
        for clause in clauses:
            conn.execute(text("""
                INSERT INTO poc_ai_doc.clauses (document_id, clause_type, clause_text)
                VALUES (:document_id, :clause_type, :clause_text)
            """), {
                "document_id": document_id,
                "clause_type": clause.get("clause_type", "") if isinstance(clause, dict) else str(clause),
                "clause_text": clause.get("clause_text", "") if isinstance(clause, dict) else str(clause),
            })


def save_risks(engine: Engine, document_id: str, risks: list[dict]) -> None:
    if not risks:
        return
    with engine.begin() as conn:
        for risk in risks:
            conn.execute(text("""
                INSERT INTO poc_ai_doc.risks (document_id, risk, severity, reason)
                VALUES (:document_id, :risk, :severity, :reason)
            """), {
                "document_id": document_id,
                "risk": risk.get("risk", "") if isinstance(risk, dict) else str(risk),
                "severity": risk.get("severity", "") if isinstance(risk, dict) else "",
                "reason": risk.get("reason", "") if isinstance(risk, dict) else "",
            })


# ── poc_ai_doc read helpers ───────────────────────────────────────────────────

def get_all_documents(engine: Engine) -> list:
    with engine.begin() as conn:
        return conn.execute(text("""
            SELECT
                document_id,
                file_name,
                document_type,
                effective_date,
                expiry_date,
                contract_value,
                governing_law,
                risk_score,
                mode,
                gcs_path,
                raw_text,
                uploaded_at,
                status,
                error_message
            FROM poc_ai_doc.documents
            ORDER BY uploaded_at DESC
        """)).fetchall()


def get_document_by_id(engine: Engine, document_id: str):
    with engine.begin() as conn:
        return conn.execute(text("""
            SELECT
                document_id,
                file_name,
                gcs_path,
                raw_text,
                status,
                error_message
            FROM poc_ai_doc.documents
            WHERE document_id = :document_id
        """), {"document_id": document_id}).fetchone()


def get_document_clauses(engine: Engine, document_id: str) -> list:
    with engine.begin() as conn:
        return conn.execute(text("""
            SELECT clause_type, clause_text FROM poc_ai_doc.clauses
            WHERE document_id = :document_id
        """), {"document_id": document_id}).fetchall()


def get_document_risks(engine: Engine, document_id: str) -> list:
    with engine.begin() as conn:
        return conn.execute(text("""
            SELECT risk, severity, reason FROM poc_ai_doc.risks
            WHERE document_id = :document_id
        """), {"document_id": document_id}).fetchall()


def get_document_parties(engine: Engine, document_id: str) -> list:
    with engine.begin() as conn:
        return conn.execute(text("""
            SELECT party_name FROM poc_ai_doc.parties
            WHERE document_id = :document_id
        """), {"document_id": document_id}).fetchall()


# ── app schema (audit logs) ───────────────────────────────────────────────────

def log_upload(engine: Engine, *, document_id: str, file_name: str,
               document_type: str, risk_score: Any, mode: str,
               status: str, gcs_path: Optional[str]) -> None:
    risk_val: Optional[int] = None
    if risk_score not in (None, ""):
        try:
            risk_val = int(float(risk_score))
        except (ValueError, TypeError):
            pass
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                EXEC app.sp_insert_document_upload
                    @document_id=:document_id, @file_name=:file_name,
                    @document_type=:document_type, @risk_score=:risk_score,
                    @mode=:mode, @status=:status, @gcs_path=:gcs_path
            """), {
                "document_id": document_id, "file_name": file_name,
                "document_type": document_type, "risk_score": risk_val,
                "mode": mode, "status": status, "gcs_path": gcs_path,
            })
    except Exception as exc:
        print("DB upload log error:", repr(exc))


def log_search(engine: Engine, *, query_text: str, result_count: int) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                EXEC app.sp_insert_search_log
                    @query_text=:query_text, @result_count=:result_count
            """), {"query_text": query_text, "result_count": result_count})
    except Exception as exc:
        print("DB search log error:", repr(exc))


def get_search_history(engine: Engine) -> list:
    with engine.begin() as conn:
        return conn.execute(text("EXEC app.sp_get_search_history")).fetchall()


def get_upload_history(engine: Engine) -> list:
    with engine.begin() as conn:
        return conn.execute(text("EXEC app.sp_get_upload_history")).fetchall()
    
def create_queued_document(
    engine: Engine,
    *,
    document_id: str,
    file_name: str,
    gcs_path: str,
    raw_text: str = "",
) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO poc_ai_doc.documents
                (document_id, file_name, document_type, effective_date, expiry_date,
                 contract_value, governing_law, risk_score, mode, gcs_path, raw_text,
                 status, error_message)
            VALUES
                (:document_id, :file_name, '', '', '',
                 '', '', NULL, '', :gcs_path, :raw_text,
                 'queued', NULL)
        """), {
            "document_id": document_id,
            "file_name": file_name,
            "gcs_path": gcs_path,
            "raw_text": raw_text,
        })


def update_document_status(
    engine: Engine,
    *,
    document_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE poc_ai_doc.documents
            SET status = :status,
                error_message = :error_message
            WHERE document_id = :document_id
        """), {
            "document_id": document_id,
            "status": status,
            "error_message": error_message,
        })


def update_document_analysis(
    engine: Engine,
    *,
    document_id: str,
    document_type: str,
    effective_date: str,
    expiry_date: str,
    contract_value: str,
    governing_law: str,
    risk_score: Any,
    mode: str,
    raw_text: str,
) -> None:
    risk_val: Optional[int] = None
    if risk_score not in (None, ""):
        try:
            risk_val = int(float(risk_score))
        except (ValueError, TypeError):
            pass

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE poc_ai_doc.documents
            SET document_type = :document_type,
                effective_date = :effective_date,
                expiry_date = :expiry_date,
                contract_value = :contract_value,
                governing_law = :governing_law,
                risk_score = :risk_score,
                mode = :mode,
                raw_text = :raw_text,
                status = 'completed',
                error_message = NULL
            WHERE document_id = :document_id
        """), {
            "document_id": document_id,
            "document_type": document_type,
            "effective_date": effective_date,
            "expiry_date": expiry_date,
            "contract_value": contract_value,
            "governing_law": governing_law,
            "risk_score": risk_val,
            "mode": mode,
            "raw_text": raw_text,
        })


def clear_document_details(engine: Engine, document_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM poc_ai_doc.parties WHERE document_id = :document_id"), {"document_id": document_id})
        conn.execute(text("DELETE FROM poc_ai_doc.clauses WHERE document_id = :document_id"), {"document_id": document_id})
        conn.execute(text("DELETE FROM poc_ai_doc.risks WHERE document_id = :document_id"), {"document_id": document_id})
