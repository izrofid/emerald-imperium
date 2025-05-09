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
YAML_OUTPUT="${DEX_DIR}/sprites.yaml"
JSON_OUTPUT="${DEX_DIR}/sprites.json"

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

echo "Extracting sprite data..."
echo "Output: $JSON_OUTPUT"

# Run the test and extract data between markers
cd "$PROJECT_ROOT" || exit 1
make -j4 check TESTS="Print Sprites" | \
    awk '/===SPRITES DEBUG OUTPUT START===/{flag=1; next} /===SPRITES DEBUG OUTPUT END===/{flag=0} flag' > "$YAML_OUTPUT"

# Check if yq is installed
if ! command -v yq &> /dev/null; then
    echo "Error: yq is not installed. Please install it to convert YAML to JSON."
    exit 1
fi

# Convert YAML to JSON
# Convert YAML to JSON with preserved hex format
python3 - <<EOF > "$JSON_OUTPUT"
import yaml
import json
import re

class HexJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        return super().default(obj)

with open("$YAML_OUTPUT", 'r') as yaml_file:
    try:
        data = yaml.safe_load(yaml_file)
        
        # Process each entry to ensure consistent hex format
        for item in data:
            if isinstance(item, dict):
                for key in list(item.keys()):
                    if key.endswith('pointer') and isinstance(item[key], str):
                        # Normalize hex strings to "0xXXXXXXXX" format
                        hex_str = item[key].replace('0x', '').strip('"')
                        try:
                            # Convert to int first to validate, then back to hex
                            int_val = int(hex_str, 16)
                            item[key] = f"0x{int_val:08X}"  # Format as 0xXXXXXXXX
                        except ValueError:
                            # Keep original if conversion fails
                            pass
        
        # Write to JSON with hex strings
        with open("$JSON_OUTPUT", 'w') as json_file:
            json.dump(data, json_file, indent=2)
            
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        exit(1)
EOF

echo "Done! Sprite data saved to $JSON_OUTPUT"