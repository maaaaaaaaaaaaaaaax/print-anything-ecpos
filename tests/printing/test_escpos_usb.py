from collections.abc import Callable

import pytest
from escpos.escpos import Escpos
from escpos.exceptions import USBNotFoundError
from escpos.printer import Dummy
from PIL import Image

from printbot.kernel import CutOp, FeedOp, PrintPlan, QrOp, RasterOp, TextOp, TextStyle
from printbot.printing import (
    DEFAULT_USB_TIMEOUT_MS,
    EscposUsbPrinter,
    PaperState,
    PrinterClosedError,
    PrinterConnectionError,
    PrinterExecutionError,
    load_bundled_profile,
    usb_device_factory,
)

PROFILE = "TM-T88IV"


class ScriptedDummy(Dummy):
    def __init__(self, replies: dict[bytes, bytes] | None = None) -> None:
        super().__init__(profile=PROFILE)
        self._replies = replies or {}
        self._last_query = b""
        self.closed = False

    def _raw(self, msg: bytes) -> None:
        self._last_query = msg
        super()._raw(msg)

    def _read(self) -> bytes:
        return self._replies.get(self._last_query, b"")

    def close(self) -> None:
        self.closed = True


class BrokenDummy(ScriptedDummy):
    def text(self, txt: str) -> None:
        raise OSError(f"usb pipe broke after {len(txt)} characters")


def plan(*ops: TextOp | RasterOp | QrOp | FeedOp | CutOp) -> PrintPlan:
    return PrintPlan(ops=ops, length_mm=0)


def factory_of(device: Escpos) -> Callable[[], Escpos]:
    return lambda: device


def output_of(device: Dummy) -> bytes:
    return bytes(device.output)


async def test_text_op_prints_text_with_line_feed() -> None:
    device = ScriptedDummy()
    printer = EscposUsbPrinter(factory_of(device))
    await printer.execute(plan(TextOp(text="Grüße")))
    assert b"\n" in output_of(device)
    assert output_of(device).count(b"\n") >= 1
    await printer.close()


async def test_text_style_is_reset_after_each_text_op() -> None:
    device = ScriptedDummy()
    printer = EscposUsbPrinter(factory_of(device))
    styled = TextOp(text="big", style=TextStyle(bold=True, width=2, height=2, align="center"))
    await printer.execute(plan(styled, TextOp(text="plain")))
    output = output_of(device)
    assert b"\x1b\x61\x01" in output
    assert output.rstrip(b"\n").count(b"\x1b\x61\x00") >= 1
    await printer.close()


async def test_raster_op_sends_a_raster_image() -> None:
    device = ScriptedDummy()
    printer = EscposUsbPrinter(factory_of(device))
    image = Image.new("1", (64, 16), 0)
    await printer.execute(plan(RasterOp(image=image)))
    assert b"\x1dv0" in output_of(device)
    await printer.close()


async def test_cut_op_sends_cut_command() -> None:
    device = ScriptedDummy()
    printer = EscposUsbPrinter(factory_of(device))
    await printer.execute(plan(FeedOp(lines=2), CutOp()))
    assert b"\x1dV" in output_of(device)
    await printer.close()


async def test_qr_op_prints_something() -> None:
    device = ScriptedDummy()
    printer = EscposUsbPrinter(factory_of(device))
    await printer.execute(plan(QrOp(data="https://example.com")))
    assert len(output_of(device)) > 0
    await printer.close()


async def test_connection_failure_is_typed_and_retried_on_next_call() -> None:
    attempts: list[int] = []
    device = ScriptedDummy()

    def flaky() -> Escpos:
        attempts.append(1)
        if len(attempts) == 1:
            raise USBNotFoundError("no printer")
        return device

    printer = EscposUsbPrinter(flaky)
    with pytest.raises(PrinterConnectionError, match="no printer"):
        await printer.execute(plan(TextOp(text="x")))
    await printer.execute(plan(TextOp(text="x")))
    assert len(attempts) == 2
    assert len(output_of(device)) > 0
    await printer.close()


async def test_missing_usb_library_is_reported_as_connection_failure() -> None:
    def missing_usb() -> Escpos:
        raise RuntimeError("Printing with USB connection requires a usb library")

    printer = EscposUsbPrinter(missing_usb)

    with pytest.raises(PrinterConnectionError, match="usb library"):
        await printer.execute(plan(TextOp(text="x")))

    await printer.close()


async def test_execution_failure_is_typed_and_drops_the_connection() -> None:
    devices: list[ScriptedDummy] = [BrokenDummy(), ScriptedDummy()]

    def factory() -> Escpos:
        return devices.pop(0)

    printer = EscposUsbPrinter(factory)
    with pytest.raises(PrinterExecutionError, match="usb pipe broke"):
        await printer.execute(plan(TextOp(text="x")))
    await printer.execute(plan(TextOp(text="y")))
    assert not devices
    await printer.close()


async def test_status_parses_replies() -> None:
    device = ScriptedDummy(
        {
            b"\x10\x04\x01": b"\x12",
            b"\x10\x04\x04": b"\x1e",
            b"\x10\x04\x02": b"\x16",
        }
    )
    printer = EscposUsbPrinter(factory_of(device))
    status = await printer.status()
    assert status.online is True
    assert status.paper is PaperState.NEAR_END
    assert status.cover_open is True
    assert status.error is None
    await printer.close()


async def test_status_without_replies_reports_unknown_not_healthy() -> None:
    printer = EscposUsbPrinter(factory_of(ScriptedDummy()))
    status = await printer.status()
    assert status.online is None
    assert status.paper is PaperState.UNKNOWN
    assert status.cover_open is None
    await printer.close()


async def test_status_reports_unreachable_printer() -> None:
    def missing() -> Escpos:
        raise USBNotFoundError("unplugged")

    printer = EscposUsbPrinter(missing)
    status = await printer.status()
    assert status.online is False
    assert status.paper is PaperState.UNKNOWN
    assert status.error is not None
    assert "unplugged" in status.error
    await printer.close()


async def test_close_closes_the_device() -> None:
    device = ScriptedDummy()
    printer = EscposUsbPrinter(factory_of(device))
    await printer.execute(plan(TextOp(text="x")))
    await printer.close()
    assert device.closed


async def test_close_is_idempotent() -> None:
    printer = EscposUsbPrinter(factory_of(ScriptedDummy()))
    await printer.close()
    await printer.close()


async def test_use_after_close_raises_a_typed_error() -> None:
    printer = EscposUsbPrinter(factory_of(ScriptedDummy()))
    await printer.close()
    with pytest.raises(PrinterClosedError):
        await printer.execute(plan(TextOp(text="x")))
    with pytest.raises(PrinterClosedError):
        await printer.status()


def test_usb_factory_applies_a_finite_timeout_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_usb(*args: object, **kwargs: object) -> Escpos:
        calls.append((args, kwargs))
        return ScriptedDummy()

    monkeypatch.setattr("printbot.printing.escpos_usb.Usb", fake_usb)
    profile = load_bundled_profile("tm_t88iv")
    usb_device_factory(profile)()
    usb_device_factory(profile, timeout_ms=5_000)()
    assert calls[0] == (
        (0x04B8, 0x0202),
        {"timeout": DEFAULT_USB_TIMEOUT_MS, "profile": "TM-T88IV"},
    )
    assert DEFAULT_USB_TIMEOUT_MS > 0
    assert calls[1][1]["timeout"] == 5_000
