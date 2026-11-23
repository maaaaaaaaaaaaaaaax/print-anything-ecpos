import asyncio
import contextlib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import assert_never

from escpos.escpos import Escpos
from escpos.exceptions import Error as EscposError
from escpos.printer import Usb

from printbot.kernel import (
    CutOp,
    FeedOp,
    PrinterProfile,
    PrintOp,
    PrintPlan,
    QrOp,
    RasterOp,
    TextOp,
    TextStyle,
)
from printbot.printing.errors import (
    PrinterClosedError,
    PrinterConnectionError,
    PrinterExecutionError,
)
from printbot.printing.ports import PaperState, PrinterStatus
from printbot.printing.status_codes import (
    QUERY_OFFLINE_CAUSE,
    QUERY_ONLINE,
    QUERY_PAPER,
    parse_cover_open,
    parse_online,
    parse_paper,
)

DeviceFactory = Callable[[], Escpos]

DEFAULT_USB_TIMEOUT_MS = 30_000

_DEVICE_ERRORS = (EscposError, OSError)


def usb_device_factory(
    profile: PrinterProfile, timeout_ms: int = DEFAULT_USB_TIMEOUT_MS
) -> DeviceFactory:
    def create() -> Escpos:
        return Usb(
            profile.usb.vendor,
            profile.usb.product,
            timeout=timeout_ms,
            profile=profile.escpos_profile,
        )

    return create


class EscposUsbPrinter:
    def __init__(self, device_factory: DeviceFactory) -> None:
        self._device_factory = device_factory
        self._device: Escpos | None = None
        self._closed = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="printer")

    async def execute(self, plan: PrintPlan) -> None:
        self._require_open()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._executor, self._execute_blocking, plan)

    async def status(self) -> PrinterStatus:
        self._require_open()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._status_blocking)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._executor, self._disconnect)
        self._executor.shutdown(wait=False)

    def _require_open(self) -> None:
        if self._closed:
            raise PrinterClosedError("printer is closed")

    def _execute_blocking(self, plan: PrintPlan) -> None:
        device = self._connection()
        try:
            for op in plan.ops:
                _run_op(device, op)
        except _DEVICE_ERRORS as error:
            self._disconnect()
            raise PrinterExecutionError(str(error)) from error

    def _status_blocking(self) -> PrinterStatus:
        try:
            device = self._connection()
            online = device.query_status(QUERY_ONLINE)
            paper = device.query_status(QUERY_PAPER)
            offline_cause = device.query_status(QUERY_OFFLINE_CAUSE)
        except PrinterConnectionError as error:
            return _unreachable(str(error))
        except _DEVICE_ERRORS as error:
            self._disconnect()
            return _unreachable(str(error))
        return PrinterStatus(
            online=parse_online(online),
            paper=parse_paper(paper),
            cover_open=parse_cover_open(offline_cause),
        )

    def _connection(self) -> Escpos:
        if self._device is None:
            try:
                self._device = self._device_factory()
            except _DEVICE_ERRORS as error:
                raise PrinterConnectionError(str(error)) from error
        return self._device

    def _disconnect(self) -> None:
        device, self._device = self._device, None
        if device is not None:
            with contextlib.suppress(*_DEVICE_ERRORS):
                device.close()


def _unreachable(message: str) -> PrinterStatus:
    return PrinterStatus(online=False, paper=PaperState.UNKNOWN, cover_open=None, error=message)


def _run_op(device: Escpos, op: PrintOp) -> None:
    match op:
        case TextOp(text=text, style=style):
            _apply_style(device, style)
            device.text(f"{text}\n")
            device.set_with_default()
        case RasterOp(image=image, centered=centered):
            device.image(
                image,
                high_density_vertical=True,
                high_density_horizontal=True,
                center=centered,
            )
        case QrOp(data=data, size=size, centered=centered):
            device.qr(data, size=size, center=centered)
        case FeedOp(lines=lines):
            device.ln(lines)
        case CutOp(mode=mode):
            device.cut(mode="FULL" if mode == "full" else "PART")
        case _:
            assert_never(op)


def _apply_style(device: Escpos, style: TextStyle) -> None:
    device.set_with_default(
        align=style.align,
        font=style.font,
        bold=style.bold,
        underline=1 if style.underline else 0,
        width=style.width,
        height=style.height,
        invert=style.invert,
        custom_size=style.width != 1 or style.height != 1,
    )
