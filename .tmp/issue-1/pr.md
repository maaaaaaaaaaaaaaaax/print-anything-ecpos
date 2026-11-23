Closes #1

### What's included in this change?
Added an opt-in USB printer smoke test using an explicitly selected bundled profile.
It prints text, alignment, line-width and cut samples, then reports printer status.
Documented the Pi setup and fields to record; actual printer behavior remains unverified until run with the hardware.

Files:
- pyproject.toml
- src/printbot/printing/README.md

### How to test
