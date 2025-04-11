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
    url = f"https://api.nal.usda.gov/fdc/v1/{fdc_id}?api_key={api_key}"
    response = requests.get(url)
    parsed = response.json()

    if 'foodNutrients' not in parsed:
        print(f"No nutrition data found for FDC ID {fdc_id}.")
        return None, None, None

    # Extract serving size if available
    serving_size = parsed.get("servingSize")
    serving_unit = parsed.get("servingSizeUnit", "g")  # Default to grams if not specified

    if serving_size is None:
        serving_size = "100"  # Assume 100g as a default reference value
        serving_unit = "g"

    nutrition_data = {}
    for nutrient in parsed['foodNutrients']:
        name = nutrient.get('nutrient', {}).get('name', 'Unknown Nutrient')
        if name in important_nutrients:
            display_name = important_nutrients[name]
            amount = nutrient.get('amount', 0)
            unit = nutrient.get('nutrient', {}).get('unitName', '')
            nutrition_data[display_name] = f"{amount} {unit}"

    return nutrition_data, serving_size, serving_unit