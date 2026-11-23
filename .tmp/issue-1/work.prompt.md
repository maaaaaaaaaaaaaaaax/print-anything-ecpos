Task: issue 1 - 1. Verify the first real USB printer in /Users/mschmalenbach/Documents/print-anything-ecpos (tier s, stage work).
Artifact dir (scratch, inside repo .tmp): /Users/mschmalenbach/Documents/print-anything-ecpos/.tmp/issue-1
Read these first; open source files only if they are not enough:
- /Users/mschmalenbach/Documents/print-anything-ecpos/.tmp/issue-1/context.md (issue)
- inventory: /Users/mschmalenbach/Documents/print-anything-ecpos/.tmp/issue-1/inventory.md (agents/skills, regenerated each run)
Agents/skills available for this stage (names may change; use what exists):
- none matched; follow AGENTS.md and the repo instruction files
Rules:
- Local only. Never stage, commit, push, create PRs, or write to GitHub (issues, comments, projects, status). Save outputs as files in the artifact dir.
- Stay inside this stage.
- Local files replace GitHub. These are WAIVED, do not attempt or check them: project Status/Ready gates, approved-plan-in-issue-comments, status updates, posting. `gh project` and `gh api` are blocked. The issue text in /Users/mschmalenbach/Documents/print-anything-ecpos/.tmp/issue-1/context.md is the full source. The file /Users/mschmalenbach/Documents/print-anything-ecpos/.tmp/issue-1/plan.md (or the local plan named below) IS the approved plan. If the issue is thin, state your assumptions in the output and continue; never stop only because GitHub state cannot be read.
- No inline code comments unless a line truly needs clarification. Clean, simple, readable code.
- Smallest change that fully solves the task. No unrelated refactors.
- Test first when behavior is testable. Run the narrowest check that can fail.
- Document decisions persistently in repo docs when behavior or architecture changes.
- Never mention scratch/plan item names from .tmp (e.g. W02, R4) in repo docs or code.
- ASCII only in text output. Concise answers. No praise, no filler.
- Scratch files only in the artifact dir inside .tmp/. Never stage, commit or push.
- On merge conflicts prefer the changes from main.
- PR text: short and simple, follow .github/pull_request_template.md.
- Report results in simple language. Explain findings plainly.
- Draft issues and PR text locally; never post them without explicit instruction.
User note: fetch issue number 1, remember that we are currently developing on mac and i will later sync the code manually to the pi to connect the printer and test it there, therefor integrate a first printing verification, there is already printing functionality in the project, gather context by reading through the readme of course


Stage work (small task, one pass): understand the issue, find the code via the digests, fix it test-first, run the narrowest check, update directly related docs. Then do a short self review of your own diff and fix what you find. No plan document needed.
Also write /Users/mschmalenbach/Documents/print-anything-ecpos/.tmp/issue-1/summary.md: 2-4 plain-language lines on what changed and why (used for the PR text).
Finish with: files changed, checks run, open items.
