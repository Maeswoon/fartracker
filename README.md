# FARTracker

## Prerequisies
- `python3` + `uv`
- `npm`

Generate secrets (one time): `./generate-secrets.sh`
SSL certificates are generated with `ssls.com` and verified via an ACME challenge file.
For development, make sure `frontend/.env` is populated with `VITE_MAPBOX_TOKEN=...`

## Frontend
Install dependencies: `npm install`
Run locally: `npm run dev`
Build: `npm run build`

## Backend
Install dependencies: `uv sync`
Run locally: `DJANGO_DEBUG=1 uv run uvicorn fartracker_backend.asgi:application --port 8000 --reload`

## Deployment
Deploy backend/frontend only: `./deploy.sh --keep-db`
Deploy everything: `./deploy.sh` (**this will back up and overwrite the database**)
Backend admin panel can be accessed at <https://tracker.faroutlaunch.org/api/admin>
