from pathlib import Path
from typing import Optional


# ── Google Cloud Storage ──────────────────────────────────────────────────────

from google.cloud import storage


def upload_file_to_gcs(file_path, destination_blob_name, bucket_name):
    try:

        client = storage.Client(project="ai-document-automation-498914")

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(str(file_path))

        return destination_blob_name

    except Exception as e:
        print("GCS ERROR:", repr(e))
        raise
