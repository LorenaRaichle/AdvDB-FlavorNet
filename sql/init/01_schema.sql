-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- USER PREFERENCES
CREATE TABLE IF NOT EXISTS user_prefs (
    pref_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    diet_type VARCHAR(50),         -- e.g., 'vegan', 'halal', 'keto'
    allergies TEXT[],              -- e.g., ['milk', 'nuts']
    dislikes TEXT[],               -- e.g., ['onion']
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RECIPE METADATA (links to MongoDB)
CREATE TABLE IF NOT EXISTS recipe_metadata (
    recipe_id SERIAL PRIMARY KEY,
    mongo_id VARCHAR(50),           -- links to MongoDB _id
    title VARCHAR(255),
    cuisine VARCHAR(100),
    rating_avg DECIMAL(3,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ANALYTICS (user activity)
CREATE TABLE IF NOT EXISTS analytics (
    event_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(50),
    event_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);