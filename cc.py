import sqlite3
import os
import csv
from datetime import datetime

DB_FILE = "calorie_counter.db"
SCHEMA_FILE = "schema.sql"
CSV_FILE = "user_data.csv"

# Setup database
def setup_database():
    if not os.path.exists(SCHEMA_FILE):
        print(f"Schema file {SCHEMA_FILE} does not exist.")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    with open(SCHEMA_FILE, 'r') as schema_file:
        schema_sql = schema_file.read()
        cursor.executescript(schema_sql)
        print("Database schema created/updated.")
    
    conn.commit()
    conn.close()

# Collect user information
def get_user_data():
    print("\nWelcome to the Calorie Counter!")
    print("Let's set up your plan and learn about you.")
    
    goal_weight = float(input("Enter your goal weight (in pounds): "))
    weekly_weight_loss = float(input("Enter your desired weekly weight loss (in pounds): "))
    activity_level = input("Enter your activity level (low, moderate, high): ").strip().lower()

    gender = input("Enter your gender (male/female/other): ").strip().lower()
    birthday = input("Enter your birthday (YYYY-MM-DD): ").strip()
    weight = float(input("Enter your current weight (in pounds): "))
    height = float(input("Enter your height (in inches): "))

    return {
        "goal_weight": goal_weight,
        "weekly_weight_loss": weekly_weight_loss,
        "activity_level": activity_level,
        "gender": gender,
        "birthday": birthday,
        "weight": weight,
        "height": height,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Save user data
def save_user_data(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_data (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height, created_at)
        VALUES (:goal_weight, :weekly_weight_loss, :activity_level, :gender, :birthday, :weight, :height, :created_at)
    """, data)
    user_id = cursor.lastrowid  # Get the newly inserted user's ID
    conn.commit()
    conn.close()
    return user_id

# List available preset foods
def list_preset_foods():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description FROM foods")
    foods = cursor.fetchall()
    conn.close()

    if not foods:
        print("\nNo preset foods found in the database.")
        return []

    print("\nAvailable Preset Foods:")
    for food in foods:
        print(f"{food[0]}. {food[1]}")
    
    return foods

# Log food intake
def log_food(user_id):
    print("\nDo you want to log a preset food or enter a custom food?")
    choice = input("Enter 'preset' for preset foods or 'custom' for custom entry: ").strip().lower()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if choice == "preset":
        foods = list_preset_foods()
        if not foods:
            print("No foods available. Please enter a custom food instead.")
            choice = "custom"
        else:
            food_id = int(input("Enter the food ID to log: "))
            quantity = float(input("Enter quantity: "))
            unit = input("Enter unit (g, oz, cup, etc.): ").strip()

            cursor.execute("""
                INSERT INTO logged_foods (user_id, food_id, quantity, unit, date_logged)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, food_id, quantity, unit, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    if choice == "custom":
        custom_food = input("Enter the name of your food: ").strip()
        quantity = float(input("Enter quantity: "))
        unit = input("Enter unit (g, oz, cup, etc.): ").strip()

        cursor.execute("""
            INSERT INTO logged_foods (user_id, custom_food, quantity, unit, date_logged)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, custom_food, quantity, unit, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    print("Food logged successfully!")

# Export user data
def export_to_csv():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_data")
    rows = cursor.fetchall()
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([description[0] for description in cursor.description])  # Header
        writer.writerows(rows)
    conn.close()
    print(f"Data exported to {CSV_FILE}")

# Import user data
def import_from_csv():
    if not os.path.exists(CSV_FILE):
        print(f"{CSV_FILE} does not exist.")
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    with open(CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            cursor.execute("""
                INSERT INTO user_data (id, goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
    conn.commit()
    conn.close()
    print("Data imported from CSV")

# Main function with menu
def main():
    setup_database()

    user_id = None

    while True:
        print("\nMenu:")
        print("1. Create New Plan")
        print("2. Log a Meal")
        print("3. Export Data")
        print("4. Import Data")
        print("5. Exit")
        
        choice = input("Select an option: ").strip()
        
        if choice == "1":
            print("\nStarting a new plan...")
            user_data = get_user_data()
            user_id = save_user_data(user_data)
            print("\nYour new plan has been saved successfully!")
        
        elif choice == "2":
            if user_id:
                log_food(user_id)
            else:
                print("No active user. Please create a plan first.")
        
        elif choice == "3":
            export_to_csv()
        
        elif choice == "4":
            import_from_csv()
        
        elif choice == "5":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter a number from 1 to 5.")

if __name__ == "__main__":
    main()
