import sqlite3
import datetime
import csv

# Importing USDA API functions from main.py
from main import get_fdc_id, get_nutrition_data

class CalorieCounter:
    def __init__(self, db_name="calorie_tracker.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._setup_db()

    def _setup_db(self):
        """Creates necessary tables if they don't exist."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            goal_weight REAL,
            weekly_weight_loss REAL,
            activity_level TEXT,
            gender TEXT,
            birthday TEXT,
            weight REAL,
            height REAL
        )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS meal_log (
            id INTEGER PRIMARY KEY,
            date TEXT,
            meal_name TEXT,
            calories INTEGER,
            fat REAL,
            carbohydrates REAL,
            protein REAL
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS daily_log (
            date TEXT PRIMARY KEY,
            calories_consumed INTEGER,
            weight REAL
        )''')
        self.conn.commit()

    def log_daily_summary(self):
        """Logs daily calories and weight into the daily_log table."""
        today = datetime.date.today().isoformat()
        calories_today = self.get_calories_today()
        user_profile = self.get_user_profile()
        current_weight = user_profile[6] if user_profile else None

        self.cursor.execute("""
            INSERT INTO daily_log (date, calories_consumed, weight)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
            calories_consumed = excluded.calories_consumed,
            weight = excluded.weight
        """, (today, calories_today, current_weight))
        self.conn.commit()

    def view_daily_log(self):
        """Displays the daily log for calories and weight."""
        self.cursor.execute("SELECT date, calories_consumed, weight FROM daily_log ORDER BY date")
        logs = self.cursor.fetchall()

        if logs:
            print("\nDate         | Calories Consumed | Weight (lbs)")
            print("------------------------------------------------")
            for log in logs:
                print(f"{log[0]}   | {log[1]}              | {log[2]}")
        else:
            print("No daily logs found.")

    def export_log_to_csv(self):
        """Exports the daily log to a CSV file."""
        self.cursor.execute("SELECT date, calories_consumed, weight FROM daily_log ORDER BY date")
        logs = self.cursor.fetchall()

        if logs:
            with open("daily_log_export.csv", "w", newline="") as csvfile:
                fieldnames = ["Date", "Calories Consumed", "Weight (lbs)"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for log in logs:
                    writer.writerow({"Date": log[0], "Calories Consumed": log[1], "Weight (lbs)": log[2]})

            print("Log exported to daily_log_export.csv!")
        else:
            print("No data available to export.")

    def set_user_profile(self, goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height):
        """Stores user profile in the database."""
        self.cursor.execute("DELETE FROM user_profile")  # Ensure only one user profile exists
        self.cursor.execute('''INSERT INTO user_profile 
                              (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height))
        self.conn.commit()

    def update_weight(self, new_weight):
        """Updates the user's weight and logs the daily summary."""
        self.cursor.execute("UPDATE user_profile SET weight = ? WHERE id = 1", (new_weight,))
        self.conn.commit()
        print("Weight updated successfully!")

        self.log_daily_summary()

    def get_user_profile(self):
        """Fetches the user profile."""
        self.cursor.execute("SELECT * FROM user_profile LIMIT 1")
        return self.cursor.fetchone()

    def log_meal(self):
        """Logs a meal, allowing the user to enter manually or search USDA API."""
        today = datetime.date.today().isoformat()
        use_api = input("Would you like to search for a meal using the USDA API? (yes/no): ").strip().lower()

        if use_api == "yes":
            food_name = input("Enter food name to search: ").strip()
            api_key = '0bxYWP3iH2bW7psubPM6SkbxOL7p4fdynk66Np6b'

            # Fetch FDC ID
            fdc_id, chosen_description, chosen_brand = get_fdc_id(food_name, api_key)

            if not fdc_id:
                print("No matching food found. Please try again.")
                return

            # Get nutrition data
            nutrition, serving_size, serving_unit = get_nutrition_data(fdc_id, api_key)

            if not nutrition:
                print("Could not retrieve nutrition data. Please try again.")
                return

            # Extract relevant nutrition values
            meal_name = f"{chosen_description} ({chosen_brand})"
            calories = int(float(nutrition.get("Calories", "0 kcal").split()[0]))
            fat = float(nutrition.get("Total Fat", "0 g").split()[0])
            carbohydrates = float(nutrition.get("Carbohydrates", "0 g").split()[0])
            protein = float(nutrition.get("Protein", "0 g").split()[0])

            print(f"\nLogging: {meal_name}")
            print(f"Calories: {calories} kcal, Fat: {fat} g, Carbs: {carbohydrates} g, Protein: {protein} g")

        else:
            # Manual meal entry
            meal_name = input("Enter meal name: ").strip()
            calories = int(input("Enter calories: ").strip())
            fat = float(input("Enter fat (g): ").strip())
            carbohydrates = float(input("Enter carbohydrates (g): ").strip())
            protein = float(input("Enter protein (g): ").strip())

        # Save meal to database
        self.cursor.execute('''INSERT INTO meal_log (date, meal_name, calories, fat, carbohydrates, protein)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (today, meal_name, calories, fat, carbohydrates, protein))
        self.conn.commit()

        print("Meal logged successfully!")

    def get_calories_today(self):
        """Calculates the total calories consumed today."""
        today = datetime.date.today().isoformat()
        self.cursor.execute("SELECT SUM(calories) FROM meal_log WHERE date = ?", (today,))
        result = self.cursor.fetchone()
        return result[0] if result[0] else 0

    def calculate_daily_calories(self):
        """Determines the number of calories the user should consume daily based on profile and goals."""
        profile = self.get_user_profile()
        if not profile:
            return None

        _, goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height = profile
        
        # Basal Metabolic Rate (BMR) Calculation
        if gender.lower() == "male":
            bmr = 10 * (weight / 2.20462) + 6.25 * height - 5 * self._calculate_age(birthday) + 5
        else:
            bmr = 10 * (weight / 2.20462) + 6.25 * height - 5 * self._calculate_age(birthday) - 161

        # Activity level multiplier
        activity_multipliers = {
            "not active": 1.2,
            "somewhat active": 1.375,
            "highly active": 1.55,
            "extremely active": 1.725
        }
        bmr *= activity_multipliers.get(activity_level.lower(), 1.2)

        # Adjust for weight loss/gain
        daily_deficit = min((weekly_weight_loss * 7700) / 7, bmr * 0.2)  # 7700 kcal per kg
        daily_calories = bmr - daily_deficit

        return round(daily_calories, 2)

    def _calculate_age(self, birthday):
        """Calculates age based on birthday."""
        birth_date = datetime.datetime.strptime(birthday, "%m-%d-%Y").date()
        today = datetime.date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def run_cli(self):
        """Runs a command-line interface for user interaction."""
        self.log_daily_summary()
        
        while True:
            print("\nCalorie Tracker Menu")
            print("1. Set User Profile")
            print("2. Log a Meal")
            print("3. View Today's Calorie Intake")
            print("4. View Recommended Daily Calories")
            print("5. Update Weight")
            print("6. View Daily Log")
            print("7. Export Daily Log to CSV")
            print("8. Exit")

            choice = input("Enter choice: ").strip()
            print(f"DEBUG: choice received -> {choice}")

            if choice == "1":
                goal_weight = float(input("Enter goal weight (lbs): ").strip())
                weekly_weight_loss = float(input("Enter weekly weight loss goal (choose from: 0.5, 1, 1.5, 2 lbs): ").strip())
                activity_level = input("Enter activity level (Not Active, Somewhat Active, Highly Active, Extremely Active): ").strip()
                gender = input("Enter gender (male/female): ").strip()
                birthday = input("Enter birthday (MM-DD-YYYY, e.g., 08-10-2002): ").strip()
                weight = float(input("Enter current weight (lbs): ").strip())
                height_ft, height_in = map(int, input("Enter height (feet and inches, separated by a space, e.g., '6 1'): ").strip().split())
                height = (height_ft * 12 + height_in) * 2.54
                self.set_user_profile(goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
                print("User profile set successfully!")

            elif choice == "2":
                self.log_meal()

            elif choice == "3":
                print(f"Total Calories consumed today: {self.get_calories_today()} Calories")

            elif choice == "4":
                print(f"Recommended daily Calorie intake: {self.calculate_daily_calories()} Calories")

            elif choice == "5":
                new_weight = float(input("Enter new weight (lbs): ").strip())
                self.update_weight(new_weight)

            elif choice == "6":
                self.view_daily_log()

            elif choice == "7":
                self.export_log_to_csv()

            elif choice == "8":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    calorie_tracker = CalorieCounter()
    calorie_tracker.run_cli()
