import sqlite3

def initialize_database(db_name="counter.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY,
        goal_weight REAL,
        weekly_weight_loss REAL,
        activity_level TEXT,
        gender TEXT,
        birthday TEXT,
        weight REAL,
        height REAL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS meal_log (
        id INTEGER PRIMARY KEY,
        date TEXT,
        meal_name TEXT,
        calories INTEGER,
        fat REAL,
        carbohydrates REAL,
        protein REAL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS daily_log (
        date TEXT PRIMARY KEY,
        calories_consumed INTEGER,
        weight REAL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS exercise_log (
        id INTEGER PRIMARY KEY,
        date TEXT,
        exercise_name TEXT,
        duration_minutes INTEGER,
        calories_burned INTEGER
    )""")

    try:
        cursor.execute("ALTER TABLE daily_log ADD COLUMN calories_burned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    return conn, cursor
