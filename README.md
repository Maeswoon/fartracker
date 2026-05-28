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

## Deployment
Deploy frontend only: `./deploy.sh --frontend-only`
Deploy backend and frontend: `./deploy.sh` (**this will back up and overwrite the database**)
Backend admin panel can be accessed at <https://tracker.faroutlaunch.org/api/admin>
