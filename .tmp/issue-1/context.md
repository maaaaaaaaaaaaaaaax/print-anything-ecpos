# Task: 1. Verify the first real USB printer
Issue: 1 (maaaaaaaaaaaaaaaax/print-anything-ecpos), labels: none

Goal

Validate the existing EscposUsbPrinter adapter and one bundled profile against the actual printer before building the Telegram-to-print flow. The README calls out the printer model, code-page behavior, status replies, USB endpoints, and timeout as unverified risks.

Scope

 - Record the printer make/model, paper width, USB vendor/product IDs, host OS, and selected profile.
 - Run a repeatable hardware smoke test using the existing adapter.
 - Add a hardware-marked test or documented manual test procedure; hardware checks must not run as part of the default just check suite.

Acceptance criteria

 - The selected bundled profile matches the connected printer and loads successfully.
 - A test receipt prints legible Font A and Font B text, including umlauts, curly quotes, and the euro sign; record any encoding limitations.
 - Verify alignment, line width, and cut behavior where supported.
 - Query online, cover, and paper status; document if the printer does not support or respond to status queries rather than treating an empty reply as healthy.
 - Verify the adapter’s USB endpoints and timeout on this device; record any required adjustment.
 - The test procedure states the required hardware/setup and the observed results.

Out of scope

Telegram, job processing, storage, formatting configuration, and support for additional printer models.
