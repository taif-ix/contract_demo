"""
tests/
├── conftest.py              — shared fixtures (TestClient, mock engine, sample PDFs)
├── test_routes/
│   ├── test_contracts.py    — upload endpoint: valid PDF, non-PDF, empty PDF
│   ├── test_search.py       — search: keyword hit, no results, DB error path
│   ├── test_reports.py      — export-excel: empty store 404, populated store 200
│   └── test_history.py      — search-history / upload-history DB rows
├── test_services/
│   ├── test_ai_client.py    — mock_contract_analysis keyword detection
│   ├── test_analysis.py     — normalize_analysis field mapping
│   ├── test_storage.py      — load/save/append round-trip
│   └── test_excel.py        — multi-sheet workbook structure
└── test_utils/
    ├── test_pdf.py          — extract_text_from_pdf with fixture PDF
    └── test_text.py         — split_into_paragraphs, find_best_paragraph
"""

# This file documents the intended test layout.
# Run with:  pytest tests/ -v
