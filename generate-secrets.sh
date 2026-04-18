set -eu
set -o pipefail
echo "DJANGO_SECRET_KEY=$(cd backend && uv run python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" > backend/.env
