import asyncio
import sqlite3
import time
from pathlib import Path

import aiosqlite

from printbot.jobs import Job, JobPatch, JobStatus, NewJob, transition_job_status
from printbot.jobs.ports import Clock
from printbot.kernel import Document, TextSource
from printbot.storage.migrations import apply_migrations


class SQLiteJobRepository:
    def __init__(
        self,
        path: Path,
        migrations_directory: Path,
        clock: Clock = time.time,
    ) -> None:
        self._path = path
        self._migrations_directory = migrations_directory
        self._clock = clock
        self._connection: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = await aiosqlite.connect(self._path)
        connection.row_factory = sqlite3.Row
        self._connection = connection
        await connection.execute("PRAGMA journal_mode = WAL")
        await connection.execute("PRAGMA busy_timeout = 5000")
        await apply_migrations(connection, self._migrations_directory)

    async def close(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is not None:
            await connection.close()

    async def add(self, job: NewJob) -> Job | None:
        connection = self._require_connection()
        async with self._lock:
            result = await connection.execute(
                """
                INSERT INTO jobs (
                    chat_id, telegram_update_id, source_json, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(telegram_update_id) DO NOTHING
                """,
                (
                    job.chat_id,
                    job.telegram_update_id,
                    job.source.model_dump_json(),
                    JobStatus.RECEIVED,
                    job.created_at,
                    job.created_at,
                ),
            )
            inserted = result.rowcount == 1
            await result.close()
            await connection.commit()
            if not inserted:
                return None
            cursor = await connection.execute(
                "SELECT * FROM jobs WHERE telegram_update_id = ?",
                (job.telegram_update_id,),
            )
            row = await cursor.fetchone()
            await cursor.close()
        if row is None:
            return None
        inserted = _job_from_row(row)
        if inserted.chat_id != job.chat_id or inserted.source != job.source:
            return None
        return inserted

    async def get(self, job_id: int) -> Job | None:
        connection = self._require_connection()
        cursor = await connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        await cursor.close()
        return _job_from_row(row) if row is not None else None

    async def claim(self, source: JobStatus, target: JobStatus) -> Job | None:
        transition_job_status(source, target)
        connection = self._require_connection()
        async with self._lock:
            await connection.execute("BEGIN IMMEDIATE")
            committed = False
            try:
                cursor = await connection.execute(
                    """
                    SELECT id FROM jobs
                    WHERE status = ?
                    ORDER BY created_at, id
                    LIMIT 1
                    """,
                    (source,),
                )
                row = await cursor.fetchone()
                await cursor.close()
                if row is None:
                    await connection.commit()
                    committed = True
                    return None
                updated_at = self._clock()
                result = await connection.execute(
                    """
                    UPDATE jobs
                    SET status = ?, updated_at = ?
                    WHERE id = ? AND status = ?
                    """,
                    (target, updated_at, row["id"], source),
                )
                if result.rowcount != 1:
                    await result.close()
                    return None
                await result.close()
                await connection.commit()
                committed = True
            finally:
                if not committed:
                    await connection.rollback()
        return await self.get(int(row["id"]))

    async def transition(
        self,
        job_id: int,
        expected: JobStatus,
        target: JobStatus,
        patch: JobPatch | None = None,
    ) -> Job | None:
        transition_job_status(expected, target)
        change = patch or JobPatch()
        connection = self._require_connection()
        async with self._lock:
            result = await connection.execute(
                """
                UPDATE jobs
                SET
                    status = ?,
                    document_json = COALESCE(?, document_json),
                    estimated_length_mm = COALESCE(?, estimated_length_mm),
                    error = COALESCE(?, error),
                    updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    target,
                    change.document.model_dump_json() if change.document is not None else None,
                    change.estimated_length_mm,
                    change.error,
                    self._clock(),
                    job_id,
                    expected,
                ),
            )
            updated = result.rowcount == 1
            await result.close()
            await connection.commit()
        return await self.get(job_id) if updated else None

    def _require_connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("repository is not initialized")
        return self._connection


def _job_from_row(row: sqlite3.Row) -> Job:
    document_json = row["document_json"]
    return Job(
        id=row["id"],
        chat_id=row["chat_id"],
        telegram_update_id=row["telegram_update_id"],
        source=TextSource.model_validate_json(row["source_json"]),
        status=JobStatus(row["status"]),
        document=Document.model_validate_json(document_json) if document_json else None,
        estimated_length_mm=row["estimated_length_mm"],
        error=row["error"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
