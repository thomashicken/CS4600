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

-- Table for storing food items
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fdc_id INTEGER UNIQUE,
    description TEXT NOT NULL
);

-- Table for storing ingredients of a food item
CREATE TABLE IF NOT EXISTS food_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER,
    ingredient_name TEXT NOT NULL,
    ingredient_weight REAL NOT NULL,
    unit TEXT NOT NULL,
    FOREIGN KEY (food_id) REFERENCES foods (id)
);

-- Table for storing nutrient information for a food item
CREATE TABLE IF NOT EXISTS food_nutrients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER,
    nutrient_name TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    FOREIGN KEY (food_id) REFERENCES foods (id)
);

-- Table for storing logged food intake
CREATE TABLE IF NOT EXISTS logged_foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    food_id INTEGER,  -- Links to preset food
    custom_food TEXT, -- If the user manually enters food
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    date_logged TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user_data(id),
    FOREIGN KEY (food_id) REFERENCES foods(id)
);