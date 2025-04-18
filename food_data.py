import requests
import json

api_key = '0bxYWP3iH2bW7psubPM6SkbxOL7p4fdynk66Np6b'

# A mapping from USDA nutrient names to simplified display names
important_nutrients = {
    "Energy": "Calories",
    "Protein": "Protein",
    "Total lipid (fat)": "Total Fat",
    "Carbohydrate, by difference": "Carbohydrates"
}

def get_fdc_id(food_name, api_key):
    # Constructs the USDA search API endpoint
    url = f"https://api.nal.usda.gov/fdc/v1/search?api_key={api_key}"
     # JSON body for the POST request
    data = {"generalSearchInput": food_name}
     # Sends a POST request to search for the food
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
    # Parses the JSON response
    parsed = response.json()

    # If there's an error in the response, print it and return None
    if 'error' in parsed:
        print(f"API Error: {parsed['error'].get('message', 'Unknown error')}")
        return None, None, None

    # If no foods are returned, notify the user and return None
    if 'foods' not in parsed or not parsed['foods']:
        print(f"No results found for '{food_name}'. Try a more specific name (e.g., 'red apple').")
        return None, None, None

    # Display the top 20 search results
    print(f"\nSearch results for '{food_name}':")
    choices = []
    for i, food in enumerate(parsed['foods'][:20]):  # Show top 20 results
        brand = food.get('brandOwner', 'Generic/Unknown')   # Brand if available
        description = food['description']                   # Food description
        fdc_id = food['fdcId']                              # Food Data Central ID
        print(f"{i+1}. {description} (Brand: {brand}, FDC ID: {fdc_id})")
        choices.append(food)

    # Ask the user to select one result
    while True:
        try:
            choice = int(input("\nEnter the number of the food you want to log (1-20): ").strip())
            if 1 <= choice <= len(choices):
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 20.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Extract details from the chosen food
    chosen_food = choices[choice - 1]
    fdc_id = chosen_food['fdcId']
    chosen_description = chosen_food['description']
    chosen_brand = chosen_food.get('brandOwner', 'Generic/Unknown')

    print(f"\nChosen food: {chosen_description} (Brand: {chosen_brand}, FDC ID: {fdc_id})")

    # Return the selected food's ID, description, and brand
    return fdc_id, chosen_description, chosen_brand

def get_nutrition_data(fdc_id, api_key):
     # Builds URL for detailed nutrient data by FDC ID
    url = f"https://api.nal.usda.gov/fdc/v1/{fdc_id}?api_key={api_key}"
    response = requests.get(url) # Send GET request
    parsed = response.json()     # Parse JSON response

    # Nutrients we're interested in, for consistent display
    important_nutrients = {
        "Energy": "Calories",
        "Protein": "Protein",
        "Total lipid (fat)": "Total Fat",
        "Carbohydrate, by difference": "Carbohydrates"
    }

    nutrition_data = {} # Dictionary to store parsed nutrition info

    # STEP 1: Use 'foodNutrients' if available
    if 'foodNutrients' in parsed:
        for nutrient in parsed['foodNutrients']:
            name = nutrient.get('nutrient', {}).get('name', 'Unknown Nutrient')
            if name in important_nutrients:
                display_name = important_nutrients[name]
                unit = nutrient.get('nutrient', {}).get('unitName', '')
                amount = nutrient.get('amount', 0)

                # Ignore non-kcal values for Energy
                if name == "Energy" and unit != "kcal":
                    continue

                # Skip absurd calorie values
                if display_name == "Calories" and amount > 1500:
                    print(f"Skipping unreasonable calorie value: {amount} kcal")
                    continue

                nutrition_data[display_name] = f"{amount} {unit}"

    # STEP 2: Fallback to 'labelNutrients' if 'foodNutrients' was empty
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

    # STEP 3: If we still don't have nutrition data, return None
    if not nutrition_data:
        print(f"No nutrition data found for FDC ID {fdc_id}.")
        return None, None, None

    # Estimate a realistic portion size from foodPortions
    portions = parsed.get("foodPortions", [])
    full_item_grams = None

    # Try to find a named portion (sandwich, bottle, etc.)
    for portion in portions:
        if not isinstance(portion, dict):
            continue  # Skip if portion isn't a dictionary

        modifier = portion.get("modifier", "")
        if isinstance(modifier, str) and any(keyword in modifier.lower() for keyword in ["sandwich", "burger", "container", "bottle", "burrito", "cup"]):
            full_item_grams = portion.get("gramWeight")
            break

     # If no match above, fallback to any portion > 50g
    if not full_item_grams:
        for portion in portions:
            if isinstance(portion, dict):
                grams = portion.get("gramWeight")
                if grams and grams > 50:
                    full_item_grams = grams
                    break

     # STEP 4: Scale nutrients based on portion size
    default_grams = 100
    scaling_factor = full_item_grams / default_grams if full_item_grams else 1.0

    # Inform the user if scaling was applied
    if scaling_factor != 1.0:
        print(f"Scaling nutrients by x{scaling_factor:.2f} (based on {full_item_grams}g)")

    # Adjust each nutrient value by the scaling factor
    for key in nutrition_data:
        value = nutrition_data[key]
        try:
            num, unit = value.split()
            scaled = round(float(num) * scaling_factor, 2)
            nutrition_data[key] = f"{scaled} {unit}"
        except Exception:
            print(f"Could not parse value for {key}: {value}")

    # Return final nutrition dictionary (and 2 unused placeholders)
    return nutrition_data, None, None
