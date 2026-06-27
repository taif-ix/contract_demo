from app.db.queries import (
    save_document, save_parties, save_clauses, save_risks,
    get_all_documents, get_document_by_id, get_document_clauses, get_document_risks, get_document_parties,
    log_upload, log_search,
    get_search_history, get_upload_history,
)
from app.db.session import make_engine

__all__ = [
    "make_engine",
    "save_document", "save_parties", "save_clauses", "save_risks",
    "get_all_documents", "get_document_by_id", "get_document_clauses", "get_document_risks", "get_document_parties",
    "log_upload", "log_search",
    "get_search_history", "get_upload_history",
]

from app.db.queries import (
    create_queued_document,
    update_document_status,
    update_document_analysis,
    clear_document_details,
)
