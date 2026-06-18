from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.engine import Engine

from app.db import get_search_history, get_upload_history
from app.dependencies import get_db_engine

router = APIRouter()


@router.get("/search-history", response_class=HTMLResponse)
def search_history(engine: Annotated[Engine, Depends(get_db_engine)]) -> HTMLResponse:
    try:
        rows = get_search_history(engine)
    except Exception as exc:
        return HTMLResponse(f"<h2>DB Error</h2><pre>{exc!r}</pre>")

    table_rows = "".join(
        f"<tr><td>{row.query_text}</td><td>{row.result_count}</td><td>{row.searched_at}</td></tr>"
        for row in rows
    )
    return HTMLResponse(f"""
    <html><body style='font-family:Arial;max-width:900px;margin:40px auto'>
    <h1>Search History</h1><p><a href='/'>← Back</a></p>
    <table border='1' cellpadding='10' cellspacing='0' style='width:100%;border-collapse:collapse'>
        <tr><th>Search Query</th><th>Result Count</th><th>Searched At</th></tr>
        {table_rows}
    </table>
    </body></html>""")


@router.get("/upload-history", response_class=HTMLResponse)
def upload_history(engine: Annotated[Engine, Depends(get_db_engine)]) -> HTMLResponse:
    try:
        rows = get_upload_history(engine)
    except Exception as exc:
        return HTMLResponse(f"<h2>DB Error</h2><pre>{exc!r}</pre>")

    table_rows = "".join(
        f"<tr><td>{row.document_id}</td><td>{row.file_name}</td><td>{row.document_type}</td>"
        f"<td>{row.risk_score}</td><td>{row.mode}</td><td>{row.status}</td>"
        f"<td>{row.gcs_path}</td><td>{row.uploaded_at}</td></tr>"
        for row in rows
    )
    return HTMLResponse(f"""
    <html><body style='font-family:Arial;max-width:1200px;margin:40px auto'>
    <h1>Upload History</h1><p><a href='/'>← Back</a></p>
    <table border='1' cellpadding='10' cellspacing='0' style='width:100%;border-collapse:collapse'>
        <tr><th>Document ID</th><th>File Name</th><th>Document Type</th>
            <th>Risk Score</th><th>Mode</th><th>Status</th>
            <th>GCS Path</th><th>Uploaded At</th></tr>
        {table_rows}
    </table>
    </body></html>""")
