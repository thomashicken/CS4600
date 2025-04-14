import requests
import json

api_key = '0bxYWP3iH2bW7psubPM6SkbxOL7p4fdynk66Np6b'

# Define only the nutrients we care about
important_nutrients = {
    "Energy": "Calories",
    "Protein": "Protein",
    "Total lipid (fat)": "Total Fat",
    "Carbohydrate, by difference": "Carbohydrates"
}

def get_fdc_id(food_name, api_key):
    url = f"https://api.nal.usda.gov/fdc/v1/search?api_key={api_key}"
    data = {"generalSearchInput": food_name}
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
    parsed = response.json()

    if 'error' in parsed:
        print(f"API Error: {parsed['error'].get('message', 'Unknown error')}")
        return None, None, None

    if 'foods' not in parsed or not parsed['foods']:
        print(f"No results found for '{food_name}'. Try a more specific name (e.g., 'red apple').")
        return None, None, None

    # Display search results
    print(f"\nSearch results for '{food_name}':")
    choices = []
    for i, food in enumerate(parsed['foods'][:20]):  # Show top 20 results
        brand = food.get('brandOwner', 'Generic/Unknown')
        description = food['description']
        fdc_id = food['fdcId']
        print(f"{i+1}. {description} (Brand: {brand}, FDC ID: {fdc_id})")
        choices.append(food)

    # Let the user pick one
    while True:
        try:
            choice = int(input("\nEnter the number of the food you want to log (1-20): ").strip())
            if 1 <= choice <= len(choices):
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 20.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    chosen_food = choices[choice - 1]
    fdc_id = chosen_food['fdcId']
    chosen_description = chosen_food['description']
    chosen_brand = chosen_food.get('brandOwner', 'Generic/Unknown')

    print(f"\nChosen food: {chosen_description} (Brand: {chosen_brand}, FDC ID: {fdc_id})")

    return fdc_id, chosen_description, chosen_brand

def get_nutrition_data(fdc_id, api_key):
    import requests

    url = f"https://api.nal.usda.gov/fdc/v1/{fdc_id}?api_key={api_key}"
    response = requests.get(url)
    parsed = response.json()

    important_nutrients = {
        "Energy": "Calories",
        "Protein": "Protein",
        "Total lipid (fat)": "Total Fat",
        "Carbohydrate, by difference": "Carbohydrates"
    }

    nutrition_data = {}

    # Step 1: Try to use foodNutrients
    if 'foodNutrients' in parsed:
        for nutrient in parsed['foodNutrients']:
            name = nutrient.get('nutrient', {}).get('name', 'Unknown Nutrient')
            if name in important_nutrients:
                display_name = important_nutrients[name]
                unit = nutrient.get('nutrient', {}).get('unitName', '')
                amount = nutrient.get('amount', 0)

                # Only include kcal values for Energy
                if name == "Energy" and unit != "kcal":
                    continue

                # Sanity check
                if display_name == "Calories" and amount > 1500:
                    print(f"Skipping unreasonable calorie value: {amount} kcal")
                    continue

                nutrition_data[display_name] = f"{amount} {unit}"

    # Step 2: If empty, try labelNutrients as fallback
    if not nutrition_data:
        label = parsed.get("labelNutrients", {})
        for key, display_name in [("calories", "Calories"),
                                  ("fat", "Total Fat"),
                                  ("carbohydrates", "Carbohydrates"),
                                  ("protein", "Protein")]:
            if key in label:
                amount = label[key].get("value", 0)
                # Sanity check
                if amount > 1500:
                    print(f"Skipping label {display_name}: suspiciously high value {amount}")
                    continue
                unit = "kcal" if key == "calories" else "g"
                nutrition_data[display_name] = f"{amount} {unit}"

    if not nutrition_data:
        print(f"No nutrition data found for FDC ID {fdc_id}.")
        return None, None, None

    # Step 3: Estimate a realistic portion size
    portions = parsed.get("foodPortions", [])
    full_item_grams = None
    for portion in portions:
        if not isinstance(portion, dict):
            continue  # Skip if portion isn't a dictionary

        modifier = portion.get("modifier", "")
        if isinstance(modifier, str) and any(keyword in modifier.lower() for keyword in ["sandwich", "burger", "container", "bottle", "burrito", "cup"]):
            full_item_grams = portion.get("gramWeight")
            break

    # Fallback: use first portion > 50g
    if not full_item_grams:
        for portion in portions:
            if isinstance(portion, dict):
                grams = portion.get("gramWeight")
                if grams and grams > 50:
                    full_item_grams = grams
                    break

    # Step 4: Scale nutrient values
    default_grams = 100
    scaling_factor = full_item_grams / default_grams if full_item_grams else 1.0

    # Optional debug
    if scaling_factor != 1.0:
        print(f"Scaling nutrients by x{scaling_factor:.2f} (based on {full_item_grams}g)")

    for key in nutrition_data:
        value = nutrition_data[key]
        try:
            num, unit = value.split()
            scaled = round(float(num) * scaling_factor, 2)
            nutrition_data[key] = f"{scaled} {unit}"
        except Exception:
            print(f"Could not parse value for {key}: {value}")

    return nutrition_data, None, None
