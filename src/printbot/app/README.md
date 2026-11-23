# app

Composition root. The only package that knows concrete classes and may import everything.

## Current implementation

`Config` reads `TELEGRAM_TOKEN` and a comma-separated `ALLOWED_USER_IDS` list from the
environment. The runtime constructs the aiogram bot, dispatcher, allowlist middleware, and
message router, then starts long polling. The bot session is closed when polling exits or fails.

Run the bot with:

```sh
TELEGRAM_TOKEN=... ALLOWED_USER_IDS=123456 uv run printbot
```

Keep Telegram credentials in the environment or a secret manager, never in source control.

Printer, repository, and worker composition remains planned.
