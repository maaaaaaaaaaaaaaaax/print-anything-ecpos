# printing

Talks to the printer. Depends on `kernel` only. `escpos` is imported only in `escpos_usb.py`, which an import-linter contract enforces.

## Contents

| Module | Purpose |
| --- | --- |
| `ports.py` | `Printer` protocol, `PrinterStatus`, `PaperState` |
| `escpos_usb.py` | `EscposUsbPrinter`: executes a `PrintPlan` through python-escpos |
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

## Profiles

TM-T88IV and TM-T88V: 180 dpi, 512 dot print width on 80 mm paper, Font A 42 columns (12 by 24), Font B 56 columns (9 by 17). USB IDs 04b8:0202 and 04b8:0e02.

These values come from python-escpos's capability data, not from a measurement on your unit.

## Not verified without hardware

The command bytes and reply bit masks in `status_codes.py` follow the Epson real-time status commands but are tested only against scripted replies. Phase 3 checklist on the real printer:

- 42 and 56 columns in Font A and B
- umlauts, curly quotes, euro sign
- cut behavior
- near-end and out-of-paper replies, cover-open reply
- whether the unit answers status requests over USB at all
- the USB write timeout, and the endpoints python-escpos hard-codes (in `0x82`, out `0x01`)

## Planned

`fake.py`: `FakePrinter` that records plans and renders them to PNG for development without hardware.
