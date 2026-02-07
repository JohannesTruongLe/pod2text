#!/usr/bin/env sh
set -eu

IMAGE_NAME="${IMAGE_NAME:-pod2text:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-pod2text-server}"
PODCAST="${PODCAST:-Was jetzt}"
INTERVAL_MINUTES="${INTERVAL_MINUTES:-30}"
DEPLOY_STARTED_AT="$(date +%s)"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

load_telegram_env() {
  if [ ! -f .env ]; then
    return 1
  fi

  set -a
  # shellcheck disable=SC1091
  . ./.env >/dev/null 2>&1 || true
  set +a

  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    return 1
  fi

  return 0
}

send_telegram_notification() {
  text="$1"

  if ! load_telegram_env; then
    log "Telegram deploy notification skipped (.env or Telegram vars missing)."
    return 0
  fi

  curl -sS --max-time 10 \
    -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${text}" \
    >/dev/null 2>&1 || log "Telegram deploy notification failed."
}

run_step() {
  step_label="$1"
  shift

  step_started_at="$(date +%s)"
  log "${step_label}"
  "$@"
  step_ended_at="$(date +%s)"
  log "${step_label} completed in $((step_ended_at - step_started_at))s"
}

replace_container() {
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
}

on_exit() {
  exit_code="$1"
  deploy_ended_at="$(date +%s)"
  total_duration="$((deploy_ended_at - DEPLOY_STARTED_AT))"

  if [ "$exit_code" -eq 0 ]; then
    log "Deploy succeeded in ${total_duration}s"
    send_telegram_notification "✅ pod2text deploy succeeded (${IMAGE_NAME}) in ${total_duration}s on $(hostname)."
  else
    log "Deploy failed in ${total_duration}s (exit ${exit_code})"
    send_telegram_notification "❌ pod2text deploy failed (${IMAGE_NAME}) after ${total_duration}s on $(hostname). Exit code: ${exit_code}."
  fi
}

trap 'on_exit "$?"' EXIT

run_step "Step 1/3: Running setup wizard" python3 scripts/setup_env.py
run_step "Step 2/3: Building Docker image (${IMAGE_NAME})" env DOCKER_BUILDKIT=1 docker build -t "${IMAGE_NAME}" .
run_step "Step 3/3: Replacing container (${CONTAINER_NAME})" replace_container

log "Container is running. Follow logs with: docker logs -f ${CONTAINER_NAME}"
