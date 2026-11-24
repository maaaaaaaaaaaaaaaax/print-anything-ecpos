# app

Composition root. The only package that knows concrete classes and may import everything.

## Current implementation

`Config` reads `TELEGRAM_TOKEN`, comma-separated `ALLOWED_USER_IDS`, `DATA_DIR`,
`MIGRATIONS_DIRECTORY`, `PRINTER_BACKEND`, and `PRINTER_PROFILE`. The backend defaults to `fake`;
`usb` constructs the configured python-escpos adapter.

The runtime initializes SQLite, selects the printer, wires the plain-text converter, planner,
notifier, job service, and workers, then starts long polling under one task group. One conversion
worker and one print worker run with the dispatcher. Printer, database, and bot resources are
closed when polling exits or fails.

Copy `.env.example` to `.env`, replace its placeholder values, then run:

```sh
cp .env.example .env
uv run printbot
```

Multiple user IDs are comma-separated. Keep Telegram credentials in `.env`, the process
environment, or a secret manager, never in source control.

With the fake backend, output is written to `DATA_DIR/prints/print-NNNN.png` and jobs are stored in
`DATA_DIR/jobs.sqlite3`. Select a bundled profile with `PRINTER_PROFILE`; `tm_t88v` is the default.

Status polling, settings, crash recovery, bounded conversion concurrency, and deployment remain
planned.
