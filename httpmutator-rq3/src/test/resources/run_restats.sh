#!/bin/bash

# ROOT = parent.parent.parent.parent of this script file
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../../" && pwd)"

RE_STATS_DIR="$ROOT/expScripts/restats"

CONFIGS=$(find "$ROOT/httpmutator-rq3/src/test/resources" -type f -name "restats-config.json")

# cd expScripts/restats
cd "$RE_STATS_DIR" || { echo "Cannot enter $RE_STATS_DIR"; exit 1; }

for cfg in $CONFIGS; do
    echo "Executing: python app.py $cfg"
    python app.py "$cfg"
done

echo "All tasks completed."
