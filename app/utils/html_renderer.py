from fastapi.responses import HTMLResponse

from app.schemas import ProcessedDocument

_BASE_STYLES = """
body{font-family:Arial,sans-serif;background:#f6f8fb;max-width:1000px;margin:40px auto;color:#222}
.card{background:white;padding:24px;border-radius:14px;margin-bottom:24px;box-shadow:0 2px 10px rgba(0,0,0,.08)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:20px 0}
.grid div,.mini-card,.risk-card{background:#f9fafb;padding:14px;border-radius:10px;border:1px solid #e5e7eb}
.mini-card{margin-bottom:10px}
.risk-card{margin-bottom:10px;border-left:5px solid #dc2626}
a{color:#2563eb;text-decoration:none;margin-right:16px}
.actions{margin-bottom:24px}
.success{background:#dcfce7;color:#166534;padding:10px 14px;border-radius:8px;display:inline-block;margin-bottom:18px}
"""


def _render_document_card(doc: ProcessedDocument) -> str:
    analysis = doc.analysis

    parties = (
        "".join(f"<li>{p}</li>" for p in analysis.parties) or "<li>Not detected</li>"
    )

    clauses = "".join(
        f"<div class='mini-card'><b>{c.clause_type}</b><p>{c.clause_text}</p></div>"
        for c in analysis.key_clauses
    ) or "<p>No clauses detected.</p>"

    risks = "".join(
        f"<div class='risk-card'><b>{r.severity.upper()} — {r.risk}</b><p>{r.reason}</p></div>"
        for r in analysis.risks
    ) or "<p>No risks detected.</p>"

    return f"""
    <div class="card">
        <h2>{doc.file_name}</h2>
        <div class="grid">
            <div><b>Status</b><p>{doc.status}</p></div>
            <div><b>Risk Score</b><p>{doc.risk_score} / 100</p></div>
            <div><b>Mode</b><p>{doc.mode}</p></div>
            <div><b>Document Type</b><p>{analysis.document_type}</p></div>
        </div>
        <p><b>GCS Path:</b> {doc.gcs_path or 'Not uploaded to GCS'}</p>
        <h3>Parties</h3><ul>{parties}</ul>
        <h3>Important Dates</h3>
        <p><b>Effective:</b> {analysis.effective_date or 'Not detected'}</p>
        <p><b>Expiry:</b> {analysis.expiry_date or 'Not detected'}</p>
        <h3>Contract Value</h3><p>{analysis.contract_value or 'Not detected'}</p>
        <h3>Governing Law</h3><p>{analysis.governing_law or 'Not detected'}</p>
        <h3>Clauses</h3>{clauses}
        <h3>Risks</h3>{risks}
    </div>"""


def render_analysis_results(processed: list[ProcessedDocument]) -> HTMLResponse:
    cards = "".join(_render_document_card(doc) for doc in processed)
    return HTMLResponse(f"""
    <html><head><title>Analysis Results</title><style>{_BASE_STYLES}</style></head><body>
    <h1>Analysis Results</h1>
    <div class="success">Processed {len(processed)} document(s).</div>
    <div class="actions">
        <a href="/">← Back to Home</a>
        <a href="/export-excel">Download Excel</a>
        <a href="/upload-history">Upload History</a>
    </div>
    {cards}
    </body></html>""")
