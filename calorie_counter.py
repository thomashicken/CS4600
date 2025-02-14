import sqlite3
import datetime

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
        self.conn.commit()

    def set_user_profile(self, goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height):
        """Stores user profile in the database."""
        self.cursor.execute("DELETE FROM user_profile")  # Ensure only one user profile exists
        self.cursor.execute('''INSERT INTO user_profile 
                              (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height))
        self.conn.commit()

    def update_weight(self, new_weight):
        """Updates the user's weight in the database."""
        self.cursor.execute("UPDATE user_profile SET weight = ? WHERE id = 1", (new_weight,))
        self.conn.commit()
        print("Weight updated successfully!")

    def get_user_profile(self):
        """Fetches the user profile."""
        self.cursor.execute("SELECT * FROM user_profile LIMIT 1")
        return self.cursor.fetchone()

    def log_meal(self, meal_name, calories, fat, carbohydrates, protein):
        """Logs a meal entry for the current date."""
        today = datetime.date.today().isoformat()
        self.cursor.execute('''INSERT INTO meal_log (date, meal_name, calories, fat, carbohydrates, protein)
                              VALUES (?, ?, ?, ?, ?, ?)''',
                            (today, meal_name, calories, fat, carbohydrates, protein))
        self.conn.commit()

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
            bmr = 10 * (weight / 2.20462) + 6.25 * (height * 30.48) - 5 * self._calculate_age(birthday) + 5
        else:
            bmr = 10 * (weight / 2.20462) + 6.25 * (height * 30.48) - 5 * self._calculate_age(birthday) - 161

        # Activity level multiplier
        activity_multipliers = {
            "sedentary": 1.2,
            "lightly active": 1.375,
            "moderately active": 1.55,
            "very active": 1.725,
            "extra active": 1.9
        }
        bmr *= activity_multipliers.get(activity_level.lower(), 1.2)

        # Adjust for weight loss/gain
        daily_deficit = (weekly_weight_loss * 7700) / 7  # 7700 kcal per kg
        daily_calories = bmr - daily_deficit

        return round(daily_calories, 2)

    def _calculate_age(self, birthday):
        """Calculates age based on birthday."""
        birth_date = datetime.datetime.strptime(birthday, "%Y-%m-%d").date()
        today = datetime.date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def run_cli(self):
        """Runs a command-line interface for user interaction."""
        while True:
            print("\nCalorie Tracker Menu")
            print("1. Set User Profile")
            print("2. Log a Meal")
            print("3. View Today's Calorie Intake")
            print("4. View Recommended Daily Calories")
            print("5. Update Weight")
            print("6. Exit")
            choice = input("Enter choice: ")

            if choice == "1":
                goal_weight = float(input("Enter goal weight (lbs): "))
                weekly_weight_loss = float(input("Enter weekly weight loss goal (lbs): "))
                activity_level = input("Enter activity level (sedentary, lightly active, moderately active, very active, extra active): ")
                gender = input("Enter gender (male/female): ")
                birthday = input("Enter birthday (YYYY-MM-DD): ")
                weight = float(input("Enter current weight (lbs): "))
                height = float(input("Enter height (ft): "))
                self.set_user_profile(goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
                print("User profile set successfully!")

            elif choice == "5":
                new_weight = float(input("Enter new weight (lbs): "))
                self.update_weight(new_weight)
                print(f"New recommended daily calorie intake: {self.calculate_daily_calories()} Calories")

            elif choice == "6":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    calorie_tracker = CalorieCounter()
    calorie_tracker.run_cli()