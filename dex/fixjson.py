import json

# Load the species data
with open("species.json", "r") as f:
    species_data = json.load(f)

# Load the forms data
with open("forms.json", "r") as f:
    forms_data = json.load(f)

# Process each Pokémon in the species data
for pokemon in species_data:
    # Skip entries without a proper species name
    if not pokemon.get("speciesName"):
        continue

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
with open("species_updated.json", "w") as f:
    json.dump(species_data, f, indent=2)

print("Processing complete. Updated data saved to species_updated.json")
