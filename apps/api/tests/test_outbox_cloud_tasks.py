import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.domain.models import Base, OutboxEvent
from app.outbox.cloud_tasks import CloudTasksPublisher
from app.outbox.service import process_one


def test_cloud_tasks_enqueue_local_fallback():
    settings = Settings(
        google_cloud_project=None,
        google_cloud_location="us-central1",
        app_env="test",
    )
    publisher = CloudTasksPublisher(settings)
    result = publisher.enqueue_outbox_event(
        event_id=uuid.uuid4(),
        event_type="notification.created",
        payload={"message": "hello"},
    )
    assert result is None


def test_cloud_tasks_enqueue_gcp_active():
    settings = Settings(
        google_cloud_project="praxisai-test-project",
        google_cloud_location="us-central1",
        app_env="test",
    )
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.name = (
        "projects/praxisai-test-project/locations/us-central1/queues/jobs/tasks/task-1"
    )
    mock_client.create_task.return_value = mock_response
    mock_client.queue_path.return_value = (
        "projects/praxisai-test-project/locations/us-central1/queues/jobs"
    )

    publisher = CloudTasksPublisher(settings, client=mock_client)
    task_name = publisher.enqueue_outbox_event(
        event_id=uuid.uuid4(),
        event_type="notification.created",
        payload={"message": "hello"},
    )

    assert task_name == mock_response.name
    mock_client.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_outbox_duplicate_delivery_idempotency() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        event_id = uuid.uuid4()
        event = OutboxEvent(
            id=event_id,
            event_type="test.idempotent",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={"key": "val"},
            status="SUCCEEDED",
            attempts=1,
        )
        session.add(event)
        await session.commit()

        processed_calls: list[dict[str, object]] = []

        async def mock_handler(payload: dict[str, object]) -> None:
            processed_calls.append(payload)

        handlers = {"test.idempotent": mock_handler}

        # Second delivery of an already succeeded outbox event returns event
        # without re-executing handler
        result = await process_one(session, handlers=handlers, event_id=event_id)
        assert result.status == "SUCCEEDED"
        assert len(processed_calls) == 0
    await engine.dispose()


@pytest.mark.asyncio
async def test_outbox_retry_exhaustion_dead_letter() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        event_id = uuid.uuid4()
        event = OutboxEvent(
            id=event_id,
            event_type="test.failing",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={"key": "val"},
            status="RUNNING",
            attempts=4,
        )
        session.add(event)
        await session.commit()

        async def mock_failing_handler(payload: dict[str, object]) -> None:
            raise RuntimeError("Persistent handler failure")

        handlers = {"test.failing": mock_failing_handler}

        with pytest.raises(RuntimeError, match="Persistent handler failure"):
            await process_one(
                session,
                handlers=handlers,
                event_id=event_id,
                max_attempts=5,
            )

        await session.refresh(event)
        assert event.status == "DEAD_LETTER"
        assert "Persistent handler failure" in (event.last_error or "")
    await engine.dispose()
