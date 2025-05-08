import json
import sys
import os


def main():
    # Check command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python fixjson.py input.json [output.json] [forms.json]")
        print("  input.json: Path to the species JSON file to process")
        print(
            "  output.json: Path for the output JSON file (default: input_fixed.json)"
        )
        print(
            "  forms.json: Path to the forms JSON file (default: forms.json in the same dir as the script)"
        )
        sys.exit(1)

    # Dictionary of corrected species names for specific dexIds
    corrected_species_names = {
        29: "Nidoran♀",
        32: "Nidoran♂",
        669: "Flabébé",
        772: "Type: Null"
    }

    # Get input file path
    input_file = sys.argv[1]

    # Determine output file path
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Default: replace extension with _fixed.json
        base = os.path.splitext(input_file)[0]
        output_file = f"{base}_fixed.json"

    # Determine forms file path
    if len(sys.argv) >= 4:
        forms_file = sys.argv[3]
    else:
        # Default: forms.json in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        forms_file = os.path.join(script_dir, "forms.json")

    print(f"Processing species data from: {input_file}")
    print(f"Using forms data from: {forms_file}")
    print(f"Output will be saved to: {output_file}")

    # Load the species data
    try:
        with open(input_file, "r") as f:
            species_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Species file not found: {input_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in species file: {input_file}")
        sys.exit(1)

    # Load the forms data
    try:
        with open(forms_file, "r") as f:
            forms_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Forms file not found: {forms_file}")
        print("Continuing without forms data...")
        forms_data = {}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in forms file: {forms_file}")
        print("Continuing without forms data...")
        forms_data = {}

    # Process each Pokémon in the species data
    for pokemon in species_data:
        # Skip entries without a proper species name
        if not pokemon.get("speciesName"):
            continue

        # Correct species names based on dexId if needed
        if pokemon.get("dexId") and pokemon["dexId"] in corrected_species_names:
            pokemon["speciesName"] = corrected_species_names[pokemon["dexId"]]

        # Default nameKey is just the Pokémon's name
        pokemon["nameKey"] = pokemon["speciesName"]

        # Check if we need to add form information
        if pokemon.get("dexId") and pokemon.get("formId") is not None:
            dex_id_str = str(pokemon["dexId"])

            # Check if this Pokémon has forms in the forms data
            if dex_id_str in forms_data:
                form_id = pokemon["formId"]
                form_info = None

                # Special case: if form_id is 0 and there's a form with index 0, use it
                if form_id == 0:
                    for form in forms_data[dex_id_str].get("forms", []):
                        if form.get("index") == 0:
                            form_info = form
                            break
                # Otherwise look for a form with matching index
                else:
                    for form in forms_data[dex_id_str].get("forms", []):
                        if form.get("index") == form_id:
                            form_info = form
                            break

                # If we found a matching form, update the nameKey
                if form_info and "form" in form_info:
                    pokemon["nameKey"] = f"{pokemon['speciesName']}-{form_info['form']}"

    # Save the updated species data
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(species_data, f, indent=2, ensure_ascii=False)
        print(f"Processing complete. Updated data saved to {output_file}")
    except IOError as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
