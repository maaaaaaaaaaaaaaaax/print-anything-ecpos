import asyncio
from pathlib import Path

import pytest

from printbot.formatting import plan_text
from printbot.ingest import ConversionError, PlainTextConverter
from printbot.jobs import ConversionWorker, JobService, JobStatus, PrintWorker
from printbot.kernel import PrintPlan
from printbot.printing import PrinterExecutionError, PrinterStatus, load_bundled_profile
from printbot.storage import SQLiteJobRepository


class RecordingNotifier:
    def __init__(self) -> None:
        self.statuses: list[JobStatus] = []
        self.outputs: list[Path] = []
        self.output_sent = True

    async def job_updated(self, job) -> None:
        self.statuses.append(job.status)

    async def job_output(self, job, path: Path) -> bool:
        _ = job
        self.outputs.append(path)
        return self.output_sent


class SerialRecordingPrinter:
    def __init__(self) -> None:
        self.active = 0
        self.max_active = 0
        self.plans: list[PrintPlan] = []

    async def execute(self, plan: PrintPlan) -> None:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        await asyncio.sleep(0.01)
        self.plans.append(plan)
        self.active -= 1

    async def status(self) -> PrinterStatus:
        raise AssertionError("status is not used")

    async def close(self) -> None:
        return


class FailingPrinter(SerialRecordingPrinter):
    async def execute(self, plan: PrintPlan):
        _ = plan
        raise PrinterExecutionError("usb failure")


class FailingConverter:
    async def convert(self, source):
        _ = source
        raise ConversionError("invalid text")


@pytest.fixture
async def repository(tmp_path: Path):
    repository = SQLiteJobRepository(
        tmp_path / "jobs.sqlite3",
        Path("migrations"),
        clock=lambda: 50.0,
    )
    await repository.initialize()
    yield repository
    await repository.close()


async def test_service_drives_job_to_done_and_notifies_each_stage(
    repository: SQLiteJobRepository,
) -> None:
    profile = load_bundled_profile("tm_t88iv")
    notifier = RecordingNotifier()
    printer = SerialRecordingPrinter()
    service = JobService(repository, clock=lambda: 1.0)
    conversion = ConversionWorker(repository, PlainTextConverter(), plan_text, profile, notifier)
    printing = PrintWorker(repository, plan_text, profile, printer, notifier)

    job = await service.submit(chat_id=42, telegram_update_id=10, text="hello")
    assert job is not None
    assert job.status is JobStatus.RECEIVED
    assert await conversion.run_once()
    assert await printing.run_once()

    finished = await repository.get(job.id)
    assert finished is not None
    assert finished.status is JobStatus.DONE
    assert notifier.statuses == [
        JobStatus.CONVERTING,
        JobStatus.READY,
        JobStatus.PRINTING,
        JobStatus.DONE,
    ]
    assert len(printer.plans) == 1


async def test_duplicate_submission_returns_none(repository: SQLiteJobRepository) -> None:
    service = JobService(repository, clock=lambda: 1.0)

    assert await service.submit(chat_id=42, telegram_update_id=10, text="hello") is not None
    assert await service.submit(chat_id=42, telegram_update_id=10, text="hello") is None


async def test_concurrent_print_worker_calls_do_not_overlap(
    repository: SQLiteJobRepository,
) -> None:
    profile = load_bundled_profile("tm_t88iv")
    notifier = RecordingNotifier()
    printer = SerialRecordingPrinter()
    service = JobService(repository, clock=lambda: 1.0)
    conversion = ConversionWorker(repository, PlainTextConverter(), plan_text, profile, notifier)
    printing = PrintWorker(repository, plan_text, profile, printer, notifier)

    for update_id in (10, 11):
        assert await service.submit(42, update_id, f"message {update_id}") is not None
        assert await conversion.run_once()

    await asyncio.gather(printing.run_once(), printing.run_once())

    assert printer.max_active == 1
    assert len(printer.plans) == 2


async def test_typed_printer_failure_marks_job_failed(
    repository: SQLiteJobRepository,
) -> None:
    profile = load_bundled_profile("tm_t88iv")
    notifier = RecordingNotifier()
    service = JobService(repository, clock=lambda: 1.0)
    conversion = ConversionWorker(repository, PlainTextConverter(), plan_text, profile, notifier)
    printing = PrintWorker(repository, plan_text, profile, FailingPrinter(), notifier)
    job = await service.submit(42, 10, "hello")
    assert job is not None
    assert await conversion.run_once()

    assert await printing.run_once()

    failed = await repository.get(job.id)
    assert failed is not None
    assert failed.status is JobStatus.FAILED
    assert failed.error == "usb failure"
    assert notifier.statuses[-1] is JobStatus.FAILED


async def test_typed_conversion_failure_marks_job_failed(
    repository: SQLiteJobRepository,
) -> None:
    profile = load_bundled_profile("tm_t88iv")
    notifier = RecordingNotifier()
    service = JobService(repository, clock=lambda: 1.0)
    conversion = ConversionWorker(repository, FailingConverter(), plan_text, profile, notifier)
    job = await service.submit(42, 10, "hello")
    assert job is not None

    assert await conversion.run_once()

    failed = await repository.get(job.id)
    assert failed is not None
    assert failed.status is JobStatus.FAILED
    assert failed.error == "invalid text"
    assert notifier.statuses[-1] is JobStatus.FAILED
