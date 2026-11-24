from typing import Annotated

from pydantic import Field

from printbot.jobs.state import JobStatus
from printbot.kernel import Document, Frozen, TextSource


class NewJob(Frozen):
    chat_id: int = Field(gt=0)
    telegram_update_id: int = Field(gt=0)
    source: TextSource
    created_at: float = Field(ge=0)


class JobPatch(Frozen):
    document: Document | None = None
    estimated_length_mm: float | None = Field(default=None, ge=0)
    error: str | None = None


class Job(Frozen):
    id: Annotated[int, Field(gt=0)]
    chat_id: int = Field(gt=0)
    telegram_update_id: int = Field(gt=0)
    source: TextSource
    status: JobStatus
    document: Document | None = None
    estimated_length_mm: float | None = Field(default=None, ge=0)
    error: str | None = None
    created_at: float = Field(ge=0)
    updated_at: float = Field(ge=0)
