from pathlib import Path

import pandas as pd
from sqlalchemy.engine import Engine

from app.db import (
    get_all_documents, get_document_clauses,
    get_document_parties, get_document_risks,
)

OUTPUT_PATH = Path("outputs/contracts_analysis.xlsx")


def clean_excel_text(value):
    if value is None:
        return ""

    value = str(value)

    return "".join(
        c for c in value
        if c in "\n\r\t" or ord(c) >= 32
    )

def create_excel_report(engine: Engine) -> Path:
    """Build a multi-sheet Excel workbook directly from the DB."""
    documents = get_all_documents(engine)

    documents_rows, parties_rows, clauses_rows, risks_rows, raw_text_rows = [], [], [], [], []

    for doc in documents:
        doc_id = doc.document_id

        documents_rows.append({
            "document_id": doc_id,
            "file_name": doc.file_name,
            "document_type": doc.document_type,
            "effective_date": doc.effective_date,
            "expiry_date": doc.expiry_date,
            "contract_value": doc.contract_value,
            "governing_law": doc.governing_law,
            "risk_score": doc.risk_score,
            "mode": doc.mode,
            "gcs_path": doc.gcs_path,
        })

        for party in get_document_parties(engine, doc_id):
            parties_rows.append({"document_id": doc_id, "file_name": doc.file_name, "party_name": party.party_name})

        for clause in get_document_clauses(engine, doc_id):
            clauses_rows.append({
                "document_id": doc_id, "file_name": doc.file_name,
                "clause_type": clause.clause_type, "clause_text": clean_excel_text(clause.clause_text),
            })

        for risk in get_document_risks(engine, doc_id):
            risks_rows.append({
                "document_id": doc_id, "file_name": doc.file_name,
                "risk": risk.risk, "severity": risk.severity, "reason": clean_excel_text(risk.reason),
            })

        raw_text_rows.append({
            "document_id": doc_id,
            "file_name": doc.file_name,
            "raw_text": clean_excel_text(
                (doc.raw_text or "")[:30_000]
            ),
        })

        # for row in raw_text_rows:
        #     print("RAW TEXT PREVIEW:")
        #     print(repr(row["raw_text"][:500]))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        pd.DataFrame(documents_rows).to_excel(writer, sheet_name="Documents", index=False)
        pd.DataFrame(parties_rows).to_excel(writer, sheet_name="Parties", index=False)
        pd.DataFrame(clauses_rows).to_excel(writer, sheet_name="Clauses", index=False)
        pd.DataFrame(risks_rows).to_excel(writer, sheet_name="Risks", index=False)
        pd.DataFrame(raw_text_rows).to_excel(writer, sheet_name="Raw_Text", index=False)

    return OUTPUT_PATH
