---
name: planning
description: Use when planning project work, defining build phases, or proposing architecture or layer-boundary changes.
---

# Planning

- Read the architecture draft in `README.md` before proposing changes to project structure or layer boundaries.
- Propose architecture changes before implementing them.
- Break build plans into phases with clear acceptance criteria. Work on one phase at a time and stop when that phase's acceptance criteria are met.
- Respect the layer contracts in `pyproject.toml`. If a design needs a forbidden import, plan a port at the appropriate boundary instead.
- Keep domain logic pure where possible: layout, state transitions, and configuration resolution should take values and return values.
