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

TS=$(date -u +%Y%m%dT%H%M%SZ)
PROD_HOME="/home/ubuntu"
PROD_ZIP="prod.tar.gz"

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
  tar -czvf "$PROD_ZIP" frontend
else
  mkdir -p backend
  cp -r ../backend/. backend/
  tar -czvf "$PROD_ZIP" --exclude='backend/.venv' backend frontend
fi

scp "$PROD_ZIP" farout-aws:$PROD_HOME/$PROD_ZIP

if [ "$FRONTEND_ONLY" = "1" ]; then
  ssh farout-aws <<EOF
    cd $PROD_HOME
    rm -rf frontend
    tar -xf "$PROD_ZIP"
    sudo rm -rf /var/www/fartracker
    sudo mkdir -p /var/www/fartracker
    sudo cp -r $PROD_HOME/frontend/* /var/www/fartracker
EOF
else
  ssh farout-aws <<EOF
    cd $PROD_HOME

    # Back up sqlite DB
    mkdir -p $PROD_HOME/backups/$TS
    find $PROD_HOME -maxdepth 4 -name '*.sqlite3' -not -path '*/backups/*' -exec cp {} $PROD_HOME/backups/$TS/ \;
    find $PROD_HOME/backups -mindepth 1 -maxdepth 1 -type d | sort | head -n -30 | xargs -r rm -rf

    rm -rf backend frontend
    tar -xf "$PROD_ZIP"

    # Frontend
    sudo rm -rf /var/www/fartracker
    sudo mkdir -p /var/www/fartracker
    sudo cp -r $PROD_HOME/frontend/* /var/www/fartracker/

    # Backend service
    sudo snap install --classic astral-uv
    sudo cp $PROD_HOME/backend/fartracker.service /etc/systemd/system/
    sudo mkdir -p /var/log/fartracker
    sudo chown ubuntu:ubuntu /var/log/fartracker
    sudo cp $PROD_HOME/backend/fartracker.logrotate /etc/logrotate.d/fartracker
    sudo systemctl daemon-reload
    sudo systemctl enable fartracker
    sudo systemctl restart fartracker
    sudo systemctl --no-pager --full status fartracker

    # Nginx config
    sudo cp $PROD_HOME/backend/nginx.conf /etc/nginx/
    sudo chmod 644 /etc/nginx/nginx.conf
    sudo chown root:root /etc/nginx/nginx.conf
    sudo rm -rf /etc/nginx/conf.d/*
    sudo cp $PROD_HOME/backend/far_out.nginx.conf /etc/nginx/conf.d/
    sudo chmod 644 /etc/nginx/conf.d/*
    sudo chown root:root /etc/nginx/conf.d/*
    sudo rm -rf /etc/nginx/sites-enabled/*
    sudo nginx -t && sudo systemctl reload nginx
EOF
fi
