# tests

Mirrors `src/printbot`. Folders containing only `.placeholder` belong to domains that are not built yet.

- `test_source_rules.py` fails on any comment or docstring in `src`
- `fixtures/` will hold sample PDFs, images and HTML for converter tests
- `jobs/` covers state transitions, service behavior, failure mapping, and serial printing
- `storage/` uses a temporary SQLite database for persistence, deduplication, and claims
- `app/test_text_flow.py` exercises Telegram submission through fake PNG output
- USB hardware tests carry the `hardware` marker and stay out of `just check` unless explicitly
  enabled
