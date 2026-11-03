#!/usr/bin/env bash
# =============================================================================
# TEMLOOM v4.1 — Unified Air-Gapped Operations & Simulation Launcher
# Usage:
#   ./run.sh                  # Start TEMLOOM in synthetic M/M/1/K physics mode
#   ./run.sh --clab           # Deploy 7-node Containerlab MPLS/SD-WAN topology + TEMLOOM
#   ./run.sh --airgap         # Run TEMLOOM inside zero-egress network namespace
#   ./run.sh --clab --airgap  # Both: Containerlab on host + TEMLOOM in zero-egress netns
#   ./run.sh stop             # Stop all TEMLOOM background daemons
#   ./run.sh destroy          # Stop daemons and tear down Containerlab topology
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
mkdir -p .logs

ACTION="${1:-start}"
USE_CLAB=0
USE_AIRGAP=0

for arg in "$@"; do
  case "$arg" in
    --clab) USE_CLAB=1 ;;
    --airgap) USE_AIRGAP=1 ;;
    stop|destroy) ACTION="$arg" ;;
  esac
done

stop_temloom() {
  echo "[TEMLOOM] Stopping background processes..."
  pkill -f "temloom/ingestion/netflow_simulator.py" 2>/dev/null || true
  pkill -f "temloom/simulation/fault_streamer.py" 2>/dev/null || true
  pkill -f "temloom.api_ui.app" 2>/dev/null || true
  echo "[TEMLOOM] Stopped."
}

if [[ "$ACTION" == "stop" ]]; then
  stop_temloom
  exit 0
fi

if [[ "$ACTION" == "destroy" ]]; then
  stop_temloom
  if command -v containerlab >/dev/null 2>&1; then
    containerlab destroy -t configs/containerlab/temloom-multisite.clab.yml --cleanup 2>/dev/null || true
  fi
  exit 0
fi

echo "[TEMLOOM v4.1] Verifying Ed25519 Model Signatures & Air-Gap Attestation..."
python3 -m temloom.security.model_integrity --verify
python3 -m temloom.security.airgap_compliance

if [[ "$USE_CLAB" -eq 1 ]] && command -v containerlab >/dev/null 2>&1; then
  echo "[TEMLOOM] Deploying 7-node Containerlab MPLS/SD-WAN topology..."
  containerlab deploy -t configs/containerlab/temloom-multisite.clab.yml --reconfigure
  bash configs/containerlab/mpls-frr-setup.sh
  bash configs/containerlab/overlay-setup.sh
  bash configs/containerlab/qos-setup.sh
fi

echo "[TEMLOOM] Starting NetFlow/IPFIX Simulator on 127.0.0.1:9995..."
nohup python3 -m temloom.ingestion.netflow_simulator > .logs/netflow.log 2>&1 &

echo "[TEMLOOM] Starting FastAPI 5-Workbench Operator Console on http://127.0.0.1:8080..."
nohup python3 -m uvicorn temloom.api_ui.app:app --host 127.0.0.1 --port 8080 > .logs/dashboard.log 2>&1 &

echo "[TEMLOOM v4.1] Stack is ONLINE -> http://127.0.0.1:8080"
