---
name: pr
description: Use when preparing a pull-request handoff for completed work.
---

# Pull request handoff

- Inspect the current diff, worktree status, relevant commits, and completed validation before preparing the handoff.
- Provide a suggested title and a ready-to-use description covering the change, rationale, testing, and any risks, migration notes, or follow-up work.
- State the actual base and head branches when known. Distinguish committed and pushed changes from local or uncommitted work; never imply that remote CI or a PR exists unless verified.
- Include blockers and the exact information or user actions needed before opening the PR.
- Do not create, edit, or comment on a pull request or any other remote resource. Do not commit or push. Leave the user with all information needed to perform those actions.
