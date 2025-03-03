import requests
import json

api_key = '0bxYWP3iH2bW7psubPM6SkbxOL7p4fdynk66Np6b'

# Define only the nutrients we care about
important_nutrients = {
    "Energy": "Calories",
    "Protein": "Protein",
    "Total lipid (fat)": "Total Fat",
    "Fatty acids, total saturated": "Saturated Fat",
    "Carbohydrate, by difference": "Carbohydrates",
    "Fiber, total dietary": "Fiber",
    "Total Sugars": "Sugars",
    "Sodium, Na": "Sodium",
    "Cholesterol": "Cholesterol"
}

def get_fdc_id(food_name, api_key):
    url = f"https://api.nal.usda.gov/fdc/v1/search?api_key={api_key}"
    data = {"generalSearchInput": food_name}
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
    parsed = response.json()

    if 'error' in parsed:
        print(f"❌ API Error: {parsed['error'].get('message', 'Unknown error')}")
        return None, None, None

    if 'foods' not in parsed or not parsed['foods']:
        print(f"⚠️ No results found for '{food_name}'. Try a more specific name (e.g., 'red apple').")
        return None, None, None

    # Display the top search results
    print(f"\n🔍 Search results for '{food_name}':")
    for i, food in enumerate(parsed['foods'][:5]):  # Show top 5 results
        brand = food.get('brandOwner', 'Generic/Unknown')
        print(f"{i+1}. {food['description']} (Brand: {brand}, FDC ID: {food['fdcId']})")

    # Automatically select the first result
    chosen_food = parsed['foods'][0]
    fdc_id = chosen_food['fdcId']
    chosen_description = chosen_food['description']
    chosen_brand = chosen_food.get('brandOwner', 'Generic/Unknown')

    # Print the selected food explicitly
    print(f"\n✅ Chosen food: {chosen_description} (Brand: {chosen_brand}, FDC ID: {fdc_id})")

    return fdc_id, chosen_description, chosen_brand

def get_nutrition_data(fdc_id, api_key):
    url = f"https://api.nal.usda.gov/fdc/v1/{fdc_id}?api_key={api_key}"
    response = requests.get(url)
    parsed = response.json()

    if 'foodNutrients' not in parsed:
        print(f"No nutrition data found for FDC ID {fdc_id}.")
        return None

    # Extract serving size if available
    serving_size = parsed.get("servingSize", None)
    serving_unit = parsed.get("servingSizeUnit", "g")  # Default to grams if not specified

    nutrition_data = {}
    for nutrient in parsed['foodNutrients']:
        name = nutrient.get('nutrient', {}).get('name', 'Unknown Nutrient')
        if name in important_nutrients:
            display_name = important_nutrients[name]
            amount = nutrient.get('amount', 0)
            unit = nutrient.get('nutrient', {}).get('unitName', '')
            nutrition_data[display_name] = f"{amount} {unit}"

    return nutrition_data, serving_size, serving_unit
