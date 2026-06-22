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
    scores = [r.risk_score for r in rows if r.risk_score is not None]
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    return {
        "totalCount": total,
        "processingCount": 0,
        "completedCount": total,
        "failedCount": 0,
        "avgRiskScore": avg_score,
        "byType": [],
        "byRiskLevel": [],
        "historicalTrend": [],
    }