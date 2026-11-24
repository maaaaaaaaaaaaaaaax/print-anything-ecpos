from pathlib import Path
from typing import Protocol

from printbot.ingest import Conversion
from printbot.jobs.models import Job, JobPatch, NewJob
from printbot.jobs.state import JobStatus
from printbot.kernel import Document, PrinterProfile, PrintPlan, TextSource


class Clock(Protocol):
    def __call__(self) -> float: ...


class JobRepository(Protocol):
    async def add(self, job: NewJob) -> Job | None: ...

    async def get(self, job_id: int) -> Job | None: ...

    async def claim(self, source: JobStatus, target: JobStatus) -> Job | None: ...

    async def transition(
        self,
        job_id: int,
        expected: JobStatus,
        target: JobStatus,
        patch: JobPatch | None = None,
    ) -> Job | None: ...


class Notifier(Protocol):
    async def job_updated(self, job: Job) -> None: ...

    async def job_output(self, job: Job, path: Path) -> bool: ...


class TextConverter(Protocol):
    async def convert(self, source: TextSource) -> Conversion: ...


class TextPlanner(Protocol):
    def __call__(self, document: Document, profile: PrinterProfile) -> PrintPlan: ...
