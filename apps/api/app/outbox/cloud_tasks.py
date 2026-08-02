import uuid
from typing import Any

from google.cloud import tasks_v2  # type: ignore[attr-defined]
from pydantic import BaseModel

from app.config import Settings


class CloudTaskPayload(BaseModel):
    outbox_event_id: uuid.UUID
    event_type: str
    payload: dict[str, Any]


class CloudTasksPublisher:
    def __init__(self, settings: Settings, client: tasks_v2.CloudTasksClient | None = None) -> None:
        self._project = settings.google_cloud_project
        self._location = settings.google_cloud_location
        self._queue = getattr(settings, "cloud_tasks_queue", None) or "praxisai-staging-jobs"
        self._api_base_url = settings.api_base_url
        self._client = client

    def _get_client(self) -> tasks_v2.CloudTasksClient:
        if self._client is not None:
            return self._client
        return tasks_v2.CloudTasksClient()

    def enqueue_outbox_event(
        self, event_id: uuid.UUID, event_type: str, payload: dict[str, Any]
    ) -> str | None:
        """Enqueue Cloud Task to process outbox event after DB commit."""
        if not self._project or not self._location:
            # When GCP is not configured, fall back gracefully for local execution
            return None

        client = self._get_client()
        parent = client.queue_path(self._project, self._location, self._queue)

        body = (
            CloudTaskPayload(
                outbox_event_id=event_id,
                event_type=event_type,
                payload=payload,
            )
            .model_dump_json()
            .encode("utf-8")
        )

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self._api_base_url}/operations/tasks/process-outbox",
                "headers": {"Content-Type": "application/json"},
                "body": body,
                "oidc_token": {
                    "service_account_email": f"praxisai-api@{self._project}.iam.gserviceaccount.com"
                },
            }
        }

        response = client.create_task(request={"parent": parent, "task": task})
        return str(response.name)
