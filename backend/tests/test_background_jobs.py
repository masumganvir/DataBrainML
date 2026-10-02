"""DataWise AI — Background Jobs & Worker Tests."""

import pytest
from app.db.session import init_db
from app.workers.queue import get_job_queue
from app.workers.runner import BackgroundWorker


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_job_enqueue_and_status():

    queue = get_job_queue()
    job_id = await queue.enqueue_job(
        job_type="profiling",
        payload={"dataset_id": "test-ds-1"},
        priority=8,
    )
    assert job_id is not None

    status_data = await queue.get_job_status(job_id)
    assert status_data is not None
    assert status_data["status"] == "pending"


@pytest.mark.asyncio
async def test_worker_run_once():
    queue = get_job_queue()
    job_id = await queue.enqueue_job(
        job_type="profiling",
        payload={"dataset_id": "test-ds-2"},
        priority=10,
        queue="worker_test_queue",
    )

    worker = BackgroundWorker(queues=["worker_test_queue"])
    processed = await worker.run_once()
    assert processed is True

    status_data = await queue.get_job_status(job_id)
    assert status_data["status"] == "completed"

