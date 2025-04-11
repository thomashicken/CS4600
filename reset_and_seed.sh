#!/bin/bash

echo "Resetting and simulating user interactions..."

# Remove old database, CSV files, and PNG images
rm -f calorie_tracker.db daily_log_export.csv *.png

# Run Python script to seed the database
python3 - <<EOF
import sqlite3
import datetime

# Connect to SQLite database
conn = sqlite3.connect("calorie_tracker.db")
cursor = conn.cursor()

# Recreate user_profile table
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

# Insert user profile
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

# Insert meals over 3 days
today = datetime.date.today()
meal_data = [
    (str(today - datetime.timedelta(days=2)), 'Oatmeal', 300, 5, 40, 10),
    (str(today - datetime.timedelta(days=2)), 'Grilled Chicken', 450, 10, 30, 40),
    (str(today - datetime.timedelta(days=1)), 'Steak Dinner', 700, 20, 50, 50),
    (str(today - datetime.timedelta(days=1)), 'Protein Shake', 250, 5, 20, 30),
    (str(today), 'Salmon', 600, 15, 20, 50),
    (str(today), 'Rice & Beans', 500, 10, 80, 25)
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

# Insert daily logs
daily_logs = [
    (str(today - datetime.timedelta(days=2)), 750, 200),
    (str(today - datetime.timedelta(days=1)), 950, 199),
    (str(today), 1100, 198)
]
cursor.executemany('''
INSERT INTO daily_log (date, calories_consumed, weight)
VALUES (?, ?, ?)
''', daily_logs)

# Commit and close
conn.commit()
conn.close()

print("Database setup complete. User data and meal logs inserted.")
EOF

# **Simulate user interaction using `expect` (Single Session)**
echo "Simulating user interactions over multiple days..."

expect <<EOF
spawn python3 calorie_counter.py

# View today's calorie intake
expect "Enter choice:"
send "3\r"

# Update weight
expect "Enter choice:"
send "5\r"
expect "Enter new weight (lbs):"
send "197\r"

# View daily log
expect "Enter choice:"
send "6\r"

# Log a meal
expect "Enter choice:"
send "2\r"
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

# View recommended daily calorie intake
expect "Enter choice:"
send "4\r"

# View the Nutrition Pie Chart (macronutrients)
expect "Enter choice:"
send "8\r"

# Wait for the chart to be saved
sleep 2

# View the Calorie Intake vs. Goal Pie Chart
expect "Enter choice:"
send "9\r"

# Wait for the chart to be saved
sleep 2

# Exit program
expect "Enter choice:"
send "10\r"

expect eof
EOF

echo "Nutrition breakdown chart saved. Check the PNG file in the directory."
echo "Calorie intake chart saved. Check the PNG file in the directory."
echo "User simulation complete!"
