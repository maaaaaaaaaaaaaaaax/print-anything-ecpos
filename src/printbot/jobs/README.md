# jobs

Job lifecycle: model, state machine, repository and notifier ports, conversion and print workers. Depends on `kernel`, `ingest`, `formatting` and `printing`.

## Current implementation

`JobService` validates and submits `NewJob` values. `JobRepository` and `Notifier` are ports owned by
this package. Jobs use `RECEIVED -> CONVERTING -> READY -> PRINTING -> DONE`; conversion and printer
errors move the job to `FAILED`.

The conversion worker claims one received job, converts its source, plans it for the configured
profile, and stores the document and estimated length. The print worker is the only print executor.
It claims ready jobs in repository order and holds an execution lock while sending each plan to the
printer, so prints do not overlap.

Repository transitions are compare-and-set. Telegram update IDs prevent duplicate submission.
Notifier transport failures are contained by the messaging adapter and do not interrupt job work.

## Planned

Bounded conversion concurrency, cancellation, confirmation, retries, and crash recovery.
