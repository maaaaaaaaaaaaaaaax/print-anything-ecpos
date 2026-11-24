import asyncio
import contextlib
from pathlib import Path

from printbot.ingest import ConversionError
from printbot.jobs.models import JobPatch
from printbot.jobs.ports import JobRepository, Notifier, TextConverter, TextPlanner
from printbot.jobs.state import JobStatus
from printbot.kernel import PrinterProfile
from printbot.printing import Printer, PrinterError

_IDLE_SLEEP_SECONDS = 0.1


class ConversionWorker:
    def __init__(
        self,
        repository: JobRepository,
        converter: TextConverter,
        planner: TextPlanner,
        profile: PrinterProfile,
        notifier: Notifier,
    ) -> None:
        self._repository = repository
        self._converter = converter
        self._planner = planner
        self._profile = profile
        self._notifier = notifier

    async def run(self) -> None:
        while True:
            worked = await self.run_once()
            if not worked:
                await asyncio.sleep(_IDLE_SLEEP_SECONDS)

    async def run_once(self) -> bool:
        job = await self._repository.claim(JobStatus.RECEIVED, JobStatus.CONVERTING)
        if job is None:
            return False
        await self._notifier.job_updated(job)
        try:
            conversion = await self._converter.convert(job.source)
        except ConversionError as error:
            failed = await self._repository.transition(
                job.id,
                JobStatus.CONVERTING,
                JobStatus.FAILED,
                JobPatch(error=str(error)),
            )
            if failed is not None:
                await self._notifier.job_updated(failed)
            return True
        plan = self._planner(conversion.document, self._profile)
        ready = await self._repository.transition(
            job.id,
            JobStatus.CONVERTING,
            JobStatus.READY,
            JobPatch(
                document=conversion.document,
                estimated_length_mm=plan.length_mm,
            ),
        )
        if ready is not None:
            await self._notifier.job_updated(ready)
        return True


class PrintWorker:
    def __init__(
        self,
        repository: JobRepository,
        planner: TextPlanner,
        profile: PrinterProfile,
        printer: Printer,
        notifier: Notifier,
    ) -> None:
        self._repository = repository
        self._planner = planner
        self._profile = profile
        self._printer = printer
        self._notifier = notifier
        self._execution_lock = asyncio.Lock()

    async def run(self) -> None:
        while True:
            worked = await self.run_once()
            if not worked:
                await asyncio.sleep(_IDLE_SLEEP_SECONDS)

    async def run_once(self) -> bool:
        async with self._execution_lock:
            return await self._run_once_serialized()

    async def _run_once_serialized(self) -> bool:
        job = await self._repository.claim(JobStatus.READY, JobStatus.PRINTING)
        if job is None:
            return False
        await self._notifier.job_updated(job)
        if job.document is None:
            raise RuntimeError(f"job {job.id} is ready without a document")
        plan = self._planner(job.document, self._profile)
        try:
            output = await self._printer.execute(plan)
        except PrinterError as error:
            failed = await self._repository.transition(
                job.id,
                JobStatus.PRINTING,
                JobStatus.FAILED,
                JobPatch(error=str(error)),
            )
            if failed is not None:
                await self._notifier.job_updated(failed)
            return True
        done = await self._repository.transition(
            job.id,
            JobStatus.PRINTING,
            JobStatus.DONE,
        )
        if done is not None:
            if isinstance(output, Path):
                sent = await self._notifier.job_output(done, output)
                if sent:
                    with contextlib.suppress(OSError):
                        output.unlink(missing_ok=True)
                    with contextlib.suppress(OSError):
                        output.parent.rmdir()
            await self._notifier.job_updated(done)
        return True
