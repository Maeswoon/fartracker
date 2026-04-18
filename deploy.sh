usage() {
  cat <<USAGE
Usage: $0 [--frontend-only] [-h|--help]

Builds the frontend and (by default) packages the backend, uploads the
tarball to farout-aws, snapshots any sqlite databases, and redeploys.

Options:
  --frontend-only   Only build and deploy the frontend. Skips backend
                    packaging, the database backup, and the systemd
                    service restart on the server.
  -h, --help        Show this help message and exit.
USAGE
}

FRONTEND_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --frontend-only) FRONTEND_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; usage >&2; exit 1 ;;
  esac
done

if [ $# -eq 0 ]; then
  read -r -p "Are you sure you want to deploy both frontend and backend? This will backup and replace the database [y/N] " reply
  case "$reply" in
    [yY]|[yY][eE][sS]) ;;
    *) echo "Aborted" >&2; exit 1 ;;
  esac
fi

set -eux
set -o pipefail

cd frontend
npm install
npm run build

cd -
if [ ! -f "backend/.env" ]; then
  ./generate-secrets.sh
fi

rm -rf build
mkdir -p build/frontend
cp -r frontend/dist/* build/frontend

cd build
if [ "$FRONTEND_ONLY" = "1" ]; then
  tar -czvf prod.tar.gz frontend
else
  mkdir -p backend
  cp -r ../backend/. backend/
  tar -czvf prod.tar.gz --exclude='backend/.venv' backend frontend
fi
scp prod.tar.gz farout-aws:/home/ubuntu/prod.tar.gz
TS=$(date -u +%Y%m%dT%H%M%SZ)

if [ "$FRONTEND_ONLY" = "1" ]; then
  ssh farout-aws <<EOF
    cd /home/ubuntu
    rm -rf frontend
    tar -xf prod.tar.gz
    sudo rm -rf /var/www/fartracker
    sudo mkdir -p /var/www/fartracker
    sudo cp -r /home/ubuntu/frontend/* /var/www/fartracker
EOF
else
  ssh farout-aws <<EOF
    cd /home/ubuntu
    mkdir -p /home/ubuntu/backups/$TS
    find /home/ubuntu -maxdepth 4 -name '*.sqlite3' -not -path '*/backups/*' -exec cp {} /home/ubuntu/backups/$TS/ \;
    find /home/ubuntu/backups -mindepth 1 -maxdepth 1 -type d | sort | head -n -30 | xargs -r rm -rf
    rm -rf backend frontend
    tar -xf prod.tar.gz
    sudo snap install --classic astral-uv
    sudo cp /home/ubuntu/backend/fartracker.service /etc/systemd/system
    sudo mkdir -p /var/log/fartracker
    sudo chown ubuntu:ubuntu /var/log/fartracker
    sudo cp /home/ubuntu/backend/fartracker.logrotate /etc/logrotate.d/fartracker
    sudo systemctl daemon-reload
    sudo systemctl enable fartracker
    sudo systemctl restart fartracker
    sudo systemctl --no-pager --full status fartracker
    sudo rm -rf /var/www/fartracker
    sudo mkdir -p /var/www/fartracker
    sudo cp -r /home/ubuntu/frontend/* /var/www/fartracker
EOF
fi
