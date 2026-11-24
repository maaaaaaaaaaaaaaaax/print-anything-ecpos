# Printbot Architecture Draft

*A Telegram-driven thermal print server on a Raspberry Pi 5. Working document for iteration with a coding agent.*

## 1. Goals and non-goals

**Goals**

- Send almost anything to a Telegram bot from iPhone or Mac and get a readable thermal printout.
- One entry point (Telegram), one Raspberry Pi, one repo, one process.
- Restart-safe job handling: no lost jobs, no duplicate prints, no interleaved output.
- Format behavior configurable from the chat.
- Printer and paper state reported back to the chat.

**Non-goals for v1**

- Speech to text (dropped for now, the design leaves a slot for it).
- Any entry point other than Telegram (agents, webhooks, web UI come later, if ever).
- Multi-user support. One allowed Telegram user ID.

## 2. Technology decisions

| Concern | Choice | Reason |
| --- | --- | --- |
| Language | Python 3.13, managed by uv | uv installs the interpreter, so the Pi OS Python version does not matter |
| Package and env | uv | Lockfile, fast, single tool |
| Lint and format | Ruff | One tool for both |
| Type checking | ty, strict as far as it allows | Requested. Fallback to mypy or pyright if ty blocks progress |
| Telegram | aiogram 3 | Fully typed, async, router and middleware model |
| Printing | python-escpos | Requested. Untyped, so wrapped behind one adapter |
| Models | pydantic v2 | Typed JSON round-tripping for the block IR and settings |
| Database | SQLite via aiosqlite, WAL mode | Single file, typed async wrapper, enough for this load |
| HTTP | httpx | Typed, async, timeouts by default |
| Tests | pytest, pytest-asyncio, syrupy (snapshots) | Golden tests for layout output |
| Architecture enforcement | import-linter | Makes the domain separation a failing check, not a convention |
| Task runner | just | `just check` runs everything |

**Hardware**: Raspberry Pi 5 (4 GB is enough), Raspberry Pi OS Lite 64-bit, printer over USB with its own power supply. The Pi 5 has headroom for Tesseract and LibreOffice, and for local speech later.

**Run anywhere**: the same code runs on the Mac with `PRINTER_BACKEND=fake`, which renders print plans to PNG files. Most development never needs the hardware.

## Running the minimal bot

Install the locked environment, copy the environment template, and replace its placeholders:

```sh
uv sync
cp .env.example .env
uv run printbot
```

`ALLOWED_USER_IDS` is a comma-separated list of positive decimal Telegram user IDs. The bot responds to `/start` and plain text messages from allowlisted users. Other users' updates are ignored before routing. Plain text is persisted as a job, reported as queued, converted, laid out for the configured profile, and printed by the single print worker.

`PRINTER_BACKEND` is `fake` by default or `usb` for the configured printer. `PRINTER_PROFILE` selects a bundled profile such as `tm_t88v`. Fake output is uploaded to Telegram as a PNG document and deleted locally after a successful upload; it is not retained on disk. The SQLite database is stored at `DATA_DIR/jobs.sqlite3`. Set `DATA_DIR` to a writable persistent directory on the Pi.

For multiple allowed users, separate IDs with commas, for example `ALLOWED_USER_IDS=123456,789012`.
The actual `.env` file is ignored by Git. Keep `TELEGRAM_TOKEN` in `.env`, the process
environment, or a secret manager. Never commit it.

## 3. System overview

```
Telegram (iPhone / Mac)
   |  long polling, user-ID whitelist
   v
messaging  --- submits ---> jobs service ---> SQLite (text jobs)
   ^                            |
   |                            +--> conversion stage
   |                            |        ingest: plain text -> blocks (JSON)
   |                            |
   |                            +--> print stage (single worker, serial)
   |                                     formatting: blocks + profile -> PrintPlan
   |                                     printing: PrintPlan -> ESC/POS -> USB
   |                                               
   +---- Notifier <---- job lifecycle updates
```

The current vertical slice handles plain text. The central idea is a **block intermediate representation** (IR): each converter emits blocks, formatting turns them into a print plan, and one printer adapter executes the plan. Confirmation, settings, paper state, and other source types remain planned.

## 4. Repository layout

```
printbot/
  pyproject.toml
  justfile
  AGENTS.md
  deploy/
    printbot.service
    99-printer.rules
    install.md
  migrations/
    0001_initial.sql
  src/printbot/
    kernel/        shared value types, no behavior beyond validation
    ingest/        detection and converters
    formatting/    settings registry, config resolution, layout, length estimate
    printing/      printer port, ESC/POS adapter, fake printer, status, paper ledger port
    jobs/          job model, state machine, repository port, service, workers
    storage/       SQLite implementations of repository ports, migration runner
    messaging/     aiogram handlers, auth, keyboards, notifier implementation
    app/           settings from env, composition root, entrypoint
  tests/
    kernel/ ingest/ formatting/ printing/ jobs/ storage/ messaging/
    fixtures/      sample PDFs, images, HTML, expected snapshots
```

### Dependency rules (enforced by import-linter)

```toml
[tool.importlinter]
root_package = "printbot"

[[tool.importlinter.contracts]]
name = "Layered architecture"
type = "layers"
layers = [
  "printbot.app",
  "printbot.messaging | printbot.storage",
  "printbot.jobs",
  "printbot.ingest | printbot.formatting | printbot.printing",
  "printbot.kernel",
]
```

In words:

- `kernel` imports nothing from the project.
- `ingest`, `formatting` and `printing` depend only on `kernel` and never on each other.
- `jobs` orchestrates the three above and owns the job model.
- `storage` and `messaging` implement ports defined lower down and never import each other.
- `app` wires everything and is the only place that knows concrete classes.

Ports live with their consumer. `jobs` defines `JobRepository` and `Notifier`. `formatting` defines `SettingsStore`. `printing` defines `Printer` and `PaperLedger`. `storage` and `messaging` implement them.

## 5. Domains

### 5.1 kernel

Shared immutable value types.

```python
from typing import Annotated, Literal, NewType

from pydantic import BaseModel, ConfigDict, Field

AssetId = NewType("AssetId", str)


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Run(Frozen):
    text: str
    bold: bool = False
    italic: bool = False


class Heading(Frozen):
    kind: Literal["heading"] = "heading"
    level: int = Field(ge=1, le=3)
    text: str


class Paragraph(Frozen):
    kind: Literal["paragraph"] = "paragraph"
    runs: tuple[Run, ...]


class CodeBlock(Frozen):
    kind: Literal["code"] = "code"
    text: str
    language: str | None = None


class ChecklistItem(Frozen):
    kind: Literal["checklist_item"] = "checklist_item"
    text: str
    checked: bool = False


class ListItem(Frozen):
    kind: Literal["list_item"] = "list_item"
    runs: tuple[Run, ...]
    depth: int = 0


class Quote(Frozen):
    kind: Literal["quote"] = "quote"
    runs: tuple[Run, ...]


class ImageBlock(Frozen):
    kind: Literal["image"] = "image"
    asset: AssetId


class QrBlock(Frozen):
    kind: Literal["qr"] = "qr"
    data: str
    caption: str | None = None


class Rule(Frozen):
    kind: Literal["rule"] = "rule"


class Provenance(Frozen):
    kind: Literal["provenance"] = "provenance"
    label: str
    origin_url: str | None = None
    received_at: int


Block = Annotated[
    Heading
    | Paragraph
    | CodeBlock
    | ChecklistItem
    | ListItem
    | Quote
    | ImageBlock
    | QrBlock
    | Rule
    | Provenance,
    Field(discriminator="kind"),
]


class Document(Frozen):
    blocks: tuple[Block, ...]
```

Also in kernel: `MediaType` (enum of recognized types), `Source` (union of `TextSource`, `UrlSource`, `FileSource`), `JobOptions` (typed per-job overrides parsed from the caption), `ChatId`, `JobId`.

Images are never embedded in the IR. They are stored as content-addressed assets (sha256 file names under the data directory) and referenced by `AssetId`.

### 5.2 ingest

Turns a `Source` into a `Document`.

```python
class Converter(Protocol):
    def accepts(self, source: Source) -> bool: ...

    async def convert(self, source: Source, options: JobOptions) -> Conversion: ...


class Conversion(Frozen):
    document: Document
    assets: tuple[NewAsset, ...] = ()
```

A `ConverterRegistry` holds an ordered list and picks the first converter whose `accepts` returns true. Detection uses python-magic on file content, never the extension alone.

| Converter | Input | Method |
| --- | --- | --- |
| `PlainTextConverter` | text, .txt | Direct to blocks |
| `MarkdownConverter` | markdown | markdown-it-py tokens to blocks, `- [ ]` becomes `ChecklistItem` |
| `CodeFileConverter` | source files, diffs | Filename header plus `CodeBlock` |
| `UrlConverter` | URL | httpx fetch with size and time caps, trafilatura extraction, then markdown path |
| `ImageConverter` | png, jpg, heic, webp | Asset plus `ImageBlock`, or OCR text when `ocr` option is set |
| `PdfConverter` | pdf | `pdftotext -layout`, falls back to `pdftoppm` plus Tesseract when little text is found, honors page ranges |
| `OfficeConverter` | docx, odt, pptx, xlsx | `soffice --headless --convert-to pdf`, then the PDF path |
| `ReceiptFallbackConverter` | anything else | Short receipt: filename, size, type, hash |

Heavy tools run through a `ProcessRunner` port: async subprocess, hard timeout, output size cap, memory limit, kill on timeout. A hung LibreOffice must fail one job, not the bot.

Every converted document gets a `Provenance` block first (source label, original URL if any, timestamp). Whether it prints is a formatting setting.

A future speech converter (`VoiceConverter`) slots in as one more implementation of `Converter`.

### 5.3 formatting

Two responsibilities: resolve configuration, and turn a document into a print plan.

**Configuration layers**, merged in this order:

1. Defaults in code
2. Per-chat overrides from `settings` table
3. Per-job overrides from the caption (`JobOptions`)

```python
class FormatConfig(Frozen):
    paper_width_mm: Literal[58, 80] = 80
    dpi: int = 203
    cut: bool = True
    show_provenance: bool = True
    show_qr: bool = True
    code_font: Literal["a", "b"] = "b"
    dither: Literal["atkinson", "floyd_steinberg", "threshold"] = "atkinson"
    confirm_over_mm: int = 600
    ocr_languages: tuple[str, ...] = ("eng", "deu")
    margin_dots: int = 8
```

A **setting registry** defines each user-settable key exactly once: name, parser, validator, description. `/set`, `/settings`, `/reset` and the caption parser all read from it. No stringly-typed access anywhere else. Overrides are stored as `key -> string`, parsed into typed values at resolution time.

**Layout** is a pure function:

```python
def plan(document: Document, config: FormatConfig, assets: AssetStore) -> PrintPlan: ...
```

```python
class PrintPlan(Frozen):
    ops: tuple[PrintOp, ...]
    length_mm: float


PrintOp = TextOp | RasterOp | QrOp | FeedOp | CutOp
```

- Text blocks become wrapped, styled `TextOp` lines sized to the paper's characters per line.
- Images are resized to the printable width in dots and dithered into 1-bit `RasterOp`.
- Length is computed from the plan (line height times lines plus raster height over dots per mm), so the confirm gate needs no hardware.
- The text MVP uses CP858 as the native printer-safe character boundary. If any character cannot be encoded by CP858, the entire job is rasterized with the bundled Unicode font. Native and raster text are never mixed within one job.

Because the plan is pure data, layout is tested with no printer attached.

### 5.4 printing

```python
class Printer(Protocol):
    async def execute(self, plan: PrintPlan) -> None: ...

    async def status(self) -> PrinterStatus: ...


class PaperState(StrEnum):
    OK = "ok"
    NEAR_END = "near_end"
    OUT = "out"
    UNKNOWN = "unknown"


class PrinterStatus(Frozen):
    online: bool
    paper: PaperState
    cover_open: bool
    error: str | None = None
```

Implementations:

- `EscposUsbPrinter`: the only module that imports python-escpos. Executes ops, translates device errors into typed exceptions, reads real-time status where the printer answers.
- `FakePrinter`: records plans and renders them to PNG. Used in tests and on the Mac.

`PaperLedger` is a port plus a small service that tracks millimeters printed per roll. It gives a paper estimate even when the printer reports nothing, which is common on cheap models. `/newroll` resets it, and the bot warns near a configured roll length.

### 5.5 jobs

Owns the job lifecycle. Pure state machine, plus async workers.

The current text MVP uses the `RECEIVED -> CONVERTING -> READY -> PRINTING -> DONE` path, with `FAILED` reachable from conversion or printing. Confirmation, cancellation, interruption recovery, and retries remain future work.

```python
class JobStatus(StrEnum):
    RECEIVED = "received"
    CONVERTING = "converting"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    READY = "ready"
    PRINTING = "printing"
    DONE = "done"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    CANCELLED = "cancelled"


ALLOWED_TRANSITIONS: Mapping[JobStatus, frozenset[JobStatus]] = {
    JobStatus.RECEIVED: frozenset({JobStatus.CONVERTING, JobStatus.CANCELLED}),
    JobStatus.CONVERTING: frozenset(
        {JobStatus.READY, JobStatus.AWAITING_CONFIRMATION, JobStatus.FAILED, JobStatus.RECEIVED}
    ),
    JobStatus.AWAITING_CONFIRMATION: frozenset({JobStatus.READY, JobStatus.CANCELLED}),
    JobStatus.READY: frozenset({JobStatus.PRINTING, JobStatus.CANCELLED}),
    JobStatus.PRINTING: frozenset({JobStatus.DONE, JobStatus.FAILED, JobStatus.INTERRUPTED}),
    JobStatus.INTERRUPTED: frozenset({JobStatus.READY, JobStatus.CANCELLED}),
    JobStatus.FAILED: frozenset({JobStatus.RECEIVED, JobStatus.CANCELLED}),
    JobStatus.DONE: frozenset({JobStatus.READY}),
    JobStatus.CANCELLED: frozenset(),
}
```

Ports defined here:

```python
class JobRepository(Protocol):
    async def add(self, new: NewJob) -> Job | None: ...

    async def claim(self, source: JobStatus, target: JobStatus) -> Job | None: ...

    async def transition(
        self, job_id: JobId, expected: JobStatus, target: JobStatus, patch: JobPatch
    ) -> Job | None: ...

    async def recover_after_crash(self) -> tuple[Job, ...]: ...


class Notifier(Protocol):
    async def job_updated(self, job: Job) -> None: ...

    async def confirmation_needed(self, job: Job) -> None: ...

    async def printer_alert(self, status: PrinterStatus) -> None: ...
```

**Two stages, one printer.**

- The text conversion worker claims `RECEIVED`, converts plain text to blocks, stores the document, computes the estimated length, and moves to `READY`.
- Print stage: exactly one worker. It claims `READY` in creation order, runs layout, executes on the printer, and marks `DONE`.

For the current text-only path, this guarantees that prints never interleave.

**Rules**

- Transitions are compare-and-set (`expected` status must match). A lost race returns `None`, never corrupts state.
- The resolved `FormatConfig` is snapshotted on the job. A `/set` after queuing does not change queued jobs, and reprints are reproducible.
- Blocks are stored on the job, so reprint skips conversion entirely.
- `tg_update_id` is unique, so Telegram redelivery cannot create duplicate jobs.
- Crash recovery at startup: `CONVERTING` returns to `RECEIVED` (conversion is idempotent), `PRINTING` becomes `INTERRUPTED` and the bot asks whether to reprint (half a receipt is a human decision), `READY` stays.
- Printer offline or out of paper: the print worker pauses, the notifier alerts once, and jobs wait in `READY`. Nothing is dropped.

### 5.6 storage

The current `SQLiteJobRepository` persists text jobs, and a migration runner applies numbered SQL files in order and records the applied version. `SettingsStore`, `PaperLedger`, and the asset index remain planned.

```sql
CREATE TABLE jobs (
  id INTEGER PRIMARY KEY,
  chat_id INTEGER NOT NULL,
  telegram_update_id INTEGER NOT NULL UNIQUE,
  source_json TEXT NOT NULL,
  document_json TEXT,
  status TEXT NOT NULL,
  estimated_length_mm REAL,
  error TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);

CREATE INDEX jobs_status_created_at ON jobs (status, created_at, id);

CREATE TABLE settings (
  chat_id INTEGER NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (chat_id, key)
);

CREATE TABLE assets (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  media_type TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE paper_rolls (
  id INTEGER PRIMARY KEY,
  started_at INTEGER NOT NULL,
  roll_length_mm INTEGER NOT NULL,
  printed_mm REAL NOT NULL DEFAULT 0
);
```

SQLite runs in WAL mode with `busy_timeout`. Telegram update IDs are unique, claims use an immediate transaction and creation order, and stale compare-and-set transitions do not mutate jobs. Retention remains planned.

### 5.7 messaging

The implemented foundation uses aiogram 3 with one message router and one update-level middleware.

- **Auth middleware**: drops every update whose user ID is not in the whitelist, before any handler runs.
- **Message router**: acknowledges `/start`; plain text is submitted with the Telegram update ID and receives "Queued for printing."
- **Notifier**: reports conversion, ready, printing, success, and failure messages for each job.

The following messaging features remain planned:

- **Ingest router**: URLs, documents, photos, and forwarded messages. Downloads files into a temp area, builds a `Source`, and parses captions into `JobOptions`.
- **Command router**: `/settings`, `/set key value`, `/reset`, `/status`, `/queue`, `/cancel`, `/reprint`, `/newroll`, `/help`.
- **Callback router**: Print and Cancel buttons from the confirm gate, and reprint or discard for interrupted jobs.

`TelegramNotifier` implements `Notifier` by sending a short lifecycle message for each transition.

Caption syntax: plain tokens such as `ocr`, `img`, `pages 1-3`, `copies 2`, or `key=value` for any registry setting. Parsed into `JobOptions` using the same registry as `/set`.

Telegram specifics to handle: photos sent as photos are compressed (prefer sending as file for OCR), the standard Bot API download limit is 20 MB, and a bare URL message routes to `UrlConverter`.

### 5.8 app

`Config` uses pydantic-settings to read Telegram credentials and runtime paths plus `PRINTER_BACKEND` and `PRINTER_PROFILE`. The composition root opens SQLite, selects the fake or USB printer, wires the converter, planner, one print worker, notifier, middleware, and handlers, and runs polling under an `asyncio.TaskGroup`. Printer and repository resources close when polling exits.

Printer status polling, alerts, logging configuration, and deployment remain planned. Composition is injected with no globals or service locators.

## 6. Cross-cutting rules

- **No comments, no docstrings.** Names and types carry the meaning. Commented-out code is banned (Ruff `ERA`).
- **Type safety.** Full annotations everywhere. No `Any` outside the python-escpos adapter. Pydantic models and frozen dataclasses for data, `Protocol` for ports, `StrEnum` for closed sets.
- **Immutability by default.** Value types are frozen. State changes only through repositories.
- **Errors.** Domain-specific exception classes per package. Converters raise typed errors that the job service maps to `FAILED` with a readable message for the chat.
- **Time and IDs.** A `Clock` protocol is injected, so tests control time.
- **Logging.** Standard library logging to journald, one line per state transition with job ID.
- **Small modules.** One concept per file, public surface re-exported from each package `__init__`.

## 7. Quality gates

`just check` runs, in order: `ruff format --check`, `ruff check`, `ty check`, `lint-imports`, `pytest`.

- **Layout snapshot tests**: document in, plan out, compared with stored snapshots.
- **Converter tests**: fixtures for each format, asserting on blocks.
- **Repository tests**: real SQLite in a temp directory, covering compare-and-set races, crash recovery and duplicate update IDs.
- **State machine tests**: every allowed transition accepted, every other rejected.
- **Worker tests**: fake printer and fake notifier, covering printer-offline pause and resume.
- **Hardware tests**: marked `hardware`, excluded from `just check`, run manually on the Pi.

## 8. Deployment on the Pi 5

- OS packages: `tesseract-ocr` (with `eng`, `deu`), `poppler-utils`, `libreoffice-writer`, `libreoffice-impress`, `libreoffice-calc`, `libmagic1`, and a fonts package with decent Unicode coverage.
- A udev rule grants the service user access to the printer by vendor and product ID.
- A systemd unit runs `uv run printbot` with `EnvironmentFile` for secrets, `Restart=always`, and `MemoryMax` as a backstop against runaway conversions.
- Update flow: `git pull`, `uv sync --frozen`, `systemctl restart printbot`. A `just deploy` recipe wraps it.
- The SQLite file and fake-printer output live under `DATA_DIR`, on SSD or a quality SD card.

## 9. Build plan

Each phase ends with `just check` green and a short demo.

1. **Skeleton.** uv project, Ruff, ty, import-linter contracts, pytest, justfile, AGENTS.md. App boots and exits cleanly. Kernel types and the state machine with tests.
2. **Vertical slice on the fake printer.** Implemented: text message to job row to blocks to plan to PNG, with Telegram replies, whitelist enforcement, migrations, repository, and serial print worker.
3. **Real printer.** Implemented adapter and hardware smoke path; hardware legibility still needs validation on the connected printer.
4. **Format engine.** Setting registry, `/set`, `/settings`, `/reset`, caption overrides, config snapshots.
5. **Markdown and URLs.** Markdown converter with checklists, trafilatura pipeline, provenance header and QR.
6. **Images.** Asset store, dithering, `ocr` option.
7. **PDF and OCR.** Text-layer path, scanned fallback, page ranges.
8. **Operations.** Confirm gate, paper ledger, `/newroll`, status poller and alerts, crash recovery, retention task.
9. **Office formats.** LibreOffice conversion through the PDF path.
10. **Later.** Inline intent buttons for ambiguous images, speech converter, reprint history browser, an agent entry point.

## 10. Risks and open questions

- **Printer model and paper width** are not yet decided. They determine code page handling, whether real-time status works, and dots per line. Needed before phase 3.
- **ty maturity.** Expect gaps. If it blocks real progress, switch the checker, keep the typing discipline.
- **python-escpos is untyped.** Contained in one adapter. Do not let its types leak.
- **Encoding on cheap printers** is the most likely source of ugly output (umlauts, typographic quotes). Decide the transliterate-or-rasterize policy early and cover it with tests.
- **Telegram is not end-to-end encrypted.** Fine for articles, think twice for private code reviews. The whitelist limits who can send, not who can read at Telegram.
- **Thermal paper fades** over time. Printouts are working scratch paper, not archives.
- **Open**: OCR languages beyond English and German? Retention period for assets? Default paper width?

## 11. AGENTS.md (starting content)

- Read this document before changing structure. Propose architecture changes before implementing them.
- Never write comments or docstrings. Make names and types do the work.
- All code is fully type annotated and passes `ty`. Do not use `Any` outside `printing/escpos_usb.py`.
- Respect the layer contracts in `pyproject.toml`. If a change needs a forbidden import, introduce a port instead.
- Domain logic is pure where possible: layout, state transitions and config resolution take values and return values.
- Every behavior change comes with a test. Run `just check` before finishing any task.
- Work one build-plan phase at a time and stop at its acceptance criteria.
