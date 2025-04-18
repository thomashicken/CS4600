#!/bin/bash

# echo "Resetting and seeding database with realistic data (12 months)..."

# Remove old files
rm -f calorie_tracker.db daily_log_export.csv *.png

# Run embedded Python script to create realistic data
python3 - <<EOF
import sqlite3
import datetime
import random

conn = sqlite3.connect("counter.db")
cursor = conn.cursor()

# Config
start_weight = 250.0
goal_weight = 180.0
height_cm = 185.42  # ~6'1"
gender = "male"
activity_level = "somewhat active"
weekly_weight_loss = 1.5
birthday = "08-10-2002"
days = 365
start_date = datetime.date.today() - datetime.timedelta(days=days - 1)

# Reset tables
cursor.execute("DROP TABLE IF EXISTS user_profile")
cursor.execute("DROP TABLE IF EXISTS meal_log")
cursor.execute("DROP TABLE IF EXISTS exercise_log")
cursor.execute("DROP TABLE IF EXISTS daily_log")

cursor.execute('''
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY,
    goal_weight REAL,
    weekly_weight_loss REAL,
    activity_level TEXT,
    gender TEXT,
    birthday TEXT,
    weight REAL,
    height REAL
)
''')
cursor.execute('''
INSERT INTO user_profile (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', (goal_weight, weekly_weight_loss, activity_level, gender, birthday, start_weight, height_cm))

cursor.execute('''
CREATE TABLE meal_log (
    id INTEGER PRIMARY KEY,
    date TEXT,
    meal_name TEXT,
    calories INTEGER,
    fat REAL,
    carbohydrates REAL,
    protein REAL
)
''')
cursor.execute('''
CREATE TABLE exercise_log (
    id INTEGER PRIMARY KEY,
    date TEXT,
    exercise_name TEXT,
    duration_minutes INTEGER,
    calories_burned INTEGER
)
''')
cursor.execute('''
CREATE TABLE daily_log (
    date TEXT PRIMARY KEY,
    calories_consumed INTEGER,
    weight REAL,
    calories_burned INTEGER DEFAULT 0
)
''')

meals = [
    ("Oatmeal", 300, 5, 40, 10),
    ("Grilled Chicken", 450, 10, 30, 40),
    ("Salmon", 600, 15, 20, 50),
    ("Rice & Beans", 500, 10, 80, 25),
    ("Protein Shake", 250, 5, 20, 30),
    ("Veggie Wrap", 350, 7, 45, 15),
    ("Burger", 700, 40, 50, 35),
    ("Pasta", 650, 15, 70, 20),
    ("Tuna Sandwich", 400, 10, 30, 35)
]

exercises = [
    ("running", 30, 300),
    ("cycling", 45, 360),
    ("yoga", 60, 180),
    ("weightlifting", 40, 250),
    ("hiking", 50, 320),
    ("basketball", 45, 400),
    ("walking", 60, 240)
]

for i in range(days):
    date = start_date + datetime.timedelta(days=i)
    str_date = str(date)

    expected_loss = (i / days) * (start_weight - goal_weight)
    fluctuation = random.uniform(-0.4, 0.4)
    current_weight = round(start_weight - expected_loss + fluctuation, 1)

    # Meals
    k = random.choice([2, 3])
    meals_today = random.sample(meals, k=k)
    total_calories = 0
    for meal in meals_today:
        cursor.execute('''
            INSERT INTO meal_log (date, meal_name, calories, fat, carbohydrates, protein)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str_date, *meal))
        total_calories += meal[1]

    # Exercise every 2–3 days
    calories_burned = 0
    if i % random.choice([2, 3]) == 0:
        exercise = random.choice(exercises)
        cursor.execute('''
            INSERT INTO exercise_log (date, exercise_name, duration_minutes, calories_burned)
            VALUES (?, ?, ?, ?)
        ''', (str_date, *exercise))
        calories_burned = exercise[2]

    # Daily log
    cursor.execute('''
        INSERT INTO daily_log (date, calories_consumed, weight, calories_burned)
        VALUES (?, ?, ?, ?)
    ''', (str_date, total_calories, current_weight, calories_burned))

conn.commit()
conn.close()
# print("Database seeded with 365 days of realistic weight loss progress.")
EOF

# Simulate CLI interactions including exercise logging
echo "Simulating user interactions..."

expect <<EOF
spawn python3 main.py

# View personalized health plan
expect "Enter choice:"
send "2\r"

# View today's calorie intake
expect "Enter choice:"
send "6\r"

# Update weight
expect "Enter choice:"
send "8\r"
expect "Enter new weight (lbs):"
send "180\r"

# View daily log
expect "Enter choice:"
send "9\r"
expect "Would you like to see all past days?"
send "no\r"

# Edit a meal
expect "Would you like to edit or delete a meal?"
send "edit\r"
expect "Enter Meal ID to edit:"
send "1\r"
expect "New meal name:"
send "Updated Salmon\r"
expect "New calories (leave blank to keep current):"
send "\r"
expect "New fat (g) (leave blank to keep current):"
send "12\r"
expect "New carbohydrates (g) (leave blank to keep current):"
send "\r"
expect "New protein (g) (leave blank to keep current):"
send "55\r"

# Log a meal
expect "Enter choice:"
send "5\r"
expect "Would you like to search for a meal using the USDA API? (yes/no):"
send "no\r"
expect "Enter meal name:"
send "Lunch Burrito\r"
expect "Enter calories:"
send "650\r"
expect "Enter fat (g):"
send "20\r"
expect "Enter carbohydrates (g):"
send "60\r"
expect "Enter protein (g):"
send "35\r"

# Log an exercise
expect "Enter choice:"
send "14\r"
expect "Enter exercise name:"
send "running\r"
expect "Enter duration in minutes:"
send "20\r"

# View log again and delete a meal
expect "Enter choice:"
send "9\r"
expect "Would you like to see all past days?"
send "no\r"
expect "Would you like to edit or delete a meal?"
send "delete\r"
expect "Enter Meal ID to delete:"
send "3\r"

# View progress graph
expect "Enter choice:"
send "13\r"

# Log another exercise
expect "Enter choice:"
send "14\r"
expect "Enter exercise name:"
send "running\r"
expect "Enter duration in minutes:"
send "20\r"

# Exit
expect "Enter choice:"
send "15\r"

expect eof
EOF

echo "User simulation complete!"
