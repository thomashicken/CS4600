import sqlite3
import os
import csv
from datetime import datetime

DB_FILE = "calorie_counter.db"
SCHEMA_FILE = "schema.sql"
CSV_FILE = "user_data.csv"

# Create/connect to the database and execute the schema.sql file
def setup_database():
    if not os.path.exists(SCHEMA_FILE):
        print(f"Schema file {SCHEMA_FILE} does not exist.")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Execute schema.sql to create/update the database schema
    with open(SCHEMA_FILE, 'r') as schema_file:
        schema_sql = schema_file.read()
        cursor.executescript(schema_sql)
        print("Database schema created/updated.")
    
    conn.commit()
    conn.close()

# Collect user inputs
def get_user_data():
    print("Welcome to the Calorie Counter!")
    print("Let's set up your plan and learn about you.")
    
    # Collect inputs for the plan
    goal_weight = float(input("Enter your goal weight (in pounds): "))
    weekly_weight_loss = float(input("Enter your desired weekly weight loss (in pounds): "))
    activity_level = input("Enter your activity level (low, moderate, high): ").strip().lower()

    # Collect personal details
    gender = input("Enter your gender (male/female/other): ").strip().lower()
    birthday = input("Enter your birthday (YYYY-MM-DD): ").strip()
    weight = float(input("Enter your current weight (in pounds): "))
    height = float(input("Enter your height (in inches): "))

    # Return the collected data as a dictionary
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

# Save user data to the database
def save_user_data(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_data (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height, created_at)
        VALUES (:goal_weight, :weekly_weight_loss, :activity_level, :gender, :birthday, :weight, :height, :created_at)
    """, data)
    conn.commit()
    conn.close()

# Export database data to CSV
def export_to_csv():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_data")
    rows = cursor.fetchall()
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow([description[0] for description in cursor.description])
        # Write the data
        writer.writerows(rows)
    conn.close()
    print(f"Data exported to {CSV_FILE}")

# Import data from CSV to the database
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

def main():
    # Set up the database
    setup_database()
    
    # Get user data through the interface
    user_data = get_user_data()
    
    # Save the collected data to the database
    save_user_data(user_data)
    
    print("\nThank you! Your plan has been saved successfully.")

    # Offer to export or import data
    while True:
        choice = input("\nWould you like to export or import data? (export/import/exit): ").strip().lower()
        if choice == "export":
            export_to_csv()
        elif choice == "import":
            import_from_csv()
        elif choice == "exit":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 'export', 'import', or 'exit'.")

if __name__ == "__main__":
    main()
