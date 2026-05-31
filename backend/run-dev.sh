set -eux
set -o pipefail

DJANGO_DEBUG=1 uv run uvicorn fartracker_backend.asgi:application --port 8000 --reload
