#!/bin/bash
# ORPHEUS System Initializer — Creates .orpheus/ directory tree for a new system.
#
# Usage: init-system.sh <system-name> [--base-path <path>]
# Outputs JSON listing all created paths.

set -euo pipefail

SYSTEM_NAME="${1:?Usage: init-system.sh <system-name> [--base-path <path>]}"
BASE_PATH=".orpheus"

# Parse optional --base-path
shift
while [[ $# -gt 0 ]]; do
    case "$1" in
        --base-path) BASE_PATH="$2"; shift 2;;
        *) shift;;
    esac
done

# Create directory structure
mkdir -p "$BASE_PATH"/{orchestrator,experts,workers,scripts}
mkdir -p "$BASE_PATH"/state/{execution,shared}
mkdir -p "$BASE_PATH"/logs/{build,runtime}
mkdir -p "$BASE_PATH"/adapters

# Initialize empty system.yaml
cat > "$BASE_PATH/system.yaml" << YAML
system:
  name: "$SYSTEM_NAME"
  description: ""

orchestrator:
  strategy: adaptive
  max_retries: 2
  timeout_seconds: 300
  escalation: user
  routing: []

logging:
  level: info
  log_actions: true
  log_decisions: true
  log_contracts: true
  log_lifecycle: true
  log_delegations: true
  assemble_timeline: true
  assemble_decisions: true
  assemble_errors: true
  retain_last: 20
  log_builds: true
  build_retain_last: 10
YAML

# Initialize empty registry.yaml
cat > "$BASE_PATH/registry.yaml" << YAML
system: "$SYSTEM_NAME"
version: "1.0.0"

skills:
  orchestrator:
    name: ""
    path: ""
    version: "1.0.0"
    contract: ""
  experts: []
  workers: []
YAML

# Initialize counters
mkdir -p "$BASE_PATH/state"
cat > "$BASE_PATH/state/.counters.yaml" << YAML
a: 0
b: 0
d: 0
e: 0
s: 0
YAML

# Copy ORPHEUS runtime scripts into the generated system for self-containment.
# This makes the system independent of the global ORPHEUS skill install path.
# Determine ORPHEUS skill directory (where this script lives)
ORPHEUS_SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

for script in generate-id.py validate-yaml.py init-execution.sh assemble-logs.py; do
    if [ -f "$ORPHEUS_SCRIPTS_DIR/$script" ]; then
        cp "$ORPHEUS_SCRIPTS_DIR/$script" "$BASE_PATH/scripts/$script"
        chmod +x "$BASE_PATH/scripts/$script"
    fi
done

# Output JSON
echo "{\"status\":\"created\",\"system_name\":\"$SYSTEM_NAME\",\"base_path\":\"$BASE_PATH\",\"directories\":[\"orchestrator\",\"experts\",\"workers\",\"scripts\",\"state/execution\",\"state/shared\",\"logs/build\",\"logs/runtime\",\"adapters\"],\"files\":[\"system.yaml\",\"registry.yaml\",\"state/.counters.yaml\",\"scripts/generate-id.py\",\"scripts/validate-yaml.py\",\"scripts/init-execution.sh\",\"scripts/assemble-logs.py\"]}"
