CREATE TABLE IF NOT EXISTS user_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_weight REAL NOT NULL,
    weekly_weight_loss REAL NOT NULL,
    activity_level TEXT NOT NULL,
    gender TEXT NOT NULL,
    birthday TEXT NOT NULL,
    weight REAL NOT NULL,
    height REAL NOT NULL,
    created_at TEXT NOT NULL
);