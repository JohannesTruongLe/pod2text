#!/usr/bin/env sh
set -eu

IMAGE_NAME="${IMAGE_NAME:-pod2text:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-pod2text-server}"
PODCAST="${PODCAST:-Was jetzt}"
INTERVAL_MINUTES="${INTERVAL_MINUTES:-30}"

echo "Step 1/3: Running interactive setup"
python3 scripts/setup_env.py

echo "Step 2/3: Building Docker image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" .

echo "Step 3/3: Starting container in background: ${CONTAINER_NAME}"
mkdir -p output
if docker ps -a --format '{{.Names}}' | grep -Fx "${CONTAINER_NAME}" >/dev/null 2>&1; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  --env-file .env \
  -e PODCAST="${PODCAST}" \
  -e INTERVAL_MINUTES="${INTERVAL_MINUTES}" \
  -v "$(pwd)/output:/app/output" \
  "${IMAGE_NAME}" >/dev/null

echo "Container started. Logs:"
echo "  docker logs -f ${CONTAINER_NAME}"
