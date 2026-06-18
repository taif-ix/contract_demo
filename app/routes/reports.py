from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.engine import Engine

from app.db import get_all_documents
from app.dependencies import get_db_engine
from app.services import create_excel_report

router = APIRouter()


@router.get("/export-excel")
def export_excel(engine: Annotated[Engine, Depends(get_db_engine)]) -> FileResponse:
    if not get_all_documents(engine):
        return JSONResponse({"error": "No analyzed documents found"}, status_code=404)

    excel_path = create_excel_report(engine)
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="contracts_analysis.xlsx",
    )
