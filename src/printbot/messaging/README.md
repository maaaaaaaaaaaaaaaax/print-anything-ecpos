# messaging

Telegram front end built on aiogram 3. Never imports `storage`.

## Current implementation

`AllowlistMiddleware` runs at the dispatcher update boundary. It drops updates without an
allowlisted user before any handler runs. The message router acknowledges `/start` with
`Printbot is ready.` and plain text with `Message received.`.

The package has no storage, job, or printer dependencies. Ingestion, settings and callback
routers, plus the job notifier, remain planned.
