#!/bin/bash

echo "Resetting and seeding database for testing..."

# Remove old database and CSV
echo "Removing old database and CSV..."
rm -f calorie_tracker.db daily_log_export.csv

# Run Python setup for dummy data
echo "Setting up dummy data..."
python3 - <<EOF
import sqlite3
import datetime

# Connect to new SQLite database
conn = sqlite3.connect("calorie_tracker.db")
cursor = conn.cursor()

# Recreate user profile
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

# Insert dummy user profile
cursor.execute('''
INSERT INTO user_profile (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
VALUES (180, 1.0, 'Somewhat Active', 'male', '08-10-2002', 200, 177.8)
''')

# Recreate meal_log table
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

# Insert dummy meal data (3 days of meals)
today = datetime.date.today()
meal_data = [
    (str(today), 'Chicken Salad', 400, 10, 20, 30),
    (str(today), 'Oatmeal', 300, 5, 40, 10),
    (str(today), 'Grilled Salmon', 600, 20, 10, 40),
    (str(today), 'Protein Shake', 400, 5, 30, 25),
    (str(today - datetime.timedelta(days=1)), 'Pasta', 700, 15, 80, 20),
    (str(today - datetime.timedelta(days=2)), 'Grilled Salmon', 600, 20, 10, 40)
]
cursor.executemany('''
INSERT INTO meal_log (date, meal_name, calories, fat, carbohydrates, protein)
VALUES (?, ?, ?, ?, ?, ?)
''', meal_data)

# Recreate daily_log table
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_log (
    date TEXT PRIMARY KEY,
    calories_consumed INTEGER,
    weight REAL
)
''')

# Insert dummy daily logs (3 days)
daily_logs = [
    (str(today - datetime.timedelta(days=1)), 2200, 202),
    (str(today - datetime.timedelta(days=2)), 2000, 201),
    (str(today), 700, 200)
]
cursor.executemany('''
INSERT INTO daily_log (date, calories_consumed, weight)
VALUES (?, ?, ?)
''', daily_logs)

# Commit changes and close
conn.commit()
conn.close()

print("Dummy data seeded successfully!")
EOF

# Run the application
echo "Launching calorie_counter.py..."
python3 calorie_counter.py
