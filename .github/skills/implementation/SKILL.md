---
name: implementation
description: Use when implementing or modifying application code, tests, architecture, or build-plan phases in this repository.
---

# Implementation

- Read the architecture draft in `README.md` before changing project structure or layer boundaries, and propose architecture changes before implementing them.
- Follow the layer contracts in `pyproject.toml`. If a change needs a forbidden import, introduce a port at the appropriate boundary.
- Keep domain logic pure where possible: layout, state transitions, and configuration resolution should take values and return values.
- Fully annotate code. Do not use `Any`.
- Do not write comments or docstrings. `tests/test_source_rules.py` enforces this for `src`.
- Import `escpos` only in `printing/escpos_usb.py`.
- Every behavior change must include a test. Run `just check` before finishing.
- Work on one build-plan phase at a time and stop when its acceptance criteria are met.
- A folder containing only `.placeholder` is not yet built. Delete the placeholder when its first real module lands.
