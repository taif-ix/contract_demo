# AI Document Intelligence Demo

FastAPI service that uploads contract documents, uses Groq AI to extract key clauses, risks, parties, and dates, stores everything in SQL Server, and exports to Excel.

## Supported File Types

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Text-based PDFs. Scanned/image PDFs require OCR. |
| Word (modern) | `.docx` | Full support including tables |
| Word (legacy) | `.doc` | Requires `antiword` installed on the server, or `textract` |
| Plain text | `.txt` | UTF-8 encoded |

> **Note on `.doc` files:** The legacy `.doc` format requires `antiword` (Linux/Mac: `apt install antiword` / `brew install antiword`) or the `textract` Python package (`pip install textract`). On Windows, `.doc` files will attempt a plain-text fallback which may not work well — converting to `.docx` first is recommended.

## Project Structure

```
contract_demo/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Pydantic Settings — all env vars
│   ├── dependencies.py      # Shared FastAPI Depends()
│   ├── routes/
│   │   ├── contracts.py     # POST /upload-contracts
│   │   ├── search.py        # GET  /search
│   │   ├── reports.py       # GET  /export-excel
│   │   └── history.py       # GET  /search-history, /upload-history
│   ├── services/
│   │   ├── ai_client.py     # Groq AI / mock analysis
│   │   ├── analysis.py      # normalize_analysis()
│   │   ├── storage.py       # GCS upload
│   │   └── excel.py         # Excel report (reads from DB)
│   ├── db/
│   │   ├── session.py       # SQLAlchemy engine
│   │   └── queries.py       # All DB read/write operations
│   ├── schemas/
│   │   └── contract.py      # Pydantic request/response models
│   └── utils/
│       ├── file_extractor.py  # Universal text extractor (PDF/DOCX/DOC/TXT)
│       ├── pdf.py             # PDF-specific extraction
│       ├── text.py            # Paragraph splitting helpers
│       └── html_renderer.py   # HTML template helpers
├── tests/
├── outputs/                 # gitignored — Excel reports
├── uploads/                 # gitignored — uploaded files
└── requirements.txt
```

## Database Schema

All contract data is stored in the `poc_ai_doc` schema:

| Table | Contents |
|-------|----------|
| `poc_ai_doc.documents` | Contract metadata, risk score, raw text |
| `poc_ai_doc.parties` | Extracted party names per document |
| `poc_ai_doc.clauses` | Key clauses (termination, payment, etc.) |
| `poc_ai_doc.risks` | Detected risks with severity |
| `app.document_uploads` | Audit log — who uploaded what, when |
| `app.search_logs` | Search query history |

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in your values
python -m uvicorn app.main:app --reload --port 8080
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | SQLAlchemy connection string for SQL Server |
| `GROQ_API_KEY` | ❌ | Groq API key — mock keyword analysis used if absent |
| `GCS_BUCKET_NAME` | ❌ | GCS bucket name for file backup |
| `GCS_FOLDER` | ❌ | GCS folder prefix (default: `contracts`) |

### Example DATABASE_URL formats

```dotenv
# SQL Server with username/password
DATABASE_URL=mssql+pyodbc://username:password@server_ip/dbname?driver=ODBC+Driver+17+for+SQL+Server

# SQL Server with Windows Authentication
DATABASE_URL=mssql+pyodbc://@localhost/dbname?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

# Named instance (e.g. SQLEXPRESS)
DATABASE_URL=mssql+pyodbc://username:password@localhost\SQLEXPRESS/dbname?driver=ODBC+Driver+17+for+SQL+Server
```

## How It Works

```
File upload (PDF / DOCX / DOC / TXT)
        ↓
Text extraction  (fitz for PDF, python-docx for DOCX, antiword/textract for DOC)
        ↓
Groq AI analysis  (extracts parties, dates, clauses, risks, risk score)
        ↓
        ├── poc_ai_doc.documents   ← contract metadata + raw text
        ├── poc_ai_doc.parties     ← party names
        ├── poc_ai_doc.clauses     ← key clauses
        └── poc_ai_doc.risks       ← detected risks
        ↓
Excel export reads directly from DB
Search queries DB directly
```

## Running Tests

```bash
pytest tests/ -v
```
