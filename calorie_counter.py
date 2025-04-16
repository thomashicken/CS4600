import sqlite3
import datetime
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from food_data import get_fdc_id, get_nutrition_data

# --- Constants ---

EXERCISE_CALORIES_PER_MIN = {
    "running": 10, "walking": 3.5, "cycling": 8, "swimming": 9, "yoga": 3, "jump rope": 12,
    "elliptical": 8, "weightlifting": 6, "hiking": 7, "dancing": 6, "rowing": 7, "aerobics": 7,
    "pilates": 4, "climbing stairs": 8, "boxing": 9, "basketball": 8, "soccer": 9,
    "tennis": 7, "volleyball": 4, "skateboarding": 5
}

# --- Input Helpers ---

def get_valid_input(prompt, valid_fn, error_msg):
    while True:
        val = input(prompt).strip()
        if valid_fn(val): return val
        print(error_msg)

def get_valid_float(prompt):
    while True:
        try: return float(input(prompt).strip())
        except ValueError: print("Invalid number. Please enter a valid float.")

def get_valid_int(prompt):
    while True:
        try: return int(input(prompt).strip())
        except ValueError: print("Invalid number. Please enter a valid integer.")

def get_optional_float(prompt, default):
    val = input(prompt).strip()
    try: return float(val) if val else default
    except: return default

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
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS exercise_log (
            id INTEGER PRIMARY KEY,
            date TEXT,
            exercise_name TEXT,
            duration_minutes INTEGER,
            calories_burned INTEGER
        )''')
        # Add calories_burned to daily_log if not already
        try:
            self.cursor.execute("ALTER TABLE daily_log ADD COLUMN calories_burned INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Already exists
        self.conn.commit()

    # --- Core Profile Methods ---

    def get_user_profile(self):
        """Fetches the user profile."""
        self.cursor.execute("SELECT * FROM user_profile LIMIT 1")
        return self.cursor.fetchone()
    
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

    def _calculate_age(self, birthday):
        """Calculates age based on birthday."""
        birth_date = datetime.datetime.strptime(birthday, "%m-%d-%Y").date()
        today = datetime.date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

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
    
    # --- Daily Log Methods ---

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
    
    def get_calories_today(self):
        """Calculates the total calories consumed today."""
        today = datetime.date.today().isoformat()
        self.cursor.execute("SELECT SUM(calories) FROM meal_log WHERE date = ?", (today,))
        result = self.cursor.fetchone()
        return result[0] if result[0] else 0
    
    # --- Meal Method ---

    def log_meal(self):
        """Logs a meal, allowing the user to enter manually or search USDA API."""
        today = datetime.date.today().isoformat()
        print("Note: This app currently tracks macronutrients only (calories, fat, carbs, protein).")
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
            nutrition, _, _ = get_nutrition_data(fdc_id, api_key)

            if not nutrition:
                print("Could not retrieve nutrition data. Please try again.")
                return

            # Ask for quantity
            try:
                quantity = float(input("Enter quantity (e.g., 1 for one item, 2 for two): ").strip())
            except ValueError:
                print("Invalid quantity. Defaulting to 1.")
                quantity = 1

            # Extract relevant nutrition values and scale by quantity
            meal_name = f"{chosen_description} ({chosen_brand})"
            calories = round(float(nutrition.get("Calories", "0 cal").split()[0]) * quantity, 2)
            fat = round(float(nutrition.get("Total Fat", "0 g").split()[0]) * quantity, 2)
            carbohydrates = round(float(nutrition.get("Carbohydrates", "0 g").split()[0]) * quantity, 2)
            protein = round(float(nutrition.get("Protein", "0 g").split()[0]) * quantity, 2)

            print(f"\nLogging: {meal_name} (x{quantity})")
            print(f"Calories: {calories} cal, Fat: {fat} g, Carbs: {carbohydrates} g, Protein: {protein} g")

        else:
            # Manual meal entry
            meal_name = input("Enter meal name: ").strip()
            calories = get_valid_float("Enter calories: ")
            fat = get_valid_float("Enter fat (g): ")
            carbohydrates = get_valid_float("Enter carbohydrates (g): ")
            protein = get_valid_float("Enter protein (g): ")

        # Save meal to database
        self.cursor.execute('''INSERT INTO meal_log (date, meal_name, calories, fat, carbohydrates, protein)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (today, meal_name, calories, fat, carbohydrates, protein))
        self.conn.commit()

        print("Meal logged successfully!")

        self.log_daily_summary()

    # --- Exercise Function ---

    def log_exercise(self):
        today = datetime.date.today().isoformat()
        print("\nAvailable exercises:")
        for ex in EXERCISE_CALORIES_PER_MIN:
            print(f"- {ex}")
        exercise_name = input("Enter exercise name: ").strip().lower()
        if exercise_name not in EXERCISE_CALORIES_PER_MIN:
            print("Exercise not recognized. Please choose from the list.")
            return

        try:
            duration = int(input("Enter duration in minutes: "))
        except ValueError:
            print("Invalid input for duration.")
            return

        calories_per_min = EXERCISE_CALORIES_PER_MIN[exercise_name]
        calories_burned = round(duration * calories_per_min)

        self.cursor.execute('''INSERT INTO exercise_log (date, exercise_name, duration_minutes, calories_burned)
                               VALUES (?, ?, ?, ?)''',
                            (today, exercise_name, duration, calories_burned))
        self.conn.commit()
        print(f"Logged {exercise_name} for {duration} minutes, {calories_burned} calories burned.")

        # Update daily_log with calories burned
        self.cursor.execute("SELECT calories_burned FROM daily_log WHERE date = ?", (today,))
        existing = self.cursor.fetchone()
        if existing:
            total_burned = existing[0] + calories_burned
            self.cursor.execute("UPDATE daily_log SET calories_burned = ? WHERE date = ?", (total_burned, today))
        else:
            self.cursor.execute('''INSERT INTO daily_log (date, calories_consumed, weight, calories_burned)
                                 VALUES (?, ?, ?, ?)''',
                                (today, self.get_calories_today(), self.get_user_profile()[6], calories_burned))
        self.conn.commit()

    # --- Visualization Functions ---

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
        colors = ['#f94144', '#90be6d', '#577590']
        explode = (0.05, 0.05, 0.05)

        # Plot
        plt.figure(figsize=(6,6))
        plt.pie(
            sizes, labels=labels, autopct='%1.1f%%', startangle=140, 
            colors=colors, explode=explode,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2},
            textprops={'fontsize': 12, 'weight': 'bold'}
        )
        plt.axis('equal')  # Equal aspect ratio ensures a circular pie chart
        plt.suptitle("Macronutrient Breakdown", fontsize=16, fontweight="bold")
        plt.text(-1.3, -1.3, f"Date: {today}", fontsize=10, ha='left')

        # Save the chart
        filename = f"nutrition_breakdown_{today}.png"
        plt.savefig(filename, dpi=300)
        print(f"Nutrition breakdown saved as {filename}")

    def show_calorie_intake_pie_chart(self):
        """Saves a pie chart comparing consumed calories to daily recommended intake."""
        today = datetime.date.today().isoformat()
        calories_consumed = self.get_calories_today()
        recommended_calories = self.calculate_daily_calories() or 2000

        budget_calories = max(recommended_calories - calories_consumed, 0)
        budget_calories = round(budget_calories, 1)

        labels = ['Calories Consumed', 'Calories Remaining']
        sizes = [calories_consumed, budget_calories]
        colors = ['#ff6b6b', '#4dabf7']
        explode = (0.05, 0.05)

        def format_calories(pct, all_vals):
            absolute = int(round(pct / 100 * sum(all_vals)))
            return f'{absolute} cal'

        plt.figure(figsize=(8, 8))
        wedges, texts, autotexts = plt.pie(
            sizes,
            labels=labels,
            autopct=lambda pct: format_calories(pct, sizes),
            startangle=90,
            colors=colors,
            explode=explode,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2},
            textprops={'fontsize': 10, 'weight': 'bold'}  # smaller label font
        )

        plt.axis('equal')
        plt.suptitle("Calorie Intake vs. Budget", fontsize=16, fontweight="bold")
        plt.text(-1.3, -1.3, f"Date: {today}", fontsize=10, ha='left')

        plt.tight_layout()
        filename = f"calorie_intake_{today}.png"
        plt.savefig(filename, dpi=300)
        print(f"Calorie intake chart saved as {filename}")
    
    def show_progress_graph(self):
        """Display a line chart of weight over time."""
        self.cursor.execute("SELECT date, weight FROM daily_log ORDER BY date")
        logs = self.cursor.fetchall()

        if not logs:
            print("No data available to display progress.")
            return

        dates = [datetime.datetime.strptime(row[0], "%Y-%m-%d") for row in logs]
        weights = [row[1] for row in logs]

        plt.figure(figsize=(12, 6))

        # Weight trend – bold line
        plt.plot(dates, weights, label="Weight (lbs)", linewidth=1.3, color="#1f77b4", marker=".", markersize=2, zorder=3)

        # Goal Weight line
        profile = self.get_user_profile()
        if profile:
            goal_weight = profile[1]
            plt.axhline(goal_weight, color='gray', linestyle=':', linewidth=1.5,
                        label=f"Goal Weight ({goal_weight} lbs)", zorder=0)

        # Labels and formatting
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Weight (lbs)", fontsize=12)
        plt.title("Weight Progress Over Time", fontsize=14, weight='bold')
        plt.legend(fontsize=10)
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.4)

        # Date formatting
        ax = plt.gca()
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

        plt.tight_layout()
        filename = "progress_graph.png"
        plt.savefig(filename, dpi=300)
        print(f"Progress graph saved as {filename}")

    # --- Profile Interaction Functions ---

    def prompt_profile_creation(self):
        goal_type = get_valid_input("Enter your goal (lose/maintain/gain): ", lambda x: x in ["lose", "maintain", "gain"], "Please enter 'lose', 'maintain', or 'gain'.")

        valid_levels = ["not active", "somewhat active", "highly active", "extremely active"]
        activity_level = get_valid_input("Enter activity level (Not Active, Somewhat Active, Highly Active, Extremely Active): ",
                                        lambda x: x.lower() in valid_levels,
                                        f"Invalid activity level. Choose from: {', '.join(valid_levels)}.").lower()

        gender = get_valid_input("Enter gender (male/female): ", lambda x: x.lower() in ["male", "female"], "Please enter 'male' or 'female'.")
        birthday = get_valid_input("Enter birthday (MM-DD-YYYY): ", lambda x: len(x.split("-")) == 3, "Please use format MM-DD-YYYY.")
        weight = get_valid_float("Enter current weight (lbs): ")
        height_ft = get_valid_int("Enter height (feet): ")
        height_in = get_valid_int("Enter additional inches: ")
        height = (height_ft * 12 + height_in) * 2.54

        if goal_type == "lose":
            goal_weight = get_valid_float("Enter goal weight (lbs): ")
            weekly_weight_loss = get_valid_float("How many pounds would you like to lose per week (0.5 to 2)? ")
            while not (0.5 <= weekly_weight_loss <= 2):
                print("Enter a value between 0.5 and 2.")
                weekly_weight_loss = get_valid_float("Try again: ")
        elif goal_type == "gain":
            goal_weight = get_valid_float("Enter goal weight (lbs): ")
            gain_per_week = get_valid_float("How many pounds would you like to gain per week (0.5 to 2)? ")
            while not (0.5 <= gain_per_week <= 2):
                print("Enter a value between 0.5 and 2.")
                gain_per_week = get_valid_float("Try again: ")
            weekly_weight_loss = -gain_per_week
        else:
            goal_weight = weight
            weekly_weight_loss = 0

        self.set_user_profile(goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
        print("User profile created successfully!")
    
    def view_user_profile(self):
        profile = self.get_user_profile()
        if profile:
            print("\nCurrent User Profile:")
            print(f"Goal Weight: {profile[1]} lbs")
            print(f"Weekly Weight Change: {profile[2]} lbs/week")
            print(f"Activity Level: {profile[3]}")
            print(f"Gender: {profile[4]}")
            print(f"Birthday: {profile[5]}")
            print(f"Current Weight: {profile[6]} lbs")
            height_inches = round(profile[7] / 2.54)
            print(f"Height: {height_inches // 12} ft {height_inches % 12} in ({round(profile[7])} cm)")
        else:
            print("No user profile found.")

    def edit_user_profile(self):
        profile = self.get_user_profile()
        if not profile:
            print("No user profile found. Please set one first.")
            return

        print("\nEdit your profile (press Enter to keep current value):")

        def get_optional(prompt, default, cast_fn):
            val = input(f"{prompt} [{default}]: ").strip()
            if not val:
                return default
            try:
                return cast_fn(val)
            except:
                print("Invalid input. Keeping current.")
                return default

        goal_weight = get_optional("Goal Weight (lbs)", profile[1], float)
        weekly_weight_loss = get_optional("Weekly Weight Change (lbs/week)", profile[2], float)
        activity_level = input(f"Activity Level [{profile[3]}]: ").strip() or profile[3]
        gender = input(f"Gender [{profile[4]}]: ").strip() or profile[4]
        birthday = input(f"Birthday (MM-DD-YYYY) [{profile[5]}]: ").strip() or profile[5]
        weight = get_optional("Current Weight (lbs)", profile[6], float)
        total_inches = round(profile[7] / 2.54)
        current_ft = total_inches // 12
        current_in = total_inches % 12

        height_ft = get_optional("Enter height (feet)", current_ft, int)
        height_in = get_optional("Enter additional inches", current_in, int)
        height = (height_ft * 12 + height_in) * 2.54

        self.set_user_profile(goal_weight, weekly_weight_loss, activity_level, gender, birthday, weight, height)
        print("Profile updated successfully.")

    def view_personalized_plan(self):
        profile = self.get_user_profile()
        if not profile:
            print("No user profile found. Please set one first.")
            return

        _, goal_weight, weekly_weight_change, activity_level, gender, birthday, weight, height = profile
        age = self._calculate_age(birthday)
        calorie_target = self.calculate_daily_calories()

        # Timeline estimate
        if weekly_weight_change != 0:
            weeks = abs((weight - goal_weight) / weekly_weight_change)
            eta = f"{round(weeks, 1)} weeks"
        else:
            eta = "No change planned"

        # Macro recommendations (standard: 30/40/30 split)
        protein_cal = 0.3 * calorie_target
        carbs_cal = 0.4 * calorie_target
        fat_cal = 0.3 * calorie_target

        protein_g = round(protein_cal / 4)
        carbs_g = round(carbs_cal / 4)
        fat_g = round(fat_cal / 9)

        print(f"\nPersonalized Health Plan")
        print("------------------------")
        print(f"• Current Weight: {weight} lbs")
        print(f"• Goal Weight: {goal_weight} lbs")
        total_inches = round(height / 2.54)
        feet = total_inches // 12
        inches = total_inches % 12
        print(f"• Height: {feet} ft {inches} in")
        print(f"• Age: {age}")
        print(f"• Activity Level: {activity_level}")
        print(f"• Weekly Goal: {weekly_weight_change:+.1f} lbs/week")
        print(f"\nDaily Calorie Budget: {round(calorie_target)} cal")
        print(f"Estimated Time to Reach Goal: {eta}")
        print(f"\nSuggested Macronutrient Ranges:")
        print(f"• Protein: {protein_g}g")
        print(f"• Carbohydrates: {carbs_g}g")
        print(f"• Fat: {fat_g}g")

    def view_daily_log(self):
        today = datetime.date.today().isoformat()
        view_all = input("Would you like to see all past days? (yes/no): ").strip().lower()

        if view_all == "yes":
            self.cursor.execute("SELECT date, calories_consumed, weight, calories_burned FROM daily_log ORDER BY date")
        else:
            self.cursor.execute("SELECT date, calories_consumed, weight, calories_burned FROM daily_log WHERE date = ?", (today,))

        logs = self.cursor.fetchall()

        if logs:
            print("\nDate         | Calories Consumed | Weight | Calories Burned (lbs)")
            print("---------------------------------------------------------------")
            for log in logs:
                print(f"{log[0]}   | {log[1]}              | {log[2]}              | {log[3]}")

            if view_all == "yes":
                selected_date = input("\nEnter a date (YYYY-MM-DD) to view meals, or press Enter to return to menu: ").strip()
                if selected_date:
                    self.cursor.execute("SELECT id, meal_name, calories FROM meal_log WHERE date = ?", (selected_date,))
                    meals = self.cursor.fetchall()
                    print(f"\nMeals for {selected_date}:")
                    for meal in meals:
                        print(f"[ID: {meal[0]}] {meal[1]} - {meal[2]} cal")

                    action = input("Would you like to edit or delete a meal? (edit/delete/none): ").strip().lower()
                    if action == "delete":
                        meal_id = input("Enter Meal ID to delete: ").strip()
                        self.cursor.execute("DELETE FROM meal_log WHERE id = ?", (meal_id,))
                        self.conn.commit()
                        print("Meal deleted successfully.")
                    elif action == "edit":
                        meal_id = input("Enter Meal ID to edit: ").strip()
                        new_name = input("New meal name: ").strip()

                        new_calories = get_optional_float("New calories (leave blank to keep current): ", None)
                        new_fat = get_optional_float("New fat (g) (leave blank to keep current): ", None)
                        new_carbs = get_optional_float("New carbohydrates (g) (leave blank to keep current): ", None)
                        new_protein = get_optional_float("New protein (g) (leave blank to keep current): ", None)

                        self.cursor.execute("SELECT calories, fat, carbohydrates, protein FROM meal_log WHERE id = ?", (meal_id,))
                        existing = self.cursor.fetchone()
                        if not existing:
                            print("Meal ID not found.")
                            return
                        calories, fat, carbs, protein = existing

                        new_calories = new_calories if new_calories is not None else calories
                        new_fat = new_fat if new_fat is not None else fat
                        new_carbs = new_carbs if new_carbs is not None else carbs
                        new_protein = new_protein if new_protein is not None else protein

                        self.cursor.execute(
                            "UPDATE meal_log SET meal_name = ?, calories = ?, fat = ?, carbohydrates = ?, protein = ? WHERE id = ?",
                            (new_name, new_calories, new_fat, new_carbs, new_protein, meal_id))
                        self.conn.commit()
                        print("Meal updated successfully.")
            else:
                print("\nMeals logged today:")
                self.cursor.execute("SELECT id, meal_name, calories FROM meal_log WHERE date = ?", (today,))
                meals = self.cursor.fetchall()
                for meal in meals:
                    print(f"[ID: {meal[0]}] {meal[1]} - {meal[2]} cal")

                action = input("Would you like to edit or delete a meal? (edit/delete/none): ").strip().lower()
                if action == "delete":
                    meal_id = input("Enter Meal ID to delete: ").strip()
                    self.cursor.execute("DELETE FROM meal_log WHERE id = ?", (meal_id,))
                    self.conn.commit()
                    print("Meal deleted successfully.")
                elif action == "edit":
                    meal_id = input("Enter Meal ID to edit: ").strip()
                    new_name = input("New meal name: ").strip()

                    new_calories = get_optional_float("New calories (leave blank to keep current): ", None)
                    new_fat = get_optional_float("New fat (g) (leave blank to keep current): ", None)
                    new_carbs = get_optional_float("New carbohydrates (g) (leave blank to keep current): ", None)
                    new_protein = get_optional_float("New protein (g) (leave blank to keep current): ", None)

                    self.cursor.execute("SELECT calories, fat, carbohydrates, protein FROM meal_log WHERE id = ?", (meal_id,))
                    existing = self.cursor.fetchone()
                    if not existing:
                        print("Meal ID not found.")
                        return
                    calories, fat, carbs, protein = existing

                    new_calories = new_calories if new_calories is not None else calories
                    new_fat = new_fat if new_fat is not None else fat
                    new_carbs = new_carbs if new_carbs is not None else carbs
                    new_protein = new_protein if new_protein is not None else protein

                    self.cursor.execute(
                        "UPDATE meal_log SET meal_name = ?, calories = ?, fat = ?, carbohydrates = ?, protein = ? WHERE id = ?",
                        (new_name, new_calories, new_fat, new_carbs, new_protein, meal_id))
                    self.conn.commit()
                    print("Meal updated successfully.")
        else:
            print("No daily logs found.")

    def run_cli(self):
        self.log_daily_summary()
        while True:
            print("\nCalorie Counter Menu")
            print("1. Set New Profile")
            print("2. View Personalized Health Plan")
            print("3. View Current Profile")
            print("4. Edit Profile")
            print("5. Log a Meal")
            print("6. View Today's Calorie Intake")
            print("7. View Recommended Daily Calories")
            print("8. Update Weight")
            print("9. View Daily Log")
            print("10. Export Daily Log to CSV")
            print("11. View Nutrition Breakdown (Pie Chart)")
            print("12. View Calorie Intake vs. Goal (Pie Chart)")
            print("13. View Progress Graph")
            print("14. Log an Exercise")
            print("15. Exit")

            choice = get_valid_input("Enter choice: ", lambda x: x.isdigit() and 1 <= int(x) <= 15, "Please enter a number between 1 and 15.")

            if choice == "1":
                print("WARNING: If you already have a profile doing this will overwrite your existing profile.")
                confirm = input("Are you sure? (yes/no): ").strip().lower()
                if confirm != "yes":
                    print("Operation cancelled.")
                    continue
                self.prompt_profile_creation()

            elif choice == "2":
                self.view_personalized_plan()
            
            elif choice == "3":
                self.view_user_profile()

            elif choice == "4":
                self.edit_user_profile()

            elif choice == "5":
                self.log_meal()

            elif choice == "6":
                print(f"Total Calories consumed today: {self.get_calories_today()} Calories")

            elif choice == "7":
                print(f"Recommended daily Calorie intake: {self.calculate_daily_calories()} Calories")

            elif choice == "8":
                new_weight = get_valid_float("Enter new weight (lbs): ")
                self.update_weight(new_weight)

            elif choice == "9":
                self.view_daily_log()

            elif choice == "10":
                self.export_log_to_csv()

            elif choice == "11":
                self.show_nutrition_pie_chart()

            elif choice == "12":
                self.show_calorie_intake_pie_chart()

            elif choice == "13":
                self.show_progress_graph()
            
            elif choice == "14":
                self.log_exercise()

            elif choice == "15":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    calorie_tracker = CalorieCounter()
    calorie_tracker.run_cli()
