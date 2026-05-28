# FARTracker

## Prerequisies
- `python3` + `uv`
- `npm`

Generate secrets (one time): `./generate-secrets.sh`
SSL certificates are generated with `ssls.com` and verified via an ACME challenge file.

## Frontend
Install dependencies: `npm install`
Run locally: `npm run dev`
Build: `npm run build`

## Backend
Install dependencies: `uv sync`
Run locally: `DJANGO_DEBUG=1 uv run python3 manage.py runserver 8000`
