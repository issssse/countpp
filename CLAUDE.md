# Project AI operating rules

## Environment
- Use VS Code Dev Containers for project execution.
- Use Podman through Docker compatibility.
- Use uv for Python dependency/test commands when applicable.
- Use the project's existing package manager for JS/TS.
- Never commit secrets, .env files, tokens, API keys, or private credentials.

## AI workflow
- First inspect the repo and summarize architecture.
- Plan before editing.
- Make small reviewable diffs.
- Run tests/lint/typecheck after edits.
- Use cheaper/faster agents for search, docs, and test-log triage.
- Use stronger agents for architecture, security, hard debugging, and final review.

## Verification
- Python default: uv run pytest -q, ruff check ., ruff format .
- JS/TS default: npm test, npm run lint, npm run typecheck if available.
- Do not claim success unless verification ran or you explain why it could not run.

## Git
- Work on a feature branch.
- Commit only coherent passing checkpoints.
- Never force push.
- Show git diff before final summary.
