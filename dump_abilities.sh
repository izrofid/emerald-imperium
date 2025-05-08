#!/bin/bash
# filepath: /home/kildemal/romhacks/emerald-imperium/dump_abilities.sh

# Find project root by looking for the marker file
find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/.ROOT" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "Error: Could not find project root marker (.ROOT)" >&2
    exit 1
}

# Get directory paths
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")"
DEX_DIR="${PROJECT_ROOT}/dex"

# Create default output paths
YAML_OUTPUT="${DEX_DIR}/abilities.yaml"
JSON_OUTPUT="${DEX_DIR}/abilities.json"

# Parse command-line arguments (optional output file)
if [ $# -ge 1 ]; then
    # If relative path is provided, make it relative to the dex directory
    if [[ ! "$1" = /* ]]; then
        JSON_OUTPUT="${DEX_DIR}/$1"
    else
        JSON_OUTPUT="$1"
    fi
fi

# Ensure dex directory exists
mkdir -p "$(dirname "$JSON_OUTPUT")"

# Activate virtual environment if it exists
VENV_DIR="${PROJECT_ROOT}/.venv"
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    if [[ -z "$VIRTUAL_ENV" || "$VIRTUAL_ENV" != *"$VENV_DIR"* ]]; then
        echo "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
    fi
fi

echo "Extracting ability data..."
echo "Output: $JSON_OUTPUT"

# Run the test and extract data between markers
cd "$PROJECT_ROOT" || exit 1
make -j4 check TESTS="Extract Abilities" | \
    awk '/===ABILITIES DEBUG OUTPUT START===/{flag=1; next} /===ABILITIES DEBUG OUTPUT END===/{flag=0} flag' > "$YAML_OUTPUT"

# Check if yq is installed
if ! command -v yq &> /dev/null; then
    echo "Error: yq is not installed. Please install it to convert YAML to JSON."
    exit 1
fi

# Convert YAML to JSON
yq . "$YAML_OUTPUT" -j > "$JSON_OUTPUT"

echo "Done! Ability data saved to $JSON_OUTPUT"