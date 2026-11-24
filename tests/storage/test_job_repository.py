import asyncio
from pathlib import Path

import pytest

from printbot.jobs import JobPatch, JobStatus, NewJob
from printbot.kernel import Document, Paragraph, Run, TextSource
from printbot.storage import SQLiteJobRepository

MIGRATIONS = Path("migrations")


def new_job(update_id: int, text: str = "hello", chat_id: int = 42) -> NewJob:
    return NewJob(
        chat_id=chat_id,
        telegram_update_id=update_id,
        source=TextSource(text=text),
        created_at=float(update_id),
    )


@pytest.fixture
async def repository(tmp_path: Path):
    repository = SQLiteJobRepository(
        tmp_path / "printbot.sqlite3",
        MIGRATIONS,
        clock=lambda: 100.0,
    )
    await repository.initialize()
    yield repository
    await repository.close()


async def test_repository_persists_text_job(repository: SQLiteJobRepository) -> None:
    created = await repository.add(new_job(1))

    assert created is not None
    assert await repository.get(created.id) == created
    assert created.status is JobStatus.RECEIVED


async def test_duplicate_telegram_update_is_not_added(repository: SQLiteJobRepository) -> None:
    first = await repository.add(new_job(1, "first"))

    duplicate = await repository.add(new_job(1, "duplicate", chat_id=84))

    assert first is not None
    assert duplicate is None


async def test_transition_persists_document_and_estimate(
    repository: SQLiteJobRepository,
) -> None:
    job = await repository.add(new_job(1))
    assert job is not None
    converting = await repository.claim(JobStatus.RECEIVED, JobStatus.CONVERTING)
    assert converting is not None
    document = Document(blocks=(Paragraph(runs=(Run(text="hello"),)),))

    ready = await repository.transition(
        converting.id,
        JobStatus.CONVERTING,
        JobStatus.READY,
        JobPatch(document=document, estimated_length_mm=3.5),
    )

    assert ready is not None
    assert ready.document == document
    assert ready.estimated_length_mm == 3.5


async def test_concurrent_claims_are_atomic_and_creation_ordered(
    repository: SQLiteJobRepository,
) -> None:
    first = await repository.add(new_job(1))
    second = await repository.add(new_job(2))
    assert first is not None
    assert second is not None

    claimed = await asyncio.gather(
        repository.claim(JobStatus.RECEIVED, JobStatus.CONVERTING),
        repository.claim(JobStatus.RECEIVED, JobStatus.CONVERTING),
        repository.claim(JobStatus.RECEIVED, JobStatus.CONVERTING),
    )

    ids = [job.id for job in claimed if job is not None]
    assert ids == [first.id, second.id]


async def test_stale_transition_does_not_mutate_job(repository: SQLiteJobRepository) -> None:
    job = await repository.add(new_job(1))
    assert job is not None

    transitioned = await repository.transition(
        job.id,
        JobStatus.READY,
        JobStatus.PRINTING,
    )

    assert transitioned is None
    assert await repository.get(job.id) == job
