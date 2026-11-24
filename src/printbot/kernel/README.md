# kernel

Shared immutable value types. Imports nothing from the project.

## Contents

| Module | Purpose |
| --- | --- |
| `models.py` | `Frozen` pydantic base: immutable, unknown fields rejected |
| `literals.py` | Closed sets shared across domains: `Alignment`, `NativeFont`, `CutMode` |
| `printer_profile.py` | `PrinterProfile`, `FontMetrics`, `UsbId`: static hardware facts, validated so both fonts fit the print width |
| `print_plan.py` | `PrintPlan` and its ops: `TextOp`, `RasterOp`, `QrOp`, `FeedOp`, `CutOp` |
| `documents.py` | Minimal text document IR: `Document`, `Paragraph`, `Run` |
| `sources.py` | `TextSource` used by the text MVP |

## Why the print plan lives here

`formatting` produces plans and `printing` executes them. The two domains may not import each other, so the plan is shared kernel.

`TextOp.text` is one or more lines. The printer terminates it with a line feed. `RasterOp.image` is expected to be 1-bit and no wider than the profile's print width. Alignment other than centered is baked into the image by `formatting`.

Plan models carry PIL images, so they allow arbitrary types. Plans are never persisted. Blocks are.

The text document is a single paragraph or a sequence of paragraphs made of runs. Empty documents
are rejected. `TextSource` rejects blank input.

## Planned

Additional block kinds, URL and file sources, job options, media types, and typed identifiers.
