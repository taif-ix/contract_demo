import json
from google.cloud import pubsub_v1


def publish_document_job(
    *,
    project_id: str,
    topic_id: str,
    document_id: str,
    gcs_path: str,
    file_name: str,
) -> str:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    payload = {
        "document_id": document_id,
        "gcs_path": gcs_path,
        "file_name": file_name,
    }

    future = publisher.publish(
        topic_path,
        json.dumps(payload).encode("utf-8"),
    )

    return future.result()