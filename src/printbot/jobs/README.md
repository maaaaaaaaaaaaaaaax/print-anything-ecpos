# jobs

Job lifecycle: model, state machine, repository and notifier ports, conversion and print workers. Depends on `kernel`, `ingest`, `formatting` and `printing`.

## Planned

Job status transitions as compare-and-set, one conversion stage with bounded concurrency, exactly one print worker, crash recovery at startup, confirm gate for long output.

This package is empty. The `.placeholder` file marks it as not yet built.
