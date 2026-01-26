#!/bin/bash
set -e

###############################################
# 1. Define PROJECT ROOT PATH (EDIT THIS ONLY)
###############################################
# Absolute path of this script (resolves symlinks)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# We expect this script to be under:
#   PROJECT_ROOT/expScripts/restats/
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"

###############################################
# 2. Derived paths (no need to edit)
###############################################
RESTATS_DIR="$PROJECT_ROOT/expScripts/restats"
REPORTS_ROOT="$PROJECT_ROOT/expScripts/schemathesis-unique-reports"

###############################################
# 3. Move into RESTats execution directory
###############################################
echo "[INFO] Using PROJECT_ROOT: $PROJECT_ROOT"
echo "[INFO] Moving into: $RESTATS_DIR"

cd "$RESTATS_DIR" || {
    echo "[ERROR] Cannot enter directory: $RESTATS_DIR";
    exit 1;
}

echo "[INFO] Current directory: $(pwd)"
echo "[INFO] Searching for restats-config.json under:"
echo "       $REPORTS_ROOT"
echo

###############################################
# 4. Run RESTats for each config file
###############################################
find "$REPORTS_ROOT" -type f -name "restats-config.json" | while read -r config_file; do
    echo "----------------------------------------"
    echo "[INFO] Running RESTats for:"
    echo "       $config_file"
    echo "----------------------------------------"

    python app.py "$config_file"

    echo "[INFO] Completed: $config_file"
    echo
done

echo "[SUCCESS] All RESTats executions completed."