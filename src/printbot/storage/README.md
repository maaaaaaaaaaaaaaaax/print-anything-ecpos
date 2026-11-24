# storage

SQLite implementations of the ports defined in `jobs` and `formatting`. Never imports `messaging`.

## Current implementation

`SQLiteJobRepository` stores the text MVP job lifecycle. It opens SQLite in WAL mode with a
five-second busy timeout, applies numbered migrations, persists JSON source and document values,
and returns immutable jobs. Duplicate Telegram update IDs are ignored.

Claims and transitions are serialized on the repository connection. Claims select the oldest
matching job and update it in one immediate transaction. Stale transitions return `None`.

## Planned

`SettingsStore`, asset storage, paper storage, crash recovery, and retention.
