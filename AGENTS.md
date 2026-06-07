# AGENTS.md

## Important notes
- Always include a `cd` command with the fully-qualified target path before executing a command

## Backend setup
- Install deps: `cd backend && uv sync`
- Check/lint: `cd backend && uv run python manage.py check`

## Frontend setup
- Install deps: `cd frontend && npm install`
- Build/check: `cd frontend && npm run build`

## Code style
- Single newlines between separate code blocks - no double-newlines
