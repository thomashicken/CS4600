#!/bin/bash

echo "Resetting and simulating user interactions..."

# Remove old database, CSV files, and PNG images
rm -f calorie_tracker.db daily_log_export.csv *.png

# Run Python script to seed the database
python3 - <<EOF
import sqlite3
import datetime
import random

conn = sqlite3.connect("calorie_tracker.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_profile (
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
cursor.execute("DELETE FROM user_profile")
cursor.execute('''
INSERT INTO user_profile (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
VALUES (180, 1.5, 'Somewhat Active', 'male', '08-10-2002', 200, 177.8)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS meal_log (
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
CREATE TABLE IF NOT EXISTS exercise_log (
    id INTEGER PRIMARY KEY,
    date TEXT,
    exercise_name TEXT,
    duration_minutes INTEGER,
    calories_burned INTEGER
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_log (
    date TEXT PRIMARY KEY,
    calories_consumed INTEGER,
    weight REAL,
    calories_burned INTEGER DEFAULT 0
)
''')

# Sample meals and exercises
meals = [
    ("Oatmeal", 300, 5, 40, 10),
    ("Grilled Chicken", 450, 10, 30, 40),
    ("Salmon", 600, 15, 20, 50),
    ("Rice & Beans", 500, 10, 80, 25),
    ("Protein Shake", 250, 5, 20, 30),
    ("Veggie Wrap", 350, 7, 45, 15)
]
exercises = [
    ("running", 30, 300),
    ("cycling", 45, 360),
    ("yoga", 60, 180),
    ("weightlifting", 40, 250),
    ("hiking", 50, 320)
]

# Generate 90 days of logs
start_date = datetime.date.today() - datetime.timedelta(days=89)
weight = 200.0

for i in range(90):
    date = start_date + datetime.timedelta(days=i)
    str_date = str(date)

    # Weight decreases gradually with some variation
    weight_loss = i * (20 / 89)  # 20 lbs over 89 days
    daily_fluctuation = random.uniform(-0.2, 0.2)
    current_weight = round(weight - weight_loss + daily_fluctuation, 1)

    # Log 1-2 meals per day
    meals_today = random.sample(meals, k=random.choice([1, 2]))
    total_calories = 0
    for meal in meals_today:
        cursor.execute('''
            INSERT INTO meal_log (date, meal_name, calories, fat, carbohydrates, protein)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str_date, meal[0], meal[1], meal[2], meal[3], meal[4]))
        total_calories += meal[1]

    # Exercise every 2–3 days
    calories_burned = 0
    if i % random.choice([2, 3]) == 0:
        exercise = random.choice(exercises)
        cursor.execute('''
            INSERT INTO exercise_log (date, exercise_name, duration_minutes, calories_burned)
            VALUES (?, ?, ?, ?)
        ''', (str_date, exercise[0], exercise[1], exercise[2]))
        calories_burned = exercise[2]

    cursor.execute('''
        INSERT INTO daily_log (date, calories_consumed, weight, calories_burned)
        VALUES (?, ?, ?, ?)
    ''', (str_date, total_calories, current_weight, calories_burned))

conn.commit()
conn.close()
print("Database setup complete. 3 months of historical user data inserted.")
EOF

# Simulate CLI interactions including exercise logging
echo "Simulating user interactions..."

expect <<EOF
spawn python3 calorie_counter.py

# View today's calorie intake
expect "Enter choice:"
send "5\r"

# Update weight
expect "Enter choice:"
send "7\r"
expect "Enter new weight (lbs):"
send "197\r"

# View daily log
expect "Enter choice:"
send "8\r"
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
send "4\r"
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
send "13\r"
expect "Enter exercise name:"
send "running\r"
expect "Enter duration in minutes:"
send "20\r"

# View log again and delete a meal
expect "Enter choice:"
send "8\r"
expect "Would you like to see all past days?"
send "no\r"
expect "Would you like to edit or delete a meal?"
send "delete\r"
expect "Enter Meal ID to delete:"
send "3\r"

# View progress graph
expect "Enter choice:"
send "12\r"

# Log an exercise
expect "Enter choice:"
send "13\r"
expect "Enter exercise name:"
send "running\r"
expect "Enter duration in minutes:"
send "20\r"

# Exit
expect "Enter choice:"
send "14\r"

expect eof
EOF

echo "User simulation complete!"
