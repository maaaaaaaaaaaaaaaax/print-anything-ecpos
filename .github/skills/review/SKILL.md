---
name: review
description: Use when reviewing code changes, pull requests, or implementation work in this repository.
---

# Code review

- Compare the changes with the task requirements and the current build-plan phase's acceptance criteria. Do not expand the review into later phases.
- Check that behavior changes have focused tests and that `just check` passes.
- Check that code is fully annotated, uses no `Any`, and adds no comments or docstrings. `tests/test_source_rules.py` enforces the source comment and docstring rule for `src`.
- Check imports against the layer contracts in `pyproject.toml`; `escpos` must remain confined to `printing/escpos_usb.py`.
- Check that domain logic remains pure where possible, especially layout, state transitions, and configuration resolution.
- Report actionable findings with file and line references. If there are no findings, state that explicitly and note any validation not performed.
