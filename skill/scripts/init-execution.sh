#!/bin/bash
# ORPHEUS Execution Initializer — Creates execution-specific directory tree.
#
# Usage: init-execution.sh <execution-id> [--base-path <path>]
# Creates state and log directories for a single execution run.
# Outputs JSON confirming created paths.

set -euo pipefail

EID="${1:?Usage: init-execution.sh <execution-id> [--base-path <path>]}"
BASE_PATH=".orpheus"

# Parse optional --base-path
shift
while [[ $# -gt 0 ]]; do
    case "$1" in
        --base-path) BASE_PATH="$2"; shift 2;;
        *) shift;;
    esac
done

# Create state directories
mkdir -p "$BASE_PATH/state/execution/$EID"/{jobs,results,context}

# Create log directories
mkdir -p "$BASE_PATH/logs/runtime/$EID"/{jobs,orchestrator}

echo "{\"status\":\"created\",\"execution_id\":\"$EID\",\"state_path\":\"$BASE_PATH/state/execution/$EID\",\"log_path\":\"$BASE_PATH/logs/runtime/$EID\"}"
