# printing

Talks to the printer. Depends on `kernel` only. `escpos` is imported only in `escpos_usb.py`, which an import-linter contract enforces.

## Contents

| Module | Purpose |
| --- | --- |
| `ports.py` | `Printer` protocol, `PrinterStatus`, `PaperState` |
| `escpos_usb.py` | `EscposUsbPrinter`: executes a `PrintPlan` through python-escpos |
| `fake.py` | `FakePrinter`: records plans and writes PNG output without hardware |
| `status_codes.py` | Pure parsers for the real-time status replies |
| `profile_loader.py` | Loads and validates YAML profiles into `PrinterProfile` |
| `errors.py` | `PrinterError`, `PrinterConnectionError`, `PrinterExecutionError`, `ProfileError` |
| `profiles/` | `tm_t88iv.yaml`, `tm_t88v.yaml` |

## How the adapter behaves

- All device access runs on one dedicated worker thread, so a status poll and a print job can never touch USB at the same time.
- The connection opens lazily and is dropped on any device error. The next call reconnects.
- The device comes from an injected factory. `usb_device_factory(profile)` builds the real one. Tests use python-escpos's `Dummy`.
- Text styles are set fully before each text op and reset afterwards, so alignment and size never leak into images or QR codes.
- USB writes use a finite timeout, `DEFAULT_USB_TIMEOUT_MS` (30 s). python-escpos defaults to no timeout, and a stalled printer would block the worker thread forever. The value must exceed the time one raster fragment needs, so tune it on the real unit.
- `close()` is idempotent. After it, `execute()` and `status()` raise `PrinterClosedError`.
- Cancelling a task that awaits `execute()` does not stop a print already running on the worker thread. Callers must treat a cancelled `execute()` as possibly printed.
- A printer that sends no status reply reports `UNKNOWN`, not healthy. python-escpos's own `paper_status()` returns "adequate" for an empty reply, so it is deliberately not used.
- `FakePrinter` serializes writes, stores completed plans, and reports output filesystem failures as `PrinterExecutionError`.

## Profiles

TM-T88IV and TM-T88V: 180 dpi, 512 dot print width on 80 mm paper, Font A 42 columns (12 by 24), Font B 56 columns (9 by 17). USB IDs 04b8:0202 and 04b8:0e02.

These values come from python-escpos's capability data, not from a measurement on your unit.

## USB hardware verification

Run the smoke test on the Raspberry Pi with the printer connected and paper loaded:

```sh
PRINTBOT_HARDWARE_TEST=1 PRINTBOT_USB_PROFILE=tm_t88v uv run pytest -s tests/printing/test_usb_hardware.py
```

Set `PRINTBOT_USB_PROFILE` to `tm_t88iv` for that model. The bundled profiles describe Epson TM-T88V (04b8:0e02) and TM-T88IV (04b8:0202); confirm the printer's label and USB ID before selecting one. The test loads the profile, prints Font A and B samples, alignment samples, a 42-character line, then cuts, and queries online, paper, and cover status. Hardware checks are skipped by the default `just check`.

Record the printer make/model, paper width, USB ID, host OS, selected profile, legibility/encoding of umlauts, curly quotes and euro sign, line width/alignment, and cut result. The test prints its host, profile, ID, timeout, and status values; include the observations from the physical receipt. Status `None` or `unknown` is not proof of a healthy printer: record it as unsupported/unanswered and verify by inspection.

The adapter currently uses a 30-second USB timeout. python-escpos's USB backend uses endpoint IN `0x82` and OUT `0x01`. These are expected library defaults, not observations on a connected device; record whether the printer works with them and adjust only if the physical test shows a problem.

The fake backend writes numbered PNG files to its configured output directory. It renders native text
and raster operations at the selected profile width, reports healthy paper status, and requires no
USB access.
