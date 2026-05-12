#!/bin/bash
# K16-Mutex Wrapper [CRUX-MK]
set -euo pipefail

LOCK_DIR="/tmp/df-cape-coral-property-tracker.lock"
LOCK_AGE_LIMIT_S=21600  # 6h

# Stale-Lock-Auto-Claim
if [ -d "$LOCK_DIR" ]; then
    LOCK_AGE_S=$(( $(date +%s) - $(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE_S" -gt "$LOCK_AGE_LIMIT_S" ]; then
        echo "[K16] Stale lock (age=${LOCK_AGE_S}s) -- claiming"
        rm -rf "$LOCK_DIR"
    fi
fi

# Atomic mkdir-Mutex
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "[K16-VETO] Lock held by another instance, exiting"
    exit 3
fi
echo "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM

DF_DIR="/Users/make/Projects/dark-factories/df-cape-coral-property-tracker"
cd "$DF_DIR"

# Sandbox-Default
export DF_CAPE_CORAL_REAL_ENABLED="${DF_CAPE_CORAL_REAL_ENABLED:-false}"
export PHRONESIS_TICKET="${PHRONESIS_TICKET:-MISSING}"

python3 -m src.adapter_orchestrator
