# messaging

Telegram front end built on aiogram 3. Never imports `storage`.

## Current implementation

`AllowlistMiddleware` runs at the dispatcher update boundary. It drops updates without an
allowlisted user before any handler runs. The message router acknowledges `/start` with
`Printbot is ready.`. A plain text message is submitted with its chat and Telegram update IDs and
receives `Queued for printing.` once. Duplicate updates receive no second acknowledgement.

`TelegramNotifier` reports conversion, ready, printing, printed, and failure states. Telegram API
errors are logged without stopping job processing. The package depends on job ports and never
imports storage or concrete printer code.

URL, document, image, settings, command, and callback routers remain planned.
