import asyncio
import os
import platform

import pytest

from printbot.kernel import CutOp, FeedOp, PrintPlan, TextOp, TextStyle
from printbot.printing import EscposUsbPrinter, load_bundled_profile, usb_device_factory
from printbot.printing.escpos_usb import DEFAULT_USB_TIMEOUT_MS

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        os.environ.get("PRINTBOT_HARDWARE_TEST") != "1",
        reason="set PRINTBOT_HARDWARE_TEST=1 to run the USB printer test",
    ),
]


def test_usb_printer_hardware_smoke() -> None:
    asyncio.run(_run_hardware_smoke())


async def _run_hardware_smoke() -> None:
    profile_name = os.environ["PRINTBOT_USB_PROFILE"]
    profile = load_bundled_profile(profile_name)
    printer = EscposUsbPrinter(usb_device_factory(profile))
    plan = PrintPlan(
        ops=(
            TextOp(text=f"Printer check: {profile.model}", style=TextStyle(align="center")),
            TextOp(text="Font A: ä ö ü Ä Ö Ü, “curly quotes”, €"),
            TextOp(
                text="Font B: ä ö ü Ä Ö Ü, “curly quotes”, €",
                style=TextStyle(font="b"),
            ),
            TextOp(text="Left aligned", style=TextStyle(align="left")),
            TextOp(text="Centered", style=TextStyle(align="center")),
            TextOp(text="Right aligned", style=TextStyle(align="right")),
            TextOp(text="012345678901234567890123456789012345678901"),
            FeedOp(lines=3),
            CutOp(mode="full"),
        ),
        length_mm=100,
    )
    try:
        await printer.execute(plan)
        status = await printer.status()
        print(
            f"Host OS: {platform.platform()}; profile: {profile_name} ({profile.model}); "
            f"USB ID: {profile.usb.vendor:04x}:{profile.usb.product:04x}; "
            f"timeout: {DEFAULT_USB_TIMEOUT_MS} ms; status: {status.model_dump()}"
        )
    finally:
        await printer.close()
