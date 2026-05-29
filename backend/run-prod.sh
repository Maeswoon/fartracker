set -eux
set -o pipefail

rm -rf .venv uv.lock
uv sync
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput

pkill -TERM -f 'gunicorn.*fartracker_backend.wsgi' || true
for _ in $(seq 1 20); do
  pgrep -f 'gunicorn.*fartracker_backend.wsgi' >/dev/null || break
  sleep 0.5
done
pkill -KILL -f 'gunicorn.*fartracker_backend.wsgi' || true

exec uv run gunicorn fartracker_backend.asgi:application --bind 127.0.0.1:8000 --workers 3 --worker-class uvicorn.workers.UvicornWorker
