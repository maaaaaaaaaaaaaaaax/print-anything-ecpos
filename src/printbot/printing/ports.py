from enum import StrEnum
from pathlib import Path
from typing import Protocol

from printbot.kernel import Frozen, PrintPlan


class PaperState(StrEnum):
    OK = "ok"
    NEAR_END = "near_end"
    OUT = "out"
    UNKNOWN = "unknown"


class PrinterStatus(Frozen):
    online: bool | None
    paper: PaperState
    cover_open: bool | None
    error: str | None = None


class Printer(Protocol):
    async def execute(self, plan: PrintPlan) -> Path | None: ...

    async def status(self) -> PrinterStatus: ...

    async def close(self) -> None: ...
