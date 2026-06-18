from pathlib import Path
from typing import Optional


# ── Google Cloud Storage ──────────────────────────────────────────────────────

def upload_file_to_gcs(
    local_file_path: Path,
    destination_blob_name: str,
    bucket_name: str,
) -> Optional[str]:
    """Upload a file to GCS and return its gs:// URI, or None on failure."""
    if not bucket_name:
        return None
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(str(local_file_path))
        return f"gs://{bucket_name}/{destination_blob_name}"
    except Exception as exc:
        print("GCS upload error:", repr(exc))
        return None
