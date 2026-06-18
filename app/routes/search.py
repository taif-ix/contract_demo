from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.engine import Engine

from app.db import (
    log_search, get_all_documents,
    get_document_clauses, get_document_risks,
)
from app.dependencies import get_db_engine
from app.utils.text import split_into_paragraphs

router = APIRouter()

_STYLES = """
body{font-family:Arial,sans-serif;background:#f6f8fb;max-width:1000px;margin:40px auto;color:#222}
.header{background:white;padding:24px;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.06);margin-bottom:24px}
input{padding:12px;width:70%;border:1px solid #ccc;border-radius:8px}
button{padding:12px 18px;border:none;border-radius:8px;background:#2563eb;color:white;cursor:pointer}
.result-card{background:white;padding:22px;border-radius:14px;margin-bottom:16px;
             box-shadow:0 2px 10px rgba(0,0,0,.06);border-left:5px solid #2563eb}
.badge{display:inline-block;background:#e0ecff;color:#1d4ed8;padding:5px 10px;
       border-radius:999px;font-size:12px;font-weight:bold;margin-right:8px}
.severity{background:#fee2e2;color:#b91c1c}
.file{color:#666;font-size:14px}.text{line-height:1.6;white-space:pre-wrap}
a{color:#2563eb;text-decoration:none}
"""


@router.get("/search", response_class=HTMLResponse)
def search(
    q: Annotated[str, Query(min_length=1)],
    engine: Annotated[Engine, Depends(get_db_engine)],
) -> HTMLResponse:
    query = q.lower()
    results = []

    for doc in get_all_documents(engine):
        doc_id = doc.document_id
        file_name = doc.file_name

        # Search clauses
        for clause in get_document_clauses(engine, doc_id):
            if query in (clause.clause_type or "").lower() or query in (clause.clause_text or "").lower():
                results.append({
                    "file_name": file_name, "match_area": "Clause",
                    "title": clause.clause_type, "matched_text": clause.clause_text,
                })

        # Search risks
        for risk in get_document_risks(engine, doc_id):
            risk_text = f"{risk.risk} {risk.severity} {risk.reason}".lower()
            if query in risk_text:
                results.append({
                    "file_name": file_name, "match_area": "Risk",
                    "title": risk.risk, "matched_text": risk.reason,
                    "severity": risk.severity,
                })

        # Search raw text
        for para in split_into_paragraphs(doc.raw_text or ""):
            if query in para.lower():
                results.append({
                    "file_name": file_name, "match_area": "Raw Text",
                    "title": "Text Match", "matched_text": para[:1200],
                })

    log_search(engine, query_text=q, result_count=len(results))

    cards = ""
    for result in results[:50]:
        severity_badge = (
            f"<span class='badge severity'>{result['severity']}</span>"
            if result.get("severity") else ""
        )
        cards += f"""
        <div class='result-card'>
            <span class='badge'>{result['match_area']}</span>{severity_badge}
            <h3>{result['title']}</h3>
            <p class='file'>📄 {result['file_name']}</p>
            <p class='text'>{result['matched_text']}</p>
        </div>"""

    cards = cards or "<p>No results found.</p>"

    return HTMLResponse(f"""
    <html><head><title>Search Results</title><style>{_STYLES}</style></head><body>
    <div class="header">
        <h1>Search Results</h1>
        <p>Found <b>{len(results)}</b> results for <b>{q}</b></p>
        <form action="/search" method="get">
            <input type="text" name="q" value="{q}" placeholder="Search clause, risk, payment...">
            <button type="submit">Search</button>
        </form>
        <p><a href="/">← Back to Home</a></p>
    </div>
    {cards}
    </body></html>""")
