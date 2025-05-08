#!/bin/bash

# Find project root by looking for the marker file
find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        # Check for our unique marker file
        if [ -f "$dir/.ROOT" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "Error: Could not find project root marker (.EMERALD-ROOT)" >&2
    echo "Make sure you have a .EMERALD-ROOT file in your project root directory." >&2
    exit 1
}

# Start search from the script's directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(find_project_root "$SCRIPT_DIR")"

# Define dex directory (default or custom)
DEX_DIR="${PROJECT_ROOT}/dex"  # Default location

# Allow overriding DEX_DIR with environment variable
if [ ! -z "$CUSTOM_DEX_DIR" ]; then
    # Check if it's an absolute path
    if [[ "$CUSTOM_DEX_DIR" = /* ]]; then
        DEX_DIR="$CUSTOM_DEX_DIR"
    else
        # Treat as relative to project root
        DEX_DIR="${PROJECT_ROOT}/${CUSTOM_DEX_DIR}"
    fi
fi

set -e  # Exit on error

# Default filenames
YAML_OUTPUT="${DEX_DIR}/species.yaml"
JSON_OUTPUT="${DEX_DIR}/species.json"

# Parse command-line arguments
if [ $# -ge 1 ]; then
    # If relative path is provided, make it relative to the dex directory
    if [[ ! "$1" = /* ]]; then
        YAML_OUTPUT="${DEX_DIR}/$1"
    else
        YAML_OUTPUT="$1"
    fi
    JSON_OUTPUT="${YAML_OUTPUT%.*}.json"  # Replace extension with .json
fi

if [ $# -ge 2 ]; then
    # If relative path is provided, make it relative to the dex directory
    if [[ ! "$2" = /* ]]; then
        JSON_OUTPUT="${DEX_DIR}/$2"
    else
        JSON_OUTPUT="$2"
    fi
fi

# Detect and activate virtual environment if needed
VENV_DIR="${PROJECT_ROOT}/.venv"
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    if [[ -z "$VIRTUAL_ENV" || "$VIRTUAL_ENV" != *"$VENV_DIR"* ]]; then
        echo "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
    fi
fi

echo "Generating species data..."
echo "Project root: $PROJECT_ROOT"
echo "Dex directory: $DEX_DIR"
echo "YAML output: $YAML_OUTPUT"
echo "JSON output: $JSON_OUTPUT"

# Run the test and extract data between markers (from project root)
cd "$PROJECT_ROOT" || exit 1
make -j4 check TESTS="Print mons" | awk '/===DEBUG OUTPUT START===/{flag=1; next} /===DEBUG OUTPUT END===/{flag=0} flag' > "$YAML_OUTPUT"

# Check if yq is installed
if ! command -v yq &> /dev/null; then
    echo "Error: yq is not installed. Please install it to convert YAML to JSON."
    exit 1
fi

# Convert YAML to JSON
yq . "$YAML_OUTPUT" -j > "$JSON_OUTPUT"

echo "Data generation complete."
echo "YAML data saved to: $YAML_OUTPUT"
echo "JSON data saved to: $JSON_OUTPUT"