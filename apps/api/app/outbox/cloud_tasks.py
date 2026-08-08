import uuid

from google.cloud import tasks_v2
from pydantic import BaseModel

from app.config import Settings


class CloudTaskPayload(BaseModel):
    outbox_event_id: uuid.UUID
    event_type: str
    correlation_id: uuid.UUID


class CloudTasksPublisher:
    def __init__(self, settings: Settings, client: tasks_v2.CloudTasksClient | None = None) -> None:
        self._project = settings.google_cloud_project
        self._location = settings.google_cloud_location
        self._queue = settings.cloud_tasks_queue or "praxisai-staging-jobs"
        self._api_base_url = settings.api_base_url
        self._service_account_email = settings.google_service_account_email
        self._client = client

    def _task_url(self) -> str:
        return f"{self._api_base_url}/ops/tasks/process-outbox"

    def _get_client(self) -> tasks_v2.CloudTasksClient:
        if self._client is not None:
            return self._client
        return tasks_v2.CloudTasksClient()

    def enqueue_outbox_event(
        self,
        event_id: uuid.UUID,
        event_type: str,
        correlation_id: uuid.UUID,
    ) -> str | None:
        """Enqueue only outbox identity metadata after the transaction commits."""
        if not self._project or not self._location:
            # When GCP is not configured, fall back gracefully for local execution
            return None
        if not self._service_account_email:
            raise RuntimeError("Cloud Tasks requires the API service account email")

        client = self._get_client()
        parent = client.queue_path(self._project, self._location, self._queue)

        body = (
            CloudTaskPayload(
                outbox_event_id=event_id,
                event_type=event_type,
                correlation_id=correlation_id,
            )
            .model_dump_json()
            .encode("utf-8")
        )

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": self._task_url(),
                "headers": {"Content-Type": "application/json"},
                "body": body,
                "oidc_token": {
                    "service_account_email": self._service_account_email,
                    "audience": self._task_url(),
                },
            }
        }

        response = client.create_task(request={"parent": parent, "task": task})
        return str(response.name)
