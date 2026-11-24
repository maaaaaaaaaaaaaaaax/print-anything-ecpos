from pathlib import Path

import pytest
from PIL import Image

from printbot.formatting import plan_text
from printbot.kernel import Document, Paragraph, Run
from printbot.printing import (
    FakePrinter,
    PaperState,
    PrinterExecutionError,
    load_bundled_profile,
)


async def test_fake_printer_records_plan_and_renders_png(tmp_path: Path) -> None:
    profile = load_bundled_profile("tm_t88iv")
    printer = FakePrinter(profile, tmp_path)
    plan = plan_text(
        Document(blocks=(Paragraph(runs=(Run(text="hello " * 20),)),)),
        profile,
    )

    output = await printer.execute(plan)

    assert printer.plans == (plan,)
    assert len(printer.saved_paths) == 1
    assert output == printer.saved_paths[0]
    with Image.open(printer.saved_paths[0]) as image:
        assert image.width == profile.print_width_dots
        assert image.height > 0
        assert image.format == "PNG"


async def test_fake_printer_renders_raster_fallback(tmp_path: Path) -> None:
    profile = load_bundled_profile("tm_t88iv")
    printer = FakePrinter(profile, tmp_path)
    plan = plan_text(
        Document(blocks=(Paragraph(runs=(Run(text="hello \U0001f642"),)),)),
        profile,
    )

    await printer.execute(plan)

    assert printer.saved_paths[0].exists()
    status = await printer.status()
    assert status.online is True
    assert status.paper is PaperState.OK


async def test_fake_printer_reports_output_failure(tmp_path: Path) -> None:
    blocked_directory = tmp_path / "not-a-directory"
    blocked_directory.write_text("blocked", encoding="ascii")
    profile = load_bundled_profile("tm_t88iv")
    printer = FakePrinter(profile, blocked_directory)
    plan = plan_text(
        Document(blocks=(Paragraph(runs=(Run(text="hello"),)),)),
        profile,
    )

    with pytest.raises(PrinterExecutionError, match="cannot write fake print"):
        await printer.execute(plan)
