from typing import Any
from pydantic import BaseModel


class RiskItem(BaseModel):
    risk: str = ""
    severity: str = ""
    reason: str = ""


class ClauseItem(BaseModel):
    clause_type: str = ""
    clause_text: str = ""


class AnalysisResult(BaseModel):
    document_type: str = ""
    parties: list[str] = []
    effective_date: str = ""
    expiry_date: str = ""
    contract_value: str = ""
    governing_law: str = ""
    key_clauses: list[ClauseItem] = []
    risks: list[RiskItem] = []
    risk_score: int = 0
    mode: str = ""
    ai_error: str = ""


class NormalizedDocument(BaseModel):
    document_id: str
    file_name: str
    document_type: str = ""
    parties: list[str] = []
    effective_date: str = ""
    expiry_date: str = ""
    contract_value: str = ""
    governing_law: str = ""
    key_clauses: list[Any] = []
    risks: list[Any] = []
    risk_score: int | str = ""
    mode: str = ""
    gcs_path: str = ""
    raw_text: str = ""


class ProcessedDocument(BaseModel):
    document_id: str = ""
    file_name: str
    status: str
    risk_score: int | str = ""
    mode: str = ""
    gcs_path: str = ""
    analysis: AnalysisResult
