from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.routes import contracts, history, reports, search

app = FastAPI(title="AI Document Intelligence Demo")

app.include_router(contracts.router)
app.include_router(search.router)
app.include_router(reports.router)
app.include_router(history.router)


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse("""
    <html><head><title>AI Document Intelligence Demo</title><style>
    body{font-family:Arial;max-width:900px;margin:40px auto;background:#f6f8fb}
    .box{background:white;border:1px solid #ddd;padding:20px;border-radius:12px;
         margin-bottom:20px;box-shadow:0 2px 10px rgba(0,0,0,.05)}
    button{padding:10px 16px;cursor:pointer;background:#2563eb;color:white;border:none;border-radius:8px}
    input{margin:8px 0;padding:10px}a{color:#2563eb;text-decoration:none}
    .hint{color:#555;font-size:14px}.badge{display:inline-block;background:#e0ecff;
    color:#1d4ed8;padding:3px 10px;border-radius:999px;font-size:12px;margin:2px}
    </style></head><body>
    <h1>AI Document Intelligence Demo</h1>
    <div class="box">
        <h2>Upload Contract Documents</h2>
        <p class="hint">Upload one or multiple contract files for AI analysis.</p>
        <p>
            <span class="badge">PDF</span>
            <span class="badge">DOCX</span>
            <span class="badge">DOC</span>
            <span class="badge">TXT</span>
        </p>
        <form action="/upload-contracts" method="post" enctype="multipart/form-data">
            <input type="file" name="files"
                   accept=".pdf,.docx,.doc,.txt"
                   multiple required><br>
            <button type="submit">Analyze Contract(s)</button>
        </form>
    </div>
    <div class="box">
        <h2>Search</h2>
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="Search clause, risk, payment..." required>
            <button type="submit">Search</button>
        </form>
    </div>
    <div class="box">
        <h2>Reports</h2>
        <p><a href="/export-excel">Download Excel Report</a></p>
        <p><a href="/search-history">View Search History</a></p>
        <p><a href="/upload-history">View Upload History</a></p>
    </div>
    </body></html>""")
