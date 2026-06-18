from app.schemas import AnalysisResult, NormalizedDocument


def normalize_analysis(
    document_id: str,
    file_name: str,
    raw_text: str,
    analysis: AnalysisResult,
    gcs_path: str = "",
) -> NormalizedDocument:
    """Combine file metadata + AI analysis into a single storable record."""
    return NormalizedDocument(
        document_id=document_id,
        file_name=file_name,
        document_type=analysis.document_type,
        parties=analysis.parties,
        effective_date=analysis.effective_date,
        expiry_date=analysis.expiry_date,
        contract_value=analysis.contract_value,
        governing_law=analysis.governing_law,
        key_clauses=[c.model_dump() for c in analysis.key_clauses],
        risks=[r.model_dump() for r in analysis.risks],
        risk_score=analysis.risk_score,
        mode=analysis.mode,
        gcs_path=gcs_path,
        raw_text=raw_text,
    )
