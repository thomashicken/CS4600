# Calorie Counter – by Thomas Hicken

A personalized health management system to help users track their meals, monitor progress, and build realistic nutrition plans based on their goals.

---

## Motivation

Making a change in your health is hard. I built this application to make that process easier, by providing a realistic daily plan and transparent tracking tools so users always know where they stand.

---

## Features

### Personalized Health Plan
- Calculates a custom Daily Calorie Budget
- Estimates Time to Reach Goal
- Provides Suggested Macronutrient Ranges

### Visual Insights
- Nutrition Breakdown Pie Chart
- Calorie Intake vs Budget Pie Chart
- Weight Progress Graph

### Logging & Tracking
- Log meals manually or search the USDA FoodData Central API
- Log exercises from a list of 20+ common activities
- View or edit daily meal & exercise logs
- Export full history to CSV
- Edit or update your health profile any time

---

## Interesting Algorithmic Feature

### USDA FoodData Central API Integration
- Users can search for meals using the USDA database
- Results display brand and nutritional info (calories, fat, carbs, protein)
- Values are adjusted for quantity and portion size
- All entries are stored in an SQLite database
- Based on [afogarty85/fooddata_central](https://github.com/afogarty85/fooddata_central)

---

## Database Schema (SQLite)

```sql
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY,
    goal_weight REAL,
    weekly_weight_loss REAL,
    activity_level TEXT,
    gender TEXT,
    birthday TEXT,
    weight REAL,
    height REAL
);

CREATE TABLE meal_log (
    id INTEGER PRIMARY KEY,
    date TEXT,
    meal_name TEXT,
    calories INTEGER,
    fat REAL,
    carbohydrates REAL,
    protein REAL
);

CREATE TABLE exercise_log (
    id INTEGER PRIMARY KEY,
    date TEXT,
    exercise_name TEXT,
    duration_minutes INTEGER,
    calories_burned INTEGER
);

CREATE TABLE daily_log (
    date TEXT PRIMARY KEY,
    calories_consumed INTEGER,
    weight REAL,
    calories_burned INTEGER DEFAULT 0
);
```

---

## REST Endpoints

Not applicable, this is a CLI-based tool. Web/Mobile endpoints may be implemented in future versions.

---

## Security & Authentication

Local-only project. No user credentials or password hashing required.

---

## Getting Started

### Requirements
- Python 3.8+
- `matplotlib`
- `requests`

Install dependencies:

```bash
pip install matplotlib requests
```

### Running the App

```bash
python main.py
```

---

## File Structure

- `main.py`: Entry point for CLI
- `counter.py`: Main app logic (health plan, logging, graphing)
- `food_data.py`: USDA API integration
- `db.py`: SQLite database schema and initialization
- `input_helpers.py`: CLI input validation
- `constants.py`: Calories burned per exercise type

---

## Future Plans

- Convert to a Web or Mobile App
- Add muscle-building support (protein goals, workout suggestions)
- Allow on-the-go logging and chart viewing

---

## Sample Visuals

Nutrition Pie Chart  
`nutrition_breakdown_sample.png`

Calorie Intake vs Budget  
`calorie_intake_sample.png`

Weight Progress Graph  
`progress_graph_sample.png`

---

## Author

Thomas Hicken  
Senior Project, CS4600  
Spring 2025

---

## Getting a USDA API Key

To use the meal logging feature with automatic nutrition lookup, you'll need your own USDA API key.

### Steps:
1. Go to the USDA API signup page:  
   https://fdc.nal.usda.gov/api-key-signup.html

2. Fill out the form and submit it.

3. Once approved, you'll receive an API key via email.

4. Create a `.env` file in the root of the project and add:
   ```
   USDA_API_KEY=your_api_key_here
   ```

5. Make sure your `.env` file is **not committed** to version control (it's already in `.gitignore`).

---

## FAQ

### What is the purpose of a calorie counter?

A calorie counter helps users track how many calories they consume and burn each day. This supports goals like weight loss, maintenance, or muscle gain by giving insight into your energy balance.

If your goal is **weight loss**, the most important principle is to maintain a **calorie deficit**, meaning you consume fewer calories than you burn. This application helps you stay on track by calculating a realistic daily calorie target based on your profile and showing you how your intake compares to that target throughout the day.

---

### What are macronutrients and why do they matter?

Macronutrients, **protein**, **carbohydrates**, and **fat**, are the main sources of energy in your diet. Each plays a distinct role:
- **Protein** supports muscle repair and growth.
- **Carbohydrates** are the body's main fuel source.
- **Fat** is essential for hormones, brain health, and long-term energy.

This app visualizes your macronutrient breakdown so you can better understand the quality of your calorie intake.

---

### How does a calorie counter work?

This calorie counter uses your personal details (weight, height, gender, age, activity level, and goals) to:
- Calculate a personalized daily calorie budget
- Track meals and exercises
- Update your weight and progress over time
- Visualize trends and nutrient distribution with graphs

Meals can be logged manually or fetched from the USDA FoodData Central for more accurate nutrition information.
