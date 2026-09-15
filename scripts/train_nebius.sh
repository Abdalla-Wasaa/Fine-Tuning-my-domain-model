#!/usr/bin/env bash
# Run inside tmux on the target VM. Provision API permissions before starting.
set -Eeuo pipefail
: "${NEBIUS_INSTANCE_ID:?Set the exact ID of this dedicated training VM}"
: "${MAX_RUN_SECONDS:?Set a budget-derived wall-clock limit in seconds}"
: "${ARTIFACT_URI:?Set an s3:// path in your configured durable object storage}"
[[ "$MAX_RUN_SECONDS" =~ ^[1-9][0-9]*$ ]] || { echo 'Invalid time limit'; exit 2; }
[[ "$ARTIFACT_URI" == s3://* ]] || { echo 'ARTIFACT_URI must use s3://'; exit 2; }
cd "$(dirname "$0")/.."
mkdir -p reports artifacts
command -v nebius >/dev/null || { echo "Nebius CLI missing: stop the instance in the console." >&2; exit 2; }
cleanup() {
  result=$?
  trap - EXIT INT TERM
  set +e
  # All paths, including failed training/upload, request a provider-level stop.
  for attempt in 1 2 3; do
    nebius compute instance stop --id "$NEBIUS_INSTANCE_ID" --format json > reports/stop_receipt.json 2> artifacts/stop_error.log
    if [[ $? == 0 ]]; then exit "$result"; fi
    sleep 5
  done
  echo 'CRITICAL: provider stop failed. Stop this instance in the Nebius console immediately.' >&2
  exit 90
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
for executable in aws timeout python; do command -v "$executable" >/dev/null; done
# Preflight failures also trigger the provider-stop cleanup.
nebius compute instance get --id "$NEBIUS_INSTANCE_ID" --format json > artifacts/instance_before.json
aws s3 ls "$ARTIFACT_URI" >/dev/null
# Also arm a separate process so loss of the training shell still requests stop.
nohup bash -c 'sleep "$1"; nebius compute instance stop --id "$2"' _ "$MAX_RUN_SECONDS" "$NEBIUS_INSTANCE_ID" > artifacts/watchdog.log 2>&1 &
# The run limit includes artifact upload. Download models before starting this wrapper.
export ARTIFACT_URI
timeout --signal=TERM --kill-after=30 "$MAX_RUN_SECONDS" bash -c '
  set -e
  python fine_tune.py
  tar -czf artifacts/adapter-and-reports.tar.gz artifacts/adapter reports
  aws s3 cp artifacts/adapter-and-reports.tar.gz "$ARTIFACT_URI/adapter-and-reports.tar.gz"
'
# EXIT trap immediately stops the VM after durable artifact transfer. Merge/evaluate locally.
