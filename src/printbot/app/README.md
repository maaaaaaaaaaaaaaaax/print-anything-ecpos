# app

Composition root. The only package that knows concrete classes and may import everything.

## Current implementation

`Config` reads `TELEGRAM_TOKEN` and a comma-separated `ALLOWED_USER_IDS` list from the
environment. The runtime constructs the aiogram bot, dispatcher, allowlist middleware, and
message router, then starts long polling. The bot session is closed when polling exits or fails.

Copy `.env.example` to `.env`, replace its placeholder values, then run:

```sh
cp .env.example .env
uv run printbot
```

Multiple user IDs are comma-separated. Keep Telegram credentials in `.env`, the process
environment, or a secret manager, never in source control.

Printer, repository, and worker composition remains planned.
