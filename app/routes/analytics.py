from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.engine import Engine

from app.db import get_all_documents
from app.dependencies import get_db_engine

router = APIRouter()


@router.get("/api/analytics")
def get_analytics(
    engine: Annotated[Engine, Depends(get_db_engine)],
):
    rows = get_all_documents(engine)

    total = len(rows)
    processing = 0
    completed = 0
    failed = 0
    high_risk = 0
    low_risk = 0
    medium_risk = 0
    type_map: dict[str, int] = {}

    for row in rows:
        db_status = (row.status or "").lower()
        risk_score = row.risk_score

        if db_status in ("queued", "processing"):
            processing += 1
            continue

        if db_status == "failed":
            failed += 1
            continue

        if risk_score is not None and risk_score >= 70:
            high_risk += 1
        else:
            completed += 1

        if risk_score is not None:
            if risk_score <= 30:
                low_risk += 1
            elif risk_score <= 69:
                medium_risk += 1
            else:
                high_risk += 0

        document_type = row.document_type or "Contract"
        type_map[document_type] = type_map.get(document_type, 0) + 1

    scores = [
        r.risk_score
        for r in rows
        if r.risk_score is not None and (r.status or "").lower() not in ("queued", "processing", "failed")
    ]
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    return {
        "totalCount": total,
        "processingCount": processing,
        "completedCount": completed + high_risk,
        "failedCount": failed,
        "avgRiskScore": avg_score,
        "byType": [
            {"name": name, "value": value}
            for name, value in sorted(type_map.items())
        ],
        "byRiskLevel": [
            {"name": "Low Risk (0-30)", "value": low_risk},
            {"name": "Medium Risk (31-69)", "value": medium_risk},
            {"name": "High Risk (70-100)", "value": high_risk},
        ],
        "historicalTrend": [],
    }
