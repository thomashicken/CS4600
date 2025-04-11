import sqlite3
import datetime
import csv
import matplotlib.pyplot as plt

# Importing USDA API functions from main.py
from food_data import get_fdc_id, get_nutrition_data

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

            # Ask for quantity
            try:
                quantity = float(input(f"Enter quantity (serving size: {serving_size} {serving_unit}): ").strip())
            except ValueError:
                print("Invalid quantity. Defaulting to 1.")
                quantity = 1

            # Extract relevant nutrition values and scale by quantity
            meal_name = f"{chosen_description} ({chosen_brand})"
            calories = round(float(nutrition.get("Calories", "0 kcal").split()[0]) * quantity, 2)
            fat = round(float(nutrition.get("Total Fat", "0 g").split()[0]) * quantity, 2)
            carbohydrates = round(float(nutrition.get("Carbohydrates", "0 g").split()[0]) * quantity, 2)
            protein = round(float(nutrition.get("Protein", "0 g").split()[0]) * quantity, 2)

            print(f"\nLogging: {meal_name} (x{quantity})")
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

        _, goal_weight, weekly_weight_change, activity_level, gender, birthday, weight, height = profile

        # Basal Metabolic Rate (BMR) Calculation using Mifflin-St Jeor Equation
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

        # Adjust calories based on user's weekly weight change goal
        if weekly_weight_change > 0:
            # Weight loss
            daily_adjustment = min((weekly_weight_change * 7700) / 7, bmr * 0.2)
            daily_calories = bmr - daily_adjustment
        elif weekly_weight_change < 0:
            # Weight gain
            daily_adjustment = min((abs(weekly_weight_change) * 7700) / 7, bmr * 0.2)
            daily_calories = bmr + daily_adjustment
        else:
            # Maintain weight
            daily_calories = bmr

        # Clamp daily calories to safe limits
        daily_calories = max(min(daily_calories, 4000), 1200)
        return round(daily_calories, 2)

    def _calculate_age(self, birthday):
        """Calculates age based on birthday."""
        birth_date = datetime.datetime.strptime(birthday, "%m-%d-%Y").date()
        today = datetime.date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def show_nutrition_pie_chart(self):
        """Saves a pie chart of macronutrient consumption for today."""
        today = datetime.date.today().isoformat()
        
        # Get total daily consumption
        self.cursor.execute("""
            SELECT SUM(fat), SUM(carbohydrates), SUM(protein)
            FROM meal_log WHERE date = ?
        """, (today,))
        result = self.cursor.fetchone()
        
        # If no meals logged today
        if not result or all(value is None for value in result):
            print("No meals logged today. Nothing to display.")
            return

        fat, carbs, protein = result
        fat, carbs, protein = fat or 0, carbs or 0, protein or 0  # Handle None values

        # Data for pie chart
        labels = ['Fat', 'Carbohydrates', 'Protein']
        sizes = [fat, carbs, protein]
        colors = ['#ff9999','#66b3ff','#99ff99']
        
        # Plot
        plt.figure(figsize=(6,6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures a circular pie chart
        plt.title(f"Macronutrient Breakdown ({today})")
        
        # Save instead of showing
        filename = f"nutrition_breakdown_{today}.png"
        plt.savefig(filename)
        print(f"Nutrition breakdown saved as {filename}")

    def show_calorie_intake_pie_chart(self):
        """Saves a pie chart comparing consumed calories to daily recommended intake."""
        today = datetime.date.today().isoformat()
        calories_consumed = self.get_calories_today()
        recommended_calories = self.calculate_daily_calories() or 2000  # Default to 2000 if no profile set
        
        budget_calories = max(recommended_calories - calories_consumed, 0)
        budget_calories = round(budget_calories, 1)  # Round to 1 decimal place
        
        labels = [f'Consumed: {calories_consumed} kcal', f'Budget: {budget_calories} kcal']
        sizes = [calories_consumed, budget_calories]
        colors = ['#ff9999', '#66b3ff']
        
        plt.figure(figsize=(6,6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.axis('equal')
        plt.title(f"Calorie Intake vs. Budget ({today})")
        
        # Save the chart
        filename = f"calorie_intake_{today}.png"
        plt.savefig(filename)
        print(f"Calorie intake chart saved as {filename}")

    def run_cli(self):
        """Runs a command-line interface for user interaction."""
        self.log_daily_summary()
        
        while True:
            print("\nCalorie Counter Menu")
            print("1. Set User Profile")
            print("2. Log a Meal")
            print("3. View Today's Calorie Intake")
            print("4. View Recommended Daily Calories")
            print("5. Update Weight")
            print("6. View Daily Log")
            print("7. Export Daily Log to CSV")
            print("8. View Nutrition Breakdown (Pie Chart)")
            print("9. View Calorie Intake vs. Goal")
            print("10. Exit")

            choice = input("Enter choice: ").strip()
            print(f"DEBUG: choice received -> {choice}")

            if choice == "1":
                print("What would you like to do with this calorie counter?")
                print("Options: 'lose', 'maintain', or 'gain'")
                goal_type = input("Enter your goal: ").strip().lower()

                valid_activity_levels = {
                    "not active": 1.2,
                    "somewhat active": 1.375,
                    "highly active": 1.55,
                    "extremely active": 1.725
                }

                while True:
                    activity_level = input("Enter activity level (Not Active, Somewhat Active, Highly Active, Extremely Active): ").strip().lower()
                    if activity_level in valid_activity_levels:
                        break
                    else:
                        print("Invalid activity level. Please choose from: Not Active, Somewhat Active, Highly Active, Extremely Active.")
                
                gender = input("Enter gender (male/female): ").strip()
                birthday = input("Enter birthday (MM-DD-YYYY): ").strip()
                weight = float(input("Enter current weight (lbs): ").strip())
                height_ft, height_in = map(int, input("Enter height (feet and inches, separated by a space, e.g., '6 1'): ").strip().split())
                height = (height_ft * 12 + height_in) * 2.54

                if goal_type == "lose":
                    goal_weight = float(input("Enter goal weight (lbs): ").strip())
                    if goal_weight < 100 or goal_weight > 400:
                        print("Warning: Goal weight seems outside of typical safe bounds (100–400 lbs).")
                        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
                        if confirm != "yes":
                            print("Profile setup cancelled.")
                            return
                    while True:
                        weekly_weight_loss = float(input("How many pounds would you like to lose per week? (0.5 to 2 lbs recommended): ").strip())
                        if 0.5 <= weekly_weight_loss <= 2:
                            break
                        print("Invalid value. Please enter a number between 0.5 and 2.")

                elif goal_type == "gain":
                    goal_weight = float(input("Enter goal weight (lbs): ").strip())
                    if goal_weight < 100 or goal_weight > 400:
                        print("Warning: Goal weight seems outside of typical safe bounds (100–400 lbs).")
                        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
                        if confirm != "yes":
                            print("Profile setup cancelled.")
                            return
                    while True:
                        gain_per_week = float(input("How many pounds would you like to gain per week? (0.5 to 2 lbs recommended): ").strip())
                        if 0.5 <= gain_per_week <= 2:
                            weekly_weight_loss = -gain_per_week
                            break
                        print("Invalid value. Please enter a number between 0.5 and 2.")
                elif goal_type == "maintain":
                    goal_weight = weight  # Same as current
                    weekly_weight_loss = 0
                else:
                    print("Invalid goal type. Defaulting to 'maintain'.")
                    goal_weight = weight
                    weekly_weight_loss = 0

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
                self.show_nutrition_pie_chart()

            elif choice == "9":
                self.show_calorie_intake_pie_chart()

            elif choice == "10":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    calorie_tracker = CalorieCounter()
    calorie_tracker.run_cli()
