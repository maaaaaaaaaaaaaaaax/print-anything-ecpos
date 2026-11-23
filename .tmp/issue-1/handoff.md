# Handoff (NOT executed)
Branch: feat/1-verify-printer
Suggested commit message: feat: 1. verify the first real usb printer (#1)

Review, then run yourself:
  cd /Users/mschmalenbach/Documents/print-anything-ecpos && git add -p && git commit -m "feat: 1. verify the first real usb printer (#1)"
  git push -u origin feat/1-verify-printer

Diff stat vs origin/main:
 pyproject.toml                  |  1 +
 src/printbot/printing/README.md | 19 +++++++++++--------
 2 files changed, 12 insertions(+), 8 deletions(-)
 M pyproject.toml
 M src/printbot/printing/README.md
?? tests/printing/test_usb_hardware.py
